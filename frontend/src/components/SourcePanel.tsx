import { ArrowUpRight, BookOpen, Database, RotateCw, X } from 'lucide-react'
import type { Health, Source } from '../api'
import type { Labels } from '../i18n'
export function SourcePanel({
  t,
  sources,
  health,
  failed,
  sourceFailed,
  loading,
  refresh,
  close,
  minimum,
  margin,
}: {
  t: Labels
  sources: Source[]
  health: Health | null
  failed: boolean
  sourceFailed: boolean
  loading: boolean
  refresh: () => void
  close: () => void
  minimum: number
  margin: number
}) {
  return (
    <aside className="source-panel" aria-label={t.sources}>
      <div className="source-top">
        <span className="eyebrow">{t.collection}</span>
        <button className="icon-button" onClick={close} aria-label={t.close}>
          <X size={18} />
        </button>
      </div>
      <h2>{t.library}</h2>
      <p className="source-intro">{t.libraryText}</p>
      <div className="source-label">
        <BookOpen size={14} />
        {t.documents}
        <span className="mono">{String(sources.length).padStart(2, '0')}</span>
      </div>
      <div className="source-list">
        {sources.map((s, i) => (
          <a
            key={s.filename}
            className="source-item"
            href={s.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            <span className="source-number mono">0{i + 1}</span>
            <div>
              <h3>{s.title || s.filename}</h3>
              <p>{s.publisher}</p>
              <span className="source-kind mono">{s.kind.toUpperCase()} · FR</span>
            </div>
            <ArrowUpRight size={15} />
          </a>
        ))}
        {sourceFailed && <p className="small muted">{t.sourceError}</p>}
        {loading && !sources.length && <div className="source-skeleton skeleton" />}
      </div>
      <div className="index-card">
        <div className="index-heading">
          <Database size={15} />
          <h3>{t.index}</h3>
          <button
            className="icon-button"
            disabled={loading}
            onClick={refresh}
            aria-label={t.refresh}
          >
            <RotateCw size={13} className={loading ? 'spin' : ''} />
          </button>
        </div>
        <p className="index-count">
          <span className={`status-dot ${failed ? 'offline' : ''}`} />
          {health && !failed ? (
            <>
              <strong className="mono">{health.chunks}</strong> {t.chunks}
            </>
          ) : failed ? (
            t.unavailable
          ) : (
            t.pending
          )}
        </p>
        <p className="meta-label">{t.model}</p>
        <p className="model mono">{health?.model || '—'}</p>
        <div className="filter-heading">{t.filters}</div>
        <div className="filter-row">
          <span>{t.minimum}</span>
          <span className="mono">{minimum.toFixed(2)}</span>
        </div>
        <div className="filter-row">
          <span>{t.margin}</span>
          <span className="mono">{margin.toFixed(2)}</span>
        </div>
      </div>
      <div className="source-bottom">
        <span className="status-dot" />
        {t.searchNote}
      </div>
    </aside>
  )
}
