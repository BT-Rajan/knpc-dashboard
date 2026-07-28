import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { ItemDetail } from '../types'
import PriceChart from './PriceChart'
import NewsList from './NewsList'

export default function ItemView({ code }: { code: string }) {
  const [item, setItem] = useState<ItemDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .get<ItemDetail>(`/api/items/${code}`)
      .then((d) => !cancelled && setItem(d))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [code])

  if (loading || !item) {
    return <div style={{ padding: 40, color: 'var(--text-dim)' }}>Loading…</div>
  }

  const pct = item.daily_change_pct
  const dir = pct == null ? null : pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const dirColor = dir === 'up' ? 'var(--positive)' : dir === 'down' ? 'var(--negative)' : 'var(--text-dim)'

  return (
    <div style={{ padding: '32px 32px 48px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <div className="eyebrow" style={{ marginBottom: 6 }}>{item.category}</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 20, flexWrap: 'wrap' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 34, margin: 0 }}>
            {item.name}
          </h1>
          <span className="eyebrow">{item.unit}</span>
        </div>

        <div
          style={{
            marginTop: 18,
            paddingTop: 18,
            borderTop: '1px solid var(--brass)',
            display: 'flex',
            alignItems: 'baseline',
            gap: 18,
            flexWrap: 'wrap',
          }}
        >
          <span className="mono" style={{ fontSize: 42, fontWeight: 500, letterSpacing: '-0.01em' }}>
            {item.current_price != null ? item.current_price.toFixed(2) : '—'}
          </span>
          {dir && (
            <span className="mono" style={{ fontSize: 16, color: dirColor }}>
              {dir === 'up' ? '▲' : dir === 'down' ? '▼' : '·'} {item.daily_change?.toFixed(2)} ({Math.abs(pct!).toFixed(2)}%)
            </span>
          )}
          <span className="eyebrow">
            {item.as_of ? `as of ${item.as_of}` : 'no data collected yet'}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <PriceChart title="Weekly movement" series={item.weekly_series} unit={item.unit} />
        <PriceChart title="Monthly movement" series={item.monthly_series} unit={item.unit} />
      </div>

      <NewsList news={item.news} />
    </div>
  )
}
