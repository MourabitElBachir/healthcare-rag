import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Check,
  CircleAlert,
  Fingerprint,
  HeartPulse,
  Menu,
  Moon,
  ShieldCheck,
  Sparkles,
  Sun,
  X,
} from 'lucide-react'
import { MotionConfig } from 'motion/react'
import { api } from './api'
import type { Answer, Health, Source } from './api'
import { copy, questions } from './i18n'
import type { Language } from './i18n'
import { CitationCard } from './components/CitationCard'
import { Composer } from './components/Composer'
import { SourcePanel } from './components/SourcePanel'
interface Turn {
  id: number
  question: string
  k: number
  answer?: Answer
  error?: boolean
}
function saved(key: string, fallback: string) {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}
export default function App() {
  const [lang, setLang] = useState<Language>(() =>
      saved('medsource-language', 'fr') === 'en' ? 'en' : 'fr',
    ),
    [dark, setDark] = useState(() => saved('medsource-theme', 'dark') !== 'light')
  const [notice, setNotice] = useState(true),
    [panel, setPanel] = useState(() => window.innerWidth >= 1100),
    [sources, setSources] = useState<Source[]>([]),
    [health, setHealth] = useState<Health | null>(null),
    [healthFailed, setHealthFailed] = useState(false),
    [sourceFailed, setSourceFailed] = useState(false),
    [indexLoading, setIndexLoading] = useState(true),
    [turns, setTurns] = useState<Turn[]>([]),
    [loading, setLoading] = useState(false),
    [k, setK] = useState(4)
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
      localStorage.setItem('medsource-theme', dark ? 'dark' : 'light')
    } catch {
      /* Storage is optional. */
    }
  }, [lang, dark])
  const refresh = useCallback(async () => {
    setIndexLoading(true)
    const [h, s] = await Promise.allSettled([api.health(), api.sources()])
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
    if (turns.length) end.current?.scrollIntoView({ behavior: 'instant', block: 'end' })
  }, [turns, loading])
  useEffect(() => {
    if (!panel || window.innerWidth >= 1100) return
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
  async function ask(question: string, requestedK = k, retryId?: number) {
    if (busy.current || !question.trim()) return
    busy.current = true
    setLoading(true)
    const id = retryId ?? ++nextId.current
    setTurns((prev) =>
      retryId
        ? prev.map((x) => (x.id === id ? { id, question, k: requestedK } : x))
        : [...prev, { id, question, k: requestedK }],
    )
    try {
      const answer = await api.ask(question, requestedK)
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
  return (
    <MotionConfig reducedMotion="user">
      <div className="app">
        <a className="skip-link" href="#main">
          {t.skip}
        </a>
        <header className="topbar">
          <div className="brand">
            <span className="logo">
              <Activity size={25} />
            </span>
            <span>
              <span className="brand-name">
                MedSource <span className="rag mono">RAG</span>
              </span>
              <span className="tagline">{t.tagline}</span>
            </span>
          </div>
          <div className="header-actions">
            <span className="header-badge">
              <span className="status-dot" /> RETRIEVAL, NOT GENERATION
            </span>
            <div className="language-toggle" aria-label="Language">
              {(['fr', 'en'] as const).map((l) => (
                <button key={l} aria-pressed={lang === l} onClick={() => setLang(l)}>
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
            <button
              className="icon-button theme-button"
              onClick={() => setDark(!dark)}
              aria-label={t.theme}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              ref={trigger}
              className="sources-toggle"
              aria-expanded={panel}
              aria-controls="source-drawer"
              onClick={() => setPanel(!panel)}
            >
              <Menu size={17} />
              <span>{t.sources}</span>
            </button>
          </div>
        </header>
        <div className={`workspace ${panel ? 'panel-open' : ''}`}>
          <div className="main-column">
            {notice && (
              <div className="disclaimer">
                <ShieldCheck size={17} />
                <p>
                  <strong>{t.disclaimer}</strong> — {t.notice}
                </p>
                <button
                  className="icon-button"
                  onClick={() => setNotice(false)}
                  aria-label={t.close}
                >
                  <X size={15} />
                </button>
              </div>
            )}
            <main id="main" className={turns.length ? 'conversation' : 'empty-main'}>
              {!turns.length ? (
                <>
                  <section className="hero">
                    <div className="hero-emblem">
                      <HeartPulse size={33} strokeWidth={1.4} />
                      <span className="emblem-dot" />
                    </div>
                    <p className="eyebrow">
                      <span /> {t.eyebrow}
                    </p>
                    <h1>
                      {t.title}
                      <br />
                      <span>{t.accent}</span>
                    </h1>
                    <p className="hero-description">{t.description}</p>
                    <div className="feature-pills">
                      <span>
                        <Fingerprint size={14} />
                        {t.local}
                      </span>
                      <span>
                        <Check size={14} />
                        {t.noLlm}
                      </span>
                      <span>
                        <Check size={14} />
                        {t.noPaid}
                      </span>
                    </div>
                  </section>
                  <section className="suggestions">
                    <div className="suggestions-heading">
                      <h2>{t.suggestions}</h2>
                      <span>
                        {t.french} <span className="tiny-fr">FR</span>
                      </span>
                    </div>
                    <div className="question-grid">
                      {questions.map((q, i) => {
                        const Icon = [HeartPulse, Sparkles, ShieldCheck, Activity][i]!
                        return (
                          <button key={q} onClick={() => void ask(q)} disabled={loading}>
                            <span className="question-icon">
                              <Icon size={18} strokeWidth={1.6} />
                            </span>
                            <span>{q}</span>
                            <ArrowUpRight className="question-arrow" size={16} />
                          </button>
                        )
                      })}
                    </div>
                  </section>
                  <div className="trust-line">
                    <span />
                    <BookOpen size={13} />
                    ANSM · Santé publique France · HAS
                    <span />
                  </div>
                </>
              ) : (
                <div className="turns" aria-live="polite" aria-relevant="additions text">
                  {turns.map((turn) => (
                    <section className="turn" key={turn.id}>
                      <div className="user-message">
                        <span className="user-label">{t.you}</span>
                        <p>{turn.question}</p>
                      </div>
                      <div className="assistant-label">
                        <span className="mini-logo">
                          <Activity size={16} />
                        </span>
                        MedSource <span className="mono">/ {t.assistant}</span>
                      </div>
                      {turn.error ? (
                        <div className="state-card error-card">
                          <CircleAlert size={23} />
                          <div>
                            <h3>{t.error}</h3>
                            <p>{t.errorHint}</p>
                            <button
                              className="text-button"
                              disabled={loading}
                              onClick={() => void ask(turn.question, turn.k, turn.id)}
                            >
                              {t.retry}
                            </button>
                          </div>
                        </div>
                      ) : turn.answer ? (
                        turn.answer.refused ? (
                          <div className="state-card">
                            <ShieldCheck size={24} />
                            <div>
                              <h3>{t.refusal}</h3>
                              <p>{turn.answer.message?.[lang] || t.empty}</p>
                              <p className="muted small">{t.hint}</p>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="answer-heading">
                              <span>
                                <span className="status-dot" />
                                {turn.answer.citations.length}{' '}
                                {turn.answer.citations.length === 1 ? t.passage : t.passages}
                              </span>
                              <span className="mono">{turn.answer.took_ms} ms</span>
                            </div>
                            {turn.answer.citations.length ? (
                              turn.answer.citations.map((c, i) => (
                                <CitationCard
                                  key={`${c.source}-${c.chunk_index}-${i}`}
                                  citation={c}
                                  labels={t}
                                  index={i}
                                />
                              ))
                            ) : (
                              <div className="state-card">{t.empty}</div>
                            )}
                          </>
                        )
                      ) : (
                        <div className="loading-state" role="status">
                          <div className="search-heading">
                            <span className="search-orbit" />
                            {t.searching}
                            <span className="loading-dots">...</span>
                          </div>
                          <p className="mono">{t.steps}</p>
                          {[0, 1].map((i) => (
                            <div className="skeleton-card panel" key={i}>
                              <div className="skeleton skeleton-title" />
                              <div className="skeleton" />
                              <div className="skeleton" />
                              <div className="skeleton short" />
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                  ))}
                </div>
              )}
              <div ref={end} />
            </main>
            <Composer
              t={t}
              loading={loading}
              ask={(q) => void ask(q)}
              reset={() => setTurns([])}
              k={k}
              setK={setK}
            />
          </div>
          <button
            className="drawer-backdrop"
            aria-label={t.close}
            tabIndex={panel ? 0 : -1}
            onClick={closePanel}
          />
          <div id="source-drawer" ref={drawer} className="source-drawer" inert={!panel}>
            <SourcePanel
              t={t}
              sources={sources}
              health={health}
              failed={healthFailed}
              sourceFailed={sourceFailed}
              loading={indexLoading}
              refresh={() => void refresh()}
              close={closePanel}
              minimum={latest?.min_score ?? 0.6}
              margin={latest?.score_margin ?? 0.08}
            />
          </div>
        </div>
      </div>
    </MotionConfig>
  )
}
