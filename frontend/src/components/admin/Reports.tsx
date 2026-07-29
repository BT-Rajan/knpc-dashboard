import { useEffect, useState } from 'react'
import { api } from '../../api/client'

interface BenchmarkStat {
  name: string
  open: number
  close: number
  high: number
  low: number
  avg: number
  change: number
  change_pct: number
  readings: number
}

interface ProductStat {
  name: string
  open: number
  close: number
  high: number
  low: number
  avg: number
  change: number
  change_pct: number
  readings: number
}

interface ReportFile {
  filename: string
  size: number
  created: string
}

const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4'] as const

export default function Reports() {
  const [year, setYear] = useState(new Date().getFullYear())
  const [quarter, setQuarter] = useState<typeof QUARTERS[number]>('Q1')
  const [benchmarks, setBenchmarks] = useState<BenchmarkStat[]>([])
  const [products, setProducts] = useState<ProductStat[]>([])
  const [outlineNotes, setOutlineNotes] = useState('')
  const [generatedBy, setGeneratedBy] = useState('MOG Analyst')
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [reports, setReports] = useState<ReportFile[]>([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadPreview()
    loadReports()
  }, [year, quarter])

  const loadPreview = async () => {
    try {
      setLoading(true)
      const data = await api.post<{
        benchmarks: BenchmarkStat[]
        products: ProductStat[]
      }>('/api/reports/preview', {
        year,
        quarter,
      })
      setBenchmarks(data.benchmarks)
      setProducts(data.products)
    } catch (err) {
      setMessage(`Error loading preview: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  const loadReports = async () => {
    try {
      const data = await api.get<{ reports: ReportFile[] }>('/api/reports/list')
      setReports(data.reports)
    } catch (err) {
      console.error('Error loading reports:', err)
    }
  }

  const generateReport = async () => {
    if (!quarter) {
      setMessage('Please select a quarter')
      return
    }
    try {
      setGenerating(true)
      setMessage('')
      const result = await api.post<{ status: string; filename: string }>(
        '/api/reports/generate',
        {
          year,
          quarter,
          outlook_notes: outlineNotes,
          generated_by: generatedBy,
        }
      )
      if (result.status === 'success') {
        setMessage(`✓ Report generated: ${result.filename}`)
        setOutlineNotes('')
        await loadReports()
      }
    } catch (err) {
      setMessage(`Error generating report: ${err}`)
    } finally {
      setGenerating(false)
    }
  }

  const downloadReport = async (filename: string) => {
    try {
      window.location.href = `/api/reports/download/${encodeURIComponent(filename)}`
    } catch (err) {
      setMessage(`Error downloading report: ${err}`)
    }
  }

  return (
    <div>
      <h2 style={{ fontSize: 18, marginBottom: 20 }}>Quarterly Market Reports</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <div>
          <label className="form-label">Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 4 }}
          />
        </div>
        <div>
          <label className="form-label">Quarter</label>
          <select
            value={quarter}
            onChange={(e) => setQuarter(e.target.value as typeof QUARTERS[number])}
            style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 4 }}
          >
            {QUARTERS.map((q) => (
              <option key={q} value={q}>
                {q}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="panel" style={{ padding: 16, marginBottom: 24 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>
          Preview — Benchmark Movement {loading && '(loading...)'}
        </div>
        {benchmarks.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: 8, textAlign: 'left' }}>Benchmark</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Open</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Close</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Change %</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Readings</th>
                </tr>
              </thead>
              <tbody>
                {benchmarks.map((b, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-dim)' }}>
                    <td style={{ padding: 8 }}>{b.name}</td>
                    <td style={{ padding: 8, textAlign: 'right' }}>${b.open.toFixed(2)}</td>
                    <td style={{ padding: 8, textAlign: 'right' }}>${b.close.toFixed(2)}</td>
                    <td style={{ padding: 8, textAlign: 'right', color: b.change_pct >= 0 ? '#22c55e' : '#ef4444' }}>
                      {b.change_pct >= 0 ? '+' : ''}{b.change_pct.toFixed(2)}%
                    </td>
                    <td style={{ padding: 8, textAlign: 'right' }}>{b.readings}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>No data available for this period.</div>
        )}
      </div>

      <div className="panel" style={{ padding: 16, marginBottom: 24 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Preview — Product Movement</div>
        {products.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: 8, textAlign: 'left' }}>Product</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Open</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Close</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Change %</th>
                  <th style={{ padding: 8, textAlign: 'right' }}>Readings</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-dim)' }}>
                    <td style={{ padding: 8 }}>{p.name}</td>
                    <td style={{ padding: 8, textAlign: 'right' }}>${p.open.toFixed(2)}</td>
                    <td style={{ padding: 8, textAlign: 'right' }}>${p.close.toFixed(2)}</td>
                    <td style={{ padding: 8, textAlign: 'right', color: p.change_pct >= 0 ? '#22c55e' : '#ef4444' }}>
                      {p.change_pct >= 0 ? '+' : ''}{p.change_pct.toFixed(2)}%
                    </td>
                    <td style={{ padding: 8, textAlign: 'right' }}>{p.readings}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>No data available for this period.</div>
        )}
      </div>

      <div className="panel" style={{ padding: 16, marginBottom: 24 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Generate Report</div>

        <div style={{ marginBottom: 16 }}>
          <label className="form-label">Analyst Outlook & Commentary (optional)</label>
          <textarea
            value={outlineNotes}
            onChange={(e) => setOutlineNotes(e.target.value)}
            placeholder="e.g., Demand outlook for next quarter, refinery maintenance schedule impacts, key risks to monitor..."
            style={{
              width: '100%',
              minHeight: 100,
              padding: '8px',
              border: '1px solid var(--border)',
              borderRadius: 4,
              fontFamily: 'monospace',
              fontSize: 13,
            }}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label className="form-label">Prepared By</label>
          <input
            type="text"
            value={generatedBy}
            onChange={(e) => setGeneratedBy(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid var(--border)', borderRadius: 4 }}
          />
        </div>

        <button
          onClick={generateReport}
          disabled={generating}
          className="btn btn-brass"
          style={{ width: '100%', padding: '10px', fontWeight: 500 }}
        >
          {generating ? '⏳ Generating...' : '📄 Generate & Save Report'}
        </button>

        {message && (
          <div
            style={{
              marginTop: 12,
              padding: '8px',
              borderRadius: 4,
              backgroundColor: message.startsWith('✓') ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
              color: message.startsWith('✓') ? '#22c55e' : '#ef4444',
              fontSize: 13,
            }}
          >
            {message}
          </div>
        )}
      </div>

      <div className="panel" style={{ padding: 16 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Published Reports ({reports.length})</div>
        {reports.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {reports.map((report, i) => (
              <div
                key={i}
                style={{
                  padding: '12px',
                  border: '1px solid var(--border-dim)',
                  borderRadius: 4,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>📄 {report.filename}</div>
                  <div style={{ color: 'var(--text-dim)', fontSize: 12, marginTop: 4 }}>
                    {new Date(report.created).toLocaleString()} • {(report.size / 1024).toFixed(0)} KB
                  </div>
                </div>
                <button
                  onClick={() => downloadReport(report.filename)}
                  className="btn"
                  style={{ padding: '6px 12px', fontSize: 12 }}
                >
                  ⬇ Download
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>No reports generated yet.</div>
        )}
      </div>
    </div>
  )
}
