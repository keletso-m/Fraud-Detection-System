import React from 'react';

const LEVEL_COLORS = {
  LOW:      { color: '#22c55e', bg: 'rgba(34,197,94,0.1)'  },
  MEDIUM:   { color: '#eab308', bg: 'rgba(234,179,8,0.1)'  },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)'  },
};

export function AlertBadge({ level }) {
  const c = LEVEL_COLORS[level] || LEVEL_COLORS.LOW;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: c.bg, color: c.color,
      padding: '2px 8px', borderRadius: 4,
      fontSize: 11, fontWeight: 500, fontFamily: 'var(--font-mono)',
      letterSpacing: '0.05em', textTransform: 'uppercase',
      border: `1px solid ${c.color}33`,
    }}>
      <span style={{ fontSize: 7 }}>●</span>
      {level}
    </span>
  );
}

export function ScoreBar({ score }) {
  const color = score >= 75 ? '#ef4444' : score >= 50 ? '#f97316' : score >= 25 ? '#eab308' : '#22c55e';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color, minWidth: 24, textAlign: 'right' }}>{score}</span>
    </div>
  );
}

export function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)',
      padding: '1.25rem',
      ...style,
    }}>
      {children}
    </div>
  );
}

export function StatCard({ label, value, sub, accent }) {
  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <span style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
      <span style={{ fontSize: 28, fontWeight: 700, color: accent || 'var(--text)', lineHeight: 1.2 }}>{value}</span>
      {sub && <span style={{ fontSize: 12, color: 'var(--muted)' }}>{sub}</span>}
    </Card>
  );
}

export function Spinner() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{
        width: 20, height: 20,
        border: '2px solid var(--border-em)',
        borderTop: '2px solid var(--accent)',
        borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export function SectionHeader({ title, action }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
      <h2 style={{ fontSize: 13, fontWeight: 500, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{title}</h2>
      {action}
    </div>
  );
}

export function Btn({ children, onClick, variant = 'default', disabled, style }) {
  const styles = {
    default: { background: 'var(--bg-hover)', border: '1px solid var(--border-em)', color: 'var(--text)' },
    primary: { background: 'var(--accent)',    border: '1px solid var(--accent)',    color: '#fff'         },
    danger:  { background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '7px 14px', borderRadius: 'var(--r-sm)', fontSize: 13,
        fontFamily: 'var(--font-ui)', fontWeight: 500,
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'opacity 0.15s',
        ...styles[variant],
        ...style,
      }}
    >
      {children}
    </button>
  );
}