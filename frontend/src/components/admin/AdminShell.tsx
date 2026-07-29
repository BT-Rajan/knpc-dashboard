import { useState } from 'react'
import SourcesManager from './SourcesManager'
import ScrapeSettings from './ScrapeSettings'
import LogsViewer from './LogsViewer'
import CsvExport from './CsvExport'
import AISettings from './AISettings'
import Reports from './Reports'

const TABS = ['Sources', 'Scrape Control', 'AI Settings', 'Reports', 'Logs', 'Export'] as const
type Tab = (typeof TABS)[number]

export default function AdminShell() {
  const [tab, setTab] = useState<Tab>('Sources')

  return (
    <div style={{ padding: '24px 32px 48px' }}>
      <div className="eyebrow" style={{ marginBottom: 4 }}>Admin</div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 26, margin: '0 0 20px' }}>
        Control panel
      </h1>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border)' }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={tab === t ? 'btn btn-brass' : 'btn'}
            style={{ borderRadius: '3px 3px 0 0', borderBottom: 'none' }}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Sources' && <SourcesManager />}
      {tab === 'Scrape Control' && <ScrapeSettings />}
      {tab === 'AI Settings' && <AISettings />}
      {tab === 'Reports' && <Reports />}
      {tab === 'Logs' && <LogsViewer />}
      {tab === 'Export' && <CsvExport />}
    </div>
  )
}
