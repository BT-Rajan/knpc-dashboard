import { useEffect, useState } from 'react'
import { api, ApiError } from '../../api/client'
import { ItemOut, SourceOut } from '../../types'

const SOURCE_TYPES = ['css', 'json_path', 'regex']

function emptySourceForm(itemId: number) {
  return {
    item_id: itemId,
    name: '',
    url: '',
    source_type: 'css',
    value_selector: '',
    news_selector: '',
    priority: 1,
    active: true,
  }
}

function sourceToForm(s: SourceOut) {
  return {
    item_id: s.item_id,
    name: s.name,
    url: s.url,
    source_type: s.source_type,
    value_selector: s.value_selector,
    news_selector: s.news_selector || '',
    priority: s.priority,
    active: s.active,
  }
}

function emptyItemForm() {
  return { code: '', name: '', category: 'Crude', unit: 'USD/bbl' }
}

export default function SourcesManager() {
  const [items, setItems] = useState<ItemOut[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [sourceForm, setSourceForm] = useState(emptySourceForm(0))
  const [editingId, setEditingId] = useState<number | null>(null)
  const [itemForm, setItemForm] = useState(emptyItemForm())
  const [showAddItem, setShowAddItem] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [scraping, setScraping] = useState(false)

  function reload() {
    api.get<ItemOut[]>('/api/admin/items').then((data) => {
      setItems(data)
      if (selectedId == null && data.length > 0) setSelectedId(data[0].id)
    })
  }

  useEffect(reload, [])

  const selected = items.find((i) => i.id === selectedId) || null

  useEffect(() => {
    if (selected) setSourceForm(emptySourceForm(selected.id))
    setEditingId(null)
  }, [selectedId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function addItem() {
    try {
      await api.post('/api/admin/items', { ...itemForm, code: itemForm.code.toUpperCase() })
      setItemForm(emptyItemForm())
      setShowAddItem(false)
      reload()
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : 'Failed to add item')
    }
  }

  function editSource(s: SourceOut) {
    setEditingId(s.id)
    setSourceForm(sourceToForm(s))
  }

  function cancelEdit() {
    setEditingId(null)
    if (selected) setSourceForm(emptySourceForm(selected.id))
  }

  async function saveSource() {
    try {
      if (editingId != null) {
        await api.patch(`/api/admin/sources/${editingId}`, sourceForm)
      } else {
        await api.post('/api/admin/sources', sourceForm)
      }
      setEditingId(null)
      setSourceForm(emptySourceForm(selected!.id))
      reload()
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : 'Failed to save source')
    }
  }

  async function toggleSource(s: SourceOut) {
    await api.patch(`/api/admin/sources/${s.id}`, { active: !s.active })
    reload()
  }

  async function deleteSource(s: SourceOut) {
    await api.delete(`/api/admin/sources/${s.id}`)
    reload()
  }

  async function scrapeNow() {
    if (!selected) return
    setScraping(true)
    setMessage(null)
    try {
      const res = await api.post<{ code: string; success: boolean }>(`/api/admin/scrape/run/${selected.code}`)
      setMessage(res.success ? `Scraped ${res.code} successfully.` : `Scrape failed for ${res.code} — check Logs.`)
    } finally {
      setScraping(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div className="panel" style={{ width: 240, padding: 12, alignSelf: 'flex-start' }}>
        <div className="eyebrow" style={{ padding: '4px 8px 10px' }}>Items</div>
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => setSelectedId(item.id)}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              background: item.id === selectedId ? 'var(--panel-raised)' : 'transparent',
              border: 'none',
              color: item.active ? (item.id === selectedId ? 'var(--brass-bright)' : 'var(--text)') : 'var(--text-dim)',
              padding: '8px 10px',
              fontSize: 13,
              borderRadius: 3,
            }}
          >
            {item.name} <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>· {item.category}</span>
          </button>
        ))}

        <hr className="hairline" style={{ margin: '10px 0' }} />

        {showAddItem ? (
          <div style={{ padding: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="field">
              <label>Code</label>
              <input value={itemForm.code} onChange={(e) => setItemForm({ ...itemForm, code: e.target.value })} />
            </div>
            <div className="field">
              <label>Name</label>
              <input value={itemForm.name} onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })} />
            </div>
            <div className="field">
              <label>Category</label>
              <select value={itemForm.category} onChange={(e) => setItemForm({ ...itemForm, category: e.target.value })}>
                <option>Crude</option>
                <option>Products</option>
              </select>
            </div>
            <div className="field">
              <label>Unit</label>
              <input value={itemForm.unit} onChange={(e) => setItemForm({ ...itemForm, unit: e.target.value })} />
            </div>
            <button className="btn btn-brass" onClick={addItem}>Save item</button>
          </div>
        ) : (
          <button className="btn" style={{ width: '100%' }} onClick={() => setShowAddItem(true)}>+ Add item</button>
        )}
      </div>

      <div style={{ flex: 1 }}>
        {selected && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 500, margin: 0 }}>
                {selected.name} sources
              </h2>
              <button className="btn btn-brass" onClick={scrapeNow} disabled={scraping}>
                {scraping ? 'Scraping…' : 'Scrape now'}
              </button>
            </div>

            {message && <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 14 }}>{message}</div>}

            <div className="panel" style={{ marginBottom: 20 }}>
              {selected.sources.length === 0 ? (
                <div style={{ padding: 20, color: 'var(--text-dim)', fontSize: 13 }}>
                  No sources configured for this item yet — add one below.
                </div>
              ) : (
                selected.sources
                  .sort((a, b) => a.priority - b.priority)
                  .map((s, i) => (
                    <div key={s.id}>
                      {i > 0 && <hr className="hairline" />}
                      <div style={{ padding: 14, display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 14, color: s.active ? 'var(--text)' : 'var(--text-dim)' }}>
                            {s.name} <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>#{s.priority}</span>
                          </div>
                          <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {s.source_type} · {s.url}
                          </div>
                          <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                            selector: {s.value_selector}
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                          <button className="btn" onClick={() => editSource(s)}>Edit</button>
                          <button className="btn" onClick={() => toggleSource(s)}>{s.active ? 'Disable' : 'Enable'}</button>
                          <button className="btn btn-danger" onClick={() => deleteSource(s)}>Delete</button>
                        </div>
                      </div>
                    </div>
                  ))
              )}
            </div>

            <div className="panel" style={{ padding: 18 }}>
              <div className="eyebrow" style={{ marginBottom: 12 }}>{editingId != null ? 'Edit source' : 'Add source'}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="field">
                  <label>Name</label>
                  <input value={sourceForm.name} onChange={(e) => setSourceForm({ ...sourceForm, name: e.target.value })} />
                </div>
                <div className="field">
                  <label>Type</label>
                  <select value={sourceForm.source_type} onChange={(e) => setSourceForm({ ...sourceForm, source_type: e.target.value })}>
                    {SOURCE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>URL</label>
                  <input value={sourceForm.url} onChange={(e) => setSourceForm({ ...sourceForm, url: e.target.value })} />
                </div>
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>Value selector (CSS selector / dotted JSON path / regex)</label>
                  <input value={sourceForm.value_selector} onChange={(e) => setSourceForm({ ...sourceForm, value_selector: e.target.value })} />
                </div>
                <div className="field" style={{ gridColumn: '1 / -1' }}>
                  <label>News selector (optional — CSS selector for headline links)</label>
                  <input value={sourceForm.news_selector} onChange={(e) => setSourceForm({ ...sourceForm, news_selector: e.target.value })} />
                </div>
                <div className="field">
                  <label>Priority (lower tried first)</label>
                  <input type="number" value={sourceForm.priority} onChange={(e) => setSourceForm({ ...sourceForm, priority: Number(e.target.value) })} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
                <button className="btn btn-brass" onClick={saveSource}>
                  {editingId != null ? 'Save changes' : 'Add source'}
                </button>
                {editingId != null && (
                  <button className="btn" onClick={cancelEdit}>Cancel</button>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
