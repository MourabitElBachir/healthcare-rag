import { ArrowUpRight, RotateCw, X } from 'lucide-react'
import type { Health, Source } from '../api'
import type { Labels, Language } from '../i18n'
export function SourcePanel({
  t,
  lang,
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
  lang: Language
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
  const order: Language[] = lang === 'fr' ? ['fr', 'en'] : ['en', 'fr']
  return (
    <aside className="panel" aria-labelledby="panel-title">
      <div className="panel-top">
        <h2 id="panel-title">{t.library}</h2>
        <button className="icon-button" onClick={close} aria-label={t.close}>
          <X size={19} />
        </button>
      </div>
      <p className="panel-intro">{t.libraryText}</p>
      {order.map((l) => {
        const group = sources.filter((s) => s.lang === l)
        if (!group.length) return null
        return (
          <section key={l} className="source-group" aria-label={t.langNames[l]}>
            <h3>
              {t.langNames[l]} <span className="count">{group.length}</span>
            </h3>
            <ul>
              {group.map((s) => (
                <li key={s.filename}>
                  <a href={s.url} target="_blank" rel="noopener noreferrer" className="source-link">
                    <span>
                      <strong>{s.title || s.filename}</strong>
                      <span className="muted">
                        {s.publisher} · {s.kind.toUpperCase()}
                      </span>
                    </span>
                    <ArrowUpRight size={16} aria-hidden="true" />
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )
      })}
      {sourceFailed && <p className="small muted">{t.sourceError}</p>}
      {loading && !sources.length && <div className="skeleton tall" />}
      <section className="index-box" aria-label={t.index}>
        <div className="index-head">
          <h3>{t.index}</h3>
          <button
            className="icon-button"
            disabled={loading}
            onClick={refresh}
            aria-label={t.refresh}
          >
            <RotateCw size={15} className={loading ? 'spin' : ''} />
          </button>
        </div>
        <p>
          <span className={`dot ${failed ? 'off' : ''}`} aria-hidden="true" />
          {health && !failed ? (
            <>
              <strong>{health.chunks}</strong> {t.chunks}
            </>
          ) : failed ? (
            t.unavailable
          ) : (
            t.pending
          )}
        </p>
        <dl>
          <dt>{t.model}</dt>
          <dd className="break">{health?.model || '—'}</dd>
          <dt>{t.minimum}</dt>
          <dd>{minimum.toFixed(2)}</dd>
          <dt>{t.margin}</dt>
          <dd>{margin.toFixed(2)}</dd>
        </dl>
      </section>
      <p className="endorsement">{t.endorsement}</p>
    </aside>
  )
}
