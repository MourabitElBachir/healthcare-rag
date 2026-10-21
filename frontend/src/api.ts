export interface Health {
  status: string
  chunks: number
  embedder: string
  model: string
}
export interface Source {
  filename: string
  title: string
  publisher: string
  url: string
  kind: string
  lang: 'fr' | 'en'
}
export interface Citation {
  rank: number
  source: string
  title: string
  publisher: string
  url: string
  lang: 'fr' | 'en' | null
  page: number
  chunk_index: number
  score: number
  text: string
}
export interface Answer {
  question: string
  refused: boolean
  message: { fr: string; en: string } | null
  citations: Citation[]
  k: number
  source_lang: 'fr' | 'en' | null
  min_score: number
  score_margin: number
  took_ms: number
}
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { ...init, signal: AbortSignal.timeout(30000) })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json() as Promise<T>
}
export const api = {
  health: () => request<Health>('/api/health'),
  sources: () => request<Source[]>('/api/sources'),
  ask: (question: string, k: number, sourceLang: 'fr' | 'en' | null = null) =>
    request<Answer>('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, k, source_lang: sourceLang }),
    }),
}
