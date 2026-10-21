import { useState } from 'react'
import { Check, Copy, ArrowUpRight, ChevronDown } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import type { Citation } from '../api'
import type { Labels } from '../i18n'
export function CitationCard({
  citation: c,
  labels: t,
  index,
}: {
  citation: Citation
  labels: Labels
  index: number
}) {
  const [expanded, setExpanded] = useState(false),
    [copied, setCopied] = useState(false),
    [error, setError] = useState(false)
  const reduced = useReducedMotion()
  async function copyText() {
    try {
      await navigator.clipboard.writeText(
        `${c.title || c.source} — ${c.publisher}\np. ${c.page} · ${t.fragment} ${c.chunk_index}\n“${c.text}”\n${c.url}`,
      )
      setCopied(true)
      setError(false)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setError(true)
    }
  }
  return (
    <motion.article
      className="citation panel"
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: reduced ? 0 : index * 0.1, duration: 0.3 }}
    >
      <div className="citation-heading">
        <span className="rank mono">{String(c.rank).padStart(2, '0')}</span>
        <div className="citation-title">
          <h3>{c.title || c.source}</h3>
          <p>{c.publisher}</p>
        </div>
        <span
          className={`score mono ${c.score >= 0.8 ? 'green' : c.score >= 0.7 ? 'teal' : 'amber'}`}
        >
          <span className="score-track">
            <span style={{ width: `${Math.max(0, Math.min(100, c.score * 100))}%` }} />
          </span>
          {c.score.toFixed(2)}
        </span>
      </div>
      <p className="citation-meta mono">
        {c.lang && (
          <span className="lang-badge" title={t.langNames[c.lang]}>
            {c.lang.toUpperCase()}
          </span>
        )}
        p. {c.page} · {t.fragment} {c.chunk_index}
      </p>
      <blockquote className={expanded ? '' : 'clamped'}>{displayText(c.text)}</blockquote>
      <button
        className="text-button expand"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? t.less : t.full}
        <ChevronDown size={14} />
      </button>
      <div className="citation-footer">
        <a href={c.url} target="_blank" rel="noopener noreferrer">
          {t.official}
          <ArrowUpRight size={14} />
        </a>
        <button
          className="icon-button"
          onClick={() => void copyText()}
          aria-label={copied ? t.copied : t.copy}
          title={t.copy}
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
        </button>
      </div>
      <span className="copy-status" role="status">
        {copied ? t.copied : error ? t.copyError : ''}
      </span>
    </motion.article>
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
