import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { ScrapeSettingOut } from '../../types'

export default function ScrapeSettings() {
  const [frequency, setFrequency] = useState(30)
  const [saved, setSaved] = useState(true)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  useEffect(() => {
    api.get<ScrapeSettingOut>('/api/admin/scrape/settings').then((s) => setFrequency(s.frequency_minutes))
  }, [])

  async function save() {
    await api.put('/api/admin/scrape/settings', { frequency_minutes: frequency })
    setSaved(true)
  }

  async function runAll() {
    setRunning(true)
    setResult(null)
    try {
      const res = await api.post<{ results: Record<string, boolean> }>('/api/admin/scrape/run')
      const ok = Object.values(res.results).filter(Boolean).length
      const total = Object.values(res.results).length
      setResult(`${ok}/${total} items scraped successfully. See Logs for details.`)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 480 }}>
      <div className="panel" style={{ padding: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Scrape frequency</div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Minutes between runs</label>
            <input
              type="number"
              min={1}
              value={frequency}
              onChange={(e) => {
                setFrequency(Number(e.target.value))
                setSaved(false)
              }}
            />
          </div>
          <button className="btn btn-brass" onClick={save} disabled={saved}>
            {saved ? 'Saved' : 'Save'}
          </button>
        </div>
      </div>

      <div className="panel" style={{ padding: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Manual run</div>
        <button className="btn btn-brass" onClick={runAll} disabled={running}>
          {running ? 'Running…' : 'Scrape all items now'}
        </button>
        {result && <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-muted)' }}>{result}</div>}
      </div>
    </div>
  )
}
