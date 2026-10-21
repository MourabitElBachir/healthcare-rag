import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Activity,
  ArrowRight,
  BookOpenCheck,
  CircleAlert,
  Languages,
  Library,
  Moon,
  Quote,
  ShieldCheck,
  Sun,
} from 'lucide-react'
import { api } from './api'
import type { Answer as AnswerData, Health, Source } from './api'
import { browserLanguage, copy, questions } from './i18n'
import type { Language } from './i18n'
import { Answer } from './components/Answer'
import { Composer } from './components/Composer'
import { SourcePanel } from './components/SourcePanel'
import { EVAL } from './evalResult'

interface Turn {
  id: number
  question: string
  k: number
  sourceLang: Language | null
  answer?: AnswerData
  error?: boolean
}
function saved(key: string, fallback: string) {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}
const TRUST = ['CDC', 'FDA', 'HAS', 'ANSM', 'Santé.fr', 'Santé publique France']

export default function App() {
  const [lang, setLang] = useState<Language>(() => {
      const stored = saved('medsource-language', '')
      return stored === 'fr' || stored === 'en' ? stored : browserLanguage()
    }),
    [dark, setDark] = useState(() => saved('medsource-theme-v2', 'light') === 'dark')
  const [panel, setPanel] = useState(false),
    [sources, setSources] = useState<Source[]>([]),
    [health, setHealth] = useState<Health | null>(null),
    [latency, setLatency] = useState<number | null>(null),
    [healthFailed, setHealthFailed] = useState(false),
    [sourceFailed, setSourceFailed] = useState(false),
    [indexLoading, setIndexLoading] = useState(true),
    [turns, setTurns] = useState<Turn[]>([]),
    [loading, setLoading] = useState(false),
    [k, setK] = useState(4),
    [sourceLang, setSourceLang] = useState<Language | null>(null)
  const nextId = useRef(0)
  const busy = useRef(false),
    end = useRef<HTMLDivElement>(null),
    drawer = useRef<HTMLDivElement>(null),
    trigger = useRef<HTMLButtonElement>(null)
  const t = copy[lang]

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.classList.toggle('dark', dark)
    try {
      localStorage.setItem('medsource-language', lang)
      localStorage.setItem('medsource-theme-v2', dark ? 'dark' : 'light')
    } catch {
      /* Storage is optional. */
    }
  }, [lang, dark])

  const refresh = useCallback(async () => {
    setIndexLoading(true)
    const started = performance.now()
    const [h, s] = await Promise.allSettled([
      api.health().then((value) => {
        setLatency(Math.round(performance.now() - started))
        return value
      }),
      api.sources(),
    ])
    setHealthFailed(h.status === 'rejected')
    setSourceFailed(s.status === 'rejected')
    if (h.status === 'fulfilled') setHealth(h.value)
    if (s.status === 'fulfilled') setSources(s.value)
    setIndexLoading(false)
  }, [])
  useEffect(() => {
    void Promise.resolve().then(refresh)
  }, [refresh])
  useEffect(() => {
    if (turns.length) end.current?.scrollIntoView({ block: 'end' })
  }, [turns, loading])

  // Drawer: modal on every screen size, Escape closes, focus stays inside.
  useEffect(() => {
    if (!panel) return
    const old = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    drawer.current?.querySelector<HTMLButtonElement>('button')?.focus()
    function key(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setPanel(false)
        trigger.current?.focus()
      }
      if (e.key === 'Tab') {
        const nodes = drawer.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), a[href]',
        )
        if (!nodes?.length) return
        const first = nodes[0],
          last = nodes[nodes.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last?.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first?.focus()
        }
      }
    }
    document.addEventListener('keydown', key)
    return () => {
      document.body.style.overflow = old
      document.removeEventListener('keydown', key)
    }
  }, [panel])

  async function ask(question: string, requestedK = k, retryId?: number, filter = sourceLang) {
    if (busy.current || !question.trim()) return
    busy.current = true
    setLoading(true)
    const id = retryId ?? ++nextId.current
    const turn = { id, question, k: requestedK, sourceLang: filter }
    setTurns((prev) => (retryId ? prev.map((x) => (x.id === id ? turn : x)) : [...prev, turn]))
    try {
      const answer = await api.ask(question, requestedK, filter)
      setTurns((prev) => prev.map((x) => (x.id === id ? { ...x, answer } : x)))
    } catch {
      setTurns((prev) => prev.map((x) => (x.id === id ? { ...x, error: true } : x)))
    } finally {
      busy.current = false
      setLoading(false)
    }
  }
  const latest = turns.findLast((x) => x.answer)?.answer
  function closePanel() {
    setPanel(false)
    trigger.current?.focus()
  }
  const composer = (
    <Composer
      t={t}
      loading={loading}
      ask={(q) => void ask(q)}
      reset={() => setTurns([])}
      hasTurns={turns.length > 0}
      k={k}
      setK={setK}
      sourceLang={sourceLang}
      setSourceLang={setSourceLang}
    />
  )
  const metrics = [
    { value: sources.length || '—', label: t.mSources, live: true },
    { value: health ? health.chunks : '—', label: t.mPassages, live: true },
    {
      value: `${Math.round((EVAL.hits / EVAL.total) * 100)}%`,
      label: t.mEval(EVAL.hits, EVAL.total),
      live: false,
    },
    { value: latency !== null ? `${latency} ms` : '—', label: t.mLatency, live: true },
  ]

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        {t.skip}
      </a>
      <header className="topbar">
        <a className="brand" href="/" aria-label="MedSource">
          <span className="logo" aria-hidden="true">
            <Activity size={19} strokeWidth={2.2} />
          </span>
          <span className="brand-text">
            <span className="brand-name">MedSource</span>
            <span className="brand-tag">{t.tagline}</span>
          </span>
        </a>
        <nav className="actions" aria-label={t.settings}>
          <div className="segmented" role="group" aria-label={t.language}>
            {(['en', 'fr'] as const).map((l) => (
              <button key={l} aria-pressed={lang === l} onClick={() => setLang(l)}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>
          <button
            className="icon-button"
            onClick={() => setDark(!dark)}
            aria-label={dark ? t.themeLight : t.themeDark}
            title={dark ? t.themeLight : t.themeDark}
          >
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            ref={trigger}
            className="pill-button"
            aria-expanded={panel}
            aria-controls="source-drawer"
            aria-label={sources.length ? `${t.sources} (${sources.length})` : t.sources}
            onClick={() => setPanel(true)}
          >
            <Library size={16} aria-hidden="true" />
            <span>{t.sources}</span>
            <span className="count">{sources.length || ''}</span>
          </button>
        </nav>
      </header>

      <main id="main" className={turns.length ? 'thread' : 'home'}>
        {!turns.length ? (
          <>
            <section className="hero" aria-labelledby="hero-title">
              <p className="eyebrow">
                <span className="dot" aria-hidden="true" /> {t.eyebrow}
              </p>
              <h1 id="hero-title">
                {t.title} <span className="accent">{t.titleAccent}</span>
              </h1>
              <p className="lede">{t.subtitle}</p>
              <div className="hero-composer">{composer}</div>
              <div className="trust" aria-label={t.from}>
                <span className="trust-label">{t.from}</span>
                <ul>
                  {TRUST.map((name) => (
                    <li key={name}>{name}</li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="metrics" aria-label={t.metricsLabel}>
              {metrics.map((m) => (
                <div className="metric" key={m.label}>
                  <span className="metric-value">{m.value}</span>
                  <span className="metric-label">
                    {m.label}
                    {m.live && (
                      <span className="live" title={t.liveTitle}>
                        {t.live}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </section>

            <section className="suggestions" aria-labelledby="suggest-title">
              <h2 id="suggest-title">{t.suggestions}</h2>
              <ul>
                {questions[lang].map((q) => (
                  <li key={q}>
                    <button onClick={() => void ask(q)} disabled={loading}>
                      <span>{q}</span>
                      <ArrowRight size={17} aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            <section className="principles" aria-label={t.principlesLabel}>
              {[
                { icon: Quote, title: t.p1, text: t.p1Text },
                { icon: ShieldCheck, title: t.p2, text: t.p2Text },
                { icon: Languages, title: t.p3, text: t.p3Text },
              ].map(({ icon: Icon, title, text }) => (
                <div className="principle" key={title}>
                  <span className="principle-icon" aria-hidden="true">
                    <Icon size={18} />
                  </span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              ))}
            </section>

            <aside className="notice" aria-label={t.disclaimerTitle}>
              <BookOpenCheck size={18} aria-hidden="true" />
              <p>
                <strong>{t.disclaimerTitle}</strong> {t.disclaimer}
              </p>
            </aside>
          </>
        ) : (
          <>
            <h1 className="sr-only">MedSource</h1>
            <div className="turns" aria-live="polite" aria-relevant="additions text">
              {turns.map((turn) => (
                <section className="turn" key={turn.id} aria-label={turn.question}>
                  <p className="question-label">{t.you}</p>
                  <h2 className="question">{turn.question}</h2>
                  {turn.error ? (
                    <div className="card state error">
                      <CircleAlert size={20} aria-hidden="true" />
                      <div>
                        <h3>{t.error}</h3>
                        <p>{t.errorHint}</p>
                        <button
                          className="link-button"
                          disabled={loading}
                          onClick={() => void ask(turn.question, turn.k, turn.id, turn.sourceLang)}
                        >
                          {t.retry}
                        </button>
                      </div>
                    </div>
                  ) : turn.answer ? (
                    turn.answer.refused || !turn.answer.citations.length ? (
                      <div className="card state refusal">
                        <ShieldCheck size={20} aria-hidden="true" />
                        <div>
                          <h3>{t.refusal}</h3>
                          <p>{turn.answer.message?.[lang] || t.refusalText}</p>
                          <p className="muted">{t.refusalText}</p>
                          <p className="muted">{t.hint}</p>
                        </div>
                      </div>
                    ) : (
                      <Answer answer={turn.answer} t={t} turnId={turn.id} />
                    )
                  ) : (
                    <div className="card loading" role="status">
                      <p>
                        <span className="breathe" aria-hidden="true" />
                        {t.searching}
                      </p>
                      <div className="skeleton" />
                      <div className="skeleton" />
                      <div className="skeleton short" />
                    </div>
                  )}
                </section>
              ))}
              <div ref={end} />
            </div>
          </>
        )}
      </main>

      {turns.length > 0 && (
        <section className="dock" aria-label={t.askLabel}>
          {composer}
        </section>
      )}

      <div className={`backdrop ${panel ? 'open' : ''}`} onClick={closePanel} aria-hidden="true" />
      <div
        id="source-drawer"
        ref={drawer}
        className={`drawer ${panel ? 'open' : ''}`}
        inert={!panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="panel-title"
      >
        <SourcePanel
          t={t}
          lang={lang}
          sources={sources}
          health={health}
          failed={healthFailed}
          sourceFailed={sourceFailed}
          loading={indexLoading}
          refresh={() => void refresh()}
          close={closePanel}
          minimum={latest?.min_score ?? 0.55}
          margin={latest?.score_margin ?? 0.08}
        />
      </div>
    </div>
  )
}
