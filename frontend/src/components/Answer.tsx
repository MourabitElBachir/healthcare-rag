import { useState } from 'react'
import { ArrowUpRight, Check, ChevronDown, Copy } from 'lucide-react'
import type { Answer as AnswerData, Citation } from '../api'
import { matchLevel, shortName } from '../i18n'
import type { Labels } from '../i18n'

/** Evidence-first answer: a plain summary, identifiable source chips, then the quoted passages. */
export function Answer({ answer, t, turnId }: { answer: AnswerData; t: Labels; turnId: number }) {
  const citations = answer.citations
  const sources = new Set(citations.map((c) => c.source)).size
  const anchor = (c: Citation) => `turn-${turnId}-passage-${c.rank}`
  return (
    <article className="answer card" aria-label={t.basedOn(citations.length, sources)}>
      <header className="answer-head">
        <p className="answer-summary">{t.basedOn(citations.length, sources)}</p>
        <ul className="chips" aria-label={t.sources}>
          {citations.map((c) => (
            <li key={c.rank}>
              <a
                className="chip"
                href={`#${anchor(c)}`}
                title={`${t.jump} ${c.rank} · ${c.title || c.source}`}
                onClick={(e) => {
                  e.preventDefault()
                  const el = document.getElementById(anchor(c))
                  el?.scrollIntoView({ block: 'start' })
                  el?.focus({ preventScroll: true })
                }}
              >
                <span className="chip-num" aria-hidden="true">
                  {c.rank}
                </span>
                <span className="chip-name">{shortName(c.source, c.publisher)}</span>
                {c.lang && <span className="chip-lang">{c.lang.toUpperCase()}</span>}
              </a>
            </li>
          ))}
        </ul>
      </header>
      <ol className="passages">
        {citations.map((c) => (
          <Passage key={c.rank} citation={c} t={t} id={anchor(c)} />
        ))}
      </ol>
    </article>
  )
}

function Passage({ citation: c, t, id }: { citation: Citation; t: Labels; id: string }) {
  const [expanded, setExpanded] = useState(false),
    [copied, setCopied] = useState(false),
    [error, setError] = useState(false)
  const level = matchLevel(c.score)
  const long = c.text.trim().length > 320
  async function copyText() {
    try {
      await navigator.clipboard.writeText(
        `“${c.text.trim()}”\n— ${c.title || c.source}, ${c.publisher} (${t.page} ${c.page})\n${c.url}`,
      )
      setCopied(true)
      setError(false)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setError(true)
    }
  }
  return (
    <li className="passage" id={id} tabIndex={-1}>
      <div className="passage-head">
        <span className="passage-num" aria-hidden="true">
          {c.rank}
        </span>
        <div className="passage-title">
          <h3>{c.title || c.source}</h3>
          <p>
            {c.publisher}
            {c.lang && (
              <>
                {' · '}
                <span className="lang" title={t.langBadge[c.lang]}>
                  {c.lang.toUpperCase()}
                  <span className="sr-only"> ({t.langBadge[c.lang]})</span>
                </span>
              </>
            )}
          </p>
        </div>
        <span className={`match ${level}`} title={`${t.score} ${c.score.toFixed(2)}`}>
          <span className="match-dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          {t.match[level]}
        </span>
      </div>
      <blockquote className={expanded || !long ? '' : 'clamped'}>{displayText(c.text)}</blockquote>
      <div className="passage-foot">
        {long && (
          <button
            type="button"
            className="link-button"
            aria-expanded={expanded}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? t.less : t.full}
            <ChevronDown size={16} className={expanded ? 'flip' : ''} aria-hidden="true" />
          </button>
        )}
        <span className="meta">
          {t.page} {c.page} · {t.fragment} {c.chunk_index} · {t.score} {c.score.toFixed(2)}
        </span>
        <span className="spacer" />
        <a className="link-button" href={c.url} target="_blank" rel="noopener noreferrer">
          {t.official}
          <ArrowUpRight size={16} aria-hidden="true" />
        </a>
        <button
          type="button"
          className="icon-button"
          onClick={() => void copyText()}
          aria-label={copied ? t.copied : t.copy}
          title={t.copy}
        >
          {copied ? <Check size={17} /> : <Copy size={17} />}
        </button>
      </div>
      <span className="sr-only" role="status">
        {copied ? t.copied : error ? t.copyError : ''}
      </span>
      {error && <p className="small muted">{t.copyError}</p>}
    </li>
  )
}

/** Chunks are fixed-size character windows: mark cut-off edges with an ellipsis
 *  instead of altering the cited text. */
function displayText(text: string): string {
  const trimmed = text.trim()
  const startsMidSentence = /^[a-z0-9à-ÿœæ,;:)]/.test(trimmed)
  const endsMidSentence = !/[.!?…»)\]]$/.test(trimmed)
  return `${startsMidSentence ? '… ' : ''}${trimmed}${endsMidSentence ? ' …' : ''}`
}
