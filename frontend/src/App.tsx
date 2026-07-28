import { useEffect, useState } from 'react'
import { api, clearSession, getRole, getToken, getUsername } from './api/client'
import { NavCategory } from './types'
import Login from './components/Login'
import Ticker from './components/Ticker'
import NavBar from './components/NavBar'
import ItemView from './components/ItemView'
import AIPanel from './components/AIPanel'
import AdminShell from './components/admin/AdminShell'

export default function App() {
  const [authed, setAuthed] = useState(!!getToken())
  const [categories, setCategories] = useState<NavCategory[]>([])
  const [selectedCode, setSelectedCode] = useState<string | null>(null)
  const [view, setView] = useState<'dashboard' | 'admin'>('dashboard')
  const [aiOpen, setAiOpen] = useState(false)

  useEffect(() => {
    if (!authed) return
    api.get<NavCategory[]>('/api/nav').then((cats) => {
      setCategories(cats)
      if (!selectedCode && cats.length > 0 && cats[0].items.length > 0) {
        setSelectedCode(cats[0].items[0].code)
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authed])

  if (!authed) {
    return <Login onLoggedIn={() => setAuthed(true)} />
  }

  return (
    <div style={{ minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
      <Ticker />
      <NavBar
        categories={categories}
        selectedCode={selectedCode}
        onSelect={(code) => {
          setSelectedCode(code)
          setView('dashboard')
        }}
        role={getRole()}
        view={view}
        onChangeView={setView}
        onAskAI={() => setAiOpen(true)}
        onLogout={() => {
          clearSession()
          setAuthed(false)
        }}
        username={getUsername()}
      />

      <div style={{ flex: 1 }}>
        {view === 'admin' ? (
          <AdminShell />
        ) : selectedCode ? (
          <ItemView code={selectedCode} />
        ) : (
          <div style={{ padding: 40, color: 'var(--text-dim)' }}>No items configured yet.</div>
        )}
      </div>

      {aiOpen && <AIPanel itemCode={view === 'dashboard' ? selectedCode : null} onClose={() => setAiOpen(false)} />}
    </div>
  )
}
