import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { TickerEntry } from '../types'

const POLL_MS = 60_000

function TickerCell({ entry }: { entry: TickerEntry }) {
  const pct = entry.daily_change_pct
  const dir = pct == null ? null : pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  return (
    <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 8, marginRight: 40 }}>
      <span style={{ fontSize: 12, letterSpacing: '0.04em', color: 'var(--text-muted)' }}>{entry.code}</span>
      <span className="mono" style={{ fontSize: 13, color: 'var(--text)' }}>
        {entry.current_price != null ? entry.current_price.toFixed(2) : '—'}
      </span>
      {dir && (
        <span
          className="mono"
          style={{ fontSize: 12, color: dir === 'up' ? 'var(--positive)' : dir === 'down' ? 'var(--negative)' : 'var(--text-dim)' }}
        >
          {dir === 'up' ? '▲' : dir === 'down' ? '▼' : '·'} {Math.abs(pct!).toFixed(2)}%
        </span>
      )}
    </span>
  )
}

export default function Ticker() {
  const [entries, setEntries] = useState<TickerEntry[]>([])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await api.get<TickerEntry[]>('/api/ticker')
        if (!cancelled) setEntries(data)
      } catch {
        /* ticker is non-critical; silently retry on next poll */
      }
    }
    load()
    const id = setInterval(load, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  if (entries.length === 0) return <div style={{ height: 38, borderBottom: '1px solid var(--border)' }} />

  return (
    <div
      className="scrollbar-thin"
      style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--panel)',
        padding: '10px 24px',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
      }}
    >
      {entries.map((e) => (
        <TickerCell key={e.code} entry={e} />
      ))}
    </div>
  )
}
