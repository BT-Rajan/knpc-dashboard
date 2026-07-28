import { useState, FormEvent } from 'react'
import { api } from '../api/client'
import { setSession } from '../api/client'

export default function Login({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const res = await api.post<{ token: string; role: string; username: string }>('/api/auth/login', {
        username,
        password,
      })
      setSession(res.token, res.role, res.username)
      onLoggedIn()
    } catch {
      setError('Incorrect username or password.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <form onSubmit={submit} className="panel" style={{ padding: 40, width: 340 }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>KNPC · Market Intelligence</div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 500,
            fontSize: 28,
            margin: '0 0 28px',
            color: 'var(--text)',
          }}
        >
          Sign in
        </h1>

        <div className="field" style={{ marginBottom: 16 }}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </div>

        <div className="field" style={{ marginBottom: 24 }}>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>

        {error && (
          <div style={{ color: 'var(--negative)', fontSize: 13, marginBottom: 16 }}>{error}</div>
        )}

        <button type="submit" className="btn btn-brass" style={{ width: '100%' }} disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
