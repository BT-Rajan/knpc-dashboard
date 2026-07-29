import { useEffect, useState } from 'react'
import { api, ApiError } from '../../api/client'

interface Status {
  deepseek_configured: boolean
  claude_configured: boolean
}

export default function AISettings() {
  const [status, setStatus] = useState<Status | null>(null)
  const [deepseekKey, setDeepseekKey] = useState('')
  const [claudeKey, setClaudeKey] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function load() {
    api.get<Status>('/api/admin/ai-credentials').then(setStatus)
  }

  useEffect(load, [])

  async function save() {
    setBusy(true)
    setError(null)
    setMessage(null)
    try {
      const body: Record<string, string> = {}
      if (deepseekKey.trim()) body.deepseek_api_key = deepseekKey.trim()
      if (claudeKey.trim()) body.claude_api_key = claudeKey.trim()
      const res = await api.put<Status>('/api/admin/ai-credentials', body)
      setStatus(res)
      setDeepseekKey('')
      setClaudeKey('')
      setMessage('Saved.')
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to save')
    } finally {
      setBusy(false)
    }
  }

  async function clearKey(provider: 'deepseek' | 'claude') {
    const body = provider === 'deepseek' ? { deepseek_api_key: '' } : { claude_api_key: '' }
    const res = await api.put<Status>('/api/admin/ai-credentials', body)
    setStatus(res)
  }

  return (
    <div className="panel" style={{ padding: 20, maxWidth: 480 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>AI provider keys</div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="field">
          <label>
            DeepSeek API key {status && (status.deepseek_configured
              ? <span className="positive" style={{ marginLeft: 6 }}>configured</span>
              : <span style={{ color: 'var(--text-dim)', marginLeft: 6 }}>not configured</span>)}
          </label>
          <input
            type="password"
            placeholder={status?.deepseek_configured ? '•••••••••••• (enter to replace)' : 'sk-...'}
            value={deepseekKey}
            onChange={(e) => setDeepseekKey(e.target.value)}
          />
          {status?.deepseek_configured && (
            <button className="btn" style={{ alignSelf: 'flex-start', marginTop: 4 }} onClick={() => clearKey('deepseek')}>
              Clear
            </button>
          )}
        </div>

        <div className="field">
          <label>
            Claude API key {status && (status.claude_configured
              ? <span className="positive" style={{ marginLeft: 6 }}>configured</span>
              : <span style={{ color: 'var(--text-dim)', marginLeft: 6 }}>not configured</span>)}
          </label>
          <input
            type="password"
            placeholder={status?.claude_configured ? '•••••••••••• (enter to replace)' : 'sk-ant-...'}
            value={claudeKey}
            onChange={(e) => setClaudeKey(e.target.value)}
          />
          {status?.claude_configured && (
            <button className="btn" style={{ alignSelf: 'flex-start', marginTop: 4 }} onClick={() => clearKey('claude')}>
              Clear
            </button>
          )}
        </div>

        <button className="btn btn-brass" onClick={save} disabled={busy || (!deepseekKey.trim() && !claudeKey.trim())}>
          {busy ? 'Saving…' : 'Save'}
        </button>

        {message && <div style={{ fontSize: 13, color: 'var(--positive)' }}>{message}</div>}
        {error && <div style={{ fontSize: 13, color: 'var(--negative)' }}>{error}</div>}
      </div>
    </div>
  )
}
