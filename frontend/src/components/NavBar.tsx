import { useEffect, useRef, useState } from 'react'
import { NavCategory } from '../types'

interface Props {
  categories: NavCategory[]
  selectedCode: string | null
  onSelect: (code: string) => void
  role: string | null
  view: 'dashboard' | 'admin'
  onChangeView: (v: 'dashboard' | 'admin') => void
  onAskAI: () => void
  onLogout: () => void
  username: string | null
}

export default function NavBar({
  categories, selectedCode, onSelect, role, view, onChangeView, onAskAI, onLogout, username,
}: Props) {
  const [openCategory, setOpenCategory] = useState<string | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpenCategory(null)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div
      ref={rootRef}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        height: 52,
        borderBottom: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 17,
            letterSpacing: '0.01em',
            marginRight: 28,
            color: 'var(--text)',
          }}
        >
          KNPC
        </span>

        {categories.map((cat) => (
          <div key={cat.category} style={{ position: 'relative' }}>
            <button
              onClick={() => {
                setOpenCategory(openCategory === cat.category ? null : cat.category)
                onChangeView('dashboard')
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: openCategory === cat.category ? 'var(--brass-bright)' : 'var(--text-muted)',
                fontSize: 13,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                padding: '8px 14px',
              }}
            >
              {cat.category} ▾
            </button>
            {openCategory === cat.category && (
              <div
                className="panel"
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 6px)',
                  left: 0,
                  minWidth: 200,
                  padding: 6,
                  zIndex: 20,
                  boxShadow: '0 12px 28px rgba(0,0,0,0.45)',
                }}
              >
                {cat.items.map((item) => (
                  <button
                    key={item.code}
                    onClick={() => {
                      onSelect(item.code)
                      setOpenCategory(null)
                    }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      background: item.code === selectedCode ? 'var(--panel-raised)' : 'transparent',
                      border: 'none',
                      color: item.code === selectedCode ? 'var(--brass-bright)' : 'var(--text)',
                      padding: '9px 12px',
                      fontSize: 13,
                      borderRadius: 'var(--radius)',
                    }}
                  >
                    {item.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <button className="btn" onClick={onAskAI}>Ask AI</button>
        {role === 'admin' && (
          <button
            className={view === 'admin' ? 'btn btn-brass' : 'btn'}
            onClick={() => onChangeView(view === 'admin' ? 'dashboard' : 'admin')}
          >
            Admin
          </button>
        )}
        <span className="eyebrow" style={{ marginLeft: 6 }}>{username}</span>
        <button className="btn" onClick={onLogout}>Sign out</button>
      </div>
    </div>
  )
}
