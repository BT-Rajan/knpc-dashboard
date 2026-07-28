import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function LogsViewer() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api
      .get<string>('/api/admin/logs/plain')
      .then(setText)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div className="eyebrow">Scrape log (plain text)</div>
        <button className="btn" onClick={load}>{loading ? 'Refreshing…' : 'Refresh'}</button>
      </div>
      <pre
        className="mono scrollbar-thin"
        style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 3,
          padding: 16,
          fontSize: 12.5,
          lineHeight: 1.7,
          maxHeight: 520,
          overflowY: 'auto',
          whiteSpace: 'pre-wrap',
          color: 'var(--text-muted)',
        }}
      >
        {text}
      </pre>
    </div>
  )
}
