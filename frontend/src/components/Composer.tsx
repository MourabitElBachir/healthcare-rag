import { useRef, useState } from 'react'
import { ArrowUp, RotateCcw } from 'lucide-react'
import type { Labels, Language } from '../i18n'
export function Composer({
  t,
  loading,
  ask,
  reset,
  hasTurns,
  k,
  setK,
  sourceLang,
  setSourceLang,
}: {
  t: Labels
  loading: boolean
  ask: (q: string) => void
  reset: () => void
  hasTurns: boolean
  k: number
  setK: (k: number) => void
  sourceLang: Language | null
  setSourceLang: (lang: Language | null) => void
}) {
  const [text, setText] = useState('')
  const input = useRef<HTMLTextAreaElement>(null)
  function send() {
    if (!text.trim() || loading) return
    ask(text.trim())
    setText('')
    if (input.current) input.current.style.height = 'auto'
  }
  return (
    <div className="composer-wrap">
      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
      >
        <label className="sr-only" htmlFor="question">
          {t.askLabel}
        </label>
        <textarea
          id="question"
          ref={input}
          rows={1}
          value={text}
          placeholder={t.ask}
          onChange={(e) => {
            setText(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = `${Math.min(e.target.scrollHeight, 168)}px`
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault()
              send()
            }
          }}
        />
        <button className="send" disabled={loading || !text.trim()} aria-label={t.send}>
          <ArrowUp size={20} aria-hidden="true" />
        </button>
      </form>
      <div className="composer-tools">
        <label className="select">
          <span>{t.sourceFilter}</span>
          <select
            aria-label={t.sourceFilter}
            value={sourceLang ?? 'all'}
            onChange={(e) =>
              setSourceLang(e.target.value === 'all' ? null : (e.target.value as Language))
            }
          >
            <option value="all">{t.allSources}</option>
            <option value="en">{t.langNames.en}</option>
            <option value="fr">{t.langNames.fr}</option>
          </select>
        </label>
        <label className="select">
          <span>{t.topK}</span>
          <select aria-label={t.topK} value={k} onChange={(e) => setK(Number(e.target.value))}>
            {Array.from({ length: 10 }, (_, i) => (
              <option key={i} value={i + 1}>
                {i + 1}
              </option>
            ))}
          </select>
        </label>
        {hasTurns && (
          <button
            type="button"
            className="link-button"
            disabled={loading}
            onClick={() => {
              reset()
              setText('')
              input.current?.focus()
            }}
          >
            <RotateCcw size={15} aria-hidden="true" />
            {t.newChat}
          </button>
        )}
      </div>
      <p className="composer-note">{t.footer}</p>
    </div>
  )
}
