import { useRef, useState } from 'react'
import { ArrowUp, Plus, SlidersHorizontal } from 'lucide-react'
import type { Labels } from '../i18n'
export function Composer({
  t,
  loading,
  ask,
  reset,
  k,
  setK,
}: {
  t: Labels
  loading: boolean
  ask: (q: string) => void
  reset: () => void
  k: number
  setK: (k: number) => void
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
        className="composer panel"
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
      >
        <div className="input-row">
          <label className="sr-only" htmlFor="question">
            {t.ask}
          </label>
          <textarea
            id="question"
            ref={input}
            rows={1}
            value={text}
            disabled={loading}
            placeholder={t.ask}
            onChange={(e) => {
              setText(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                send()
              }
            }}
          />
          <button className="send" disabled={loading || !text.trim()} aria-label={t.send}>
            <ArrowUp size={21} />
          </button>
        </div>
        <div className="composer-tools">
          <label className="k-select">
            <SlidersHorizontal size={13} />
            {t.topK}
            <select value={k} disabled={loading} onChange={(e) => setK(Number(e.target.value))}>
              {Array.from({ length: 10 }, (_, i) => (
                <option key={i} value={i + 1}>
                  {i + 1}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="text-button"
            disabled={loading}
            onClick={() => {
              reset()
              setText('')
              input.current?.focus()
            }}
          >
            <Plus size={14} />
            {t.newChat}
          </button>
          <span className="enter-hint mono">↵ {t.enter}</span>
        </div>
      </form>
      <p className="composer-note">{t.footer}</p>
    </div>
  )
}
