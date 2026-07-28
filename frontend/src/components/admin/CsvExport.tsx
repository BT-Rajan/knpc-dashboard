import { useEffect, useState } from 'react'
import { getToken } from '../../api/client'

export default function CsvExport() {
  const [tables, setTables] = useState<string[]>([])
  const [downloading, setDownloading] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/admin/export/tables', { headers: { Authorization: `Bearer ${getToken()}` } })
      .then((r) => r.json())
      .then((d) => setTables(d.tables))
  }, [])

  async function download(table: string) {
    setDownloading(table)
    try {
      const resp = await fetch(`/api/admin/export/tables/${table}.csv`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${table}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="panel" style={{ padding: 20, maxWidth: 480 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>Raw table export</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {tables.map((t) => (
          <div key={t} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="mono" style={{ fontSize: 13 }}>{t}</span>
            <button className="btn" onClick={() => download(t)} disabled={downloading === t}>
              {downloading === t ? 'Downloading…' : 'Download CSV'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
