import { useState } from 'react'
import { api, ApiError } from '../api/client'
import { AIAskResponse } from '../types'

export default function AIPanel({ itemCode, onClose }: { itemCode: string | null; onClose: () => void }) {
  const [provider, setProvider] = useState<'deepseek' | 'claude'>('claude')
  const [question, setQuestion] = useState('')
  const [useContext, setUseContext] = useState(true)
  const [answer, setAnswer] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function ask() {
    if (!question.trim()) return
    setBusy(true)
    setError(null)
    setAnswer(null)
    try {
      const res = await api.post<AIAskResponse>('/api/ai/ask', {
        provider,
        question,
        item_code: useContext ? itemCode : null,
      })
      setAnswer(res.answer)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        height: '100%',
        width: 380,
        background: 'var(--panel)',
        borderLeft: '1px solid var(--border)',
        zIndex: 40,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-16px 0 40px rgba(0,0,0,0.5)',
      }}
    >
      <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="eyebrow">AI Facility</div>
        <button className="btn" onClick={onClose}>Close</button>
      </div>

      <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', flex: 1 }}>
        <div className="field">
          <label>Provider</label>
          <select value={provider} onChange={(e) => setProvider(e.target.value as 'deepseek' | 'claude')}>
            <option value="claude">Claude</option>
            <option value="deepseek">DeepSeek</option>
          </select>
        </div>

        {itemCode && (
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-muted)' }}>
            <input type="checkbox" checked={useContext} onChange={(e) => setUseContext(e.target.checked)} />
            Ground answer in {itemCode} price &amp; news
          </label>
        )}

        <div className="field">
          <label>Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={4}
            style={{
              background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)',
              padding: 10, borderRadius: 3, fontSize: 13, resize: 'vertical',
            }}
            placeholder="e.g. What's driving the move this week?"
          />
        </div>

        <button className="btn btn-brass" onClick={ask} disabled={busy}>
          {busy ? 'Asking…' : 'Ask'}
        </button>

        {error && <div style={{ color: 'var(--negative)', fontSize: 13 }}>{error}</div>}

        {answer && (
          <div className="panel" style={{ padding: 16, fontSize: 13.5, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {answer}
          </div>
        )}
      </div>
    </div>
  )
}
