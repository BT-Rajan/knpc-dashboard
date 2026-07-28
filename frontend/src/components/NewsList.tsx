import { NewsOut } from '../types'

export default function NewsList({ news }: { news: NewsOut[] }) {
  return (
    <div className="panel" style={{ padding: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>News</div>
      {news.length === 0 ? (
        <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>No headlines collected yet.</div>
      ) : (
        <div>
          {news.map((n, i) => (
            <div key={i}>
              {i > 0 && <hr className="hairline" style={{ margin: '12px 0' }} />}
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                <a href={n.url ?? undefined} target="_blank" rel="noreferrer" style={{ fontSize: 14, color: 'var(--text)' }}>
                  {n.headline}
                </a>
                <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
                  {n.source}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
