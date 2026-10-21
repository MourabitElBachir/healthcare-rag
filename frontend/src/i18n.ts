export type Language = 'fr' | 'en'
export const copy = {
  en: {
    tagline: 'Health answers from official sources',
    sources: 'Sources',
    newChat: 'New question',
    disclaimerTitle: 'Information, not medical advice.',
    disclaimer:
      'Answers are quoted from official public-health pages, which may be out of date. For your own health, talk to a doctor or pharmacist. In an emergency, call your local emergency number.',
    close: 'Close',
    title: 'Trusted health answers.',
    subtitle:
      'Ask a health question in English or French. MedSource quotes the exact passage from official public-health publications, with its source. No match, no answer: it never guesses.',
    ask: 'Ask in English or French…',
    askLabel: 'Your health question',
    send: 'Ask',
    suggestions: 'You could ask',
    from: 'Sources we search',
    basedOn: (n: number, s: number) =>
      `Based on ${n} ${n === 1 ? 'passage' : 'passages'} from ${s} official ${s === 1 ? 'source' : 'sources'}`,
    jump: 'Go to passage',
    full: 'Read the full passage',
    less: 'Show less',
    official: 'Open the official page',
    copy: 'Copy the quote',
    copied: 'Quote copied',
    copyError: 'Copy is not available here. Select the text to copy it.',
    searching: 'Looking through the official sources…',
    refusal: 'We couldn’t find this in the official sources',
    refusalText: 'MedSource only answers when an official passage clearly matches your question.',
    hint: 'Try rephrasing, or ask about paracetamol, hand washing, flu vaccination or blood pressure.',
    error: 'The search didn’t go through.',
    errorHint: 'Check your connection and try again.',
    retry: 'Try again',
    index: 'Search index',
    chunks: 'passages indexed',
    model: 'Embedding model',
    filters: 'Relevance rules',
    minimum: 'Minimum match score',
    margin: 'Margin from the best match',
    pending: 'Connecting…',
    unavailable: 'Index unavailable',
    sourceError: 'Could not load the source list.',
    refresh: 'Refresh',
    themeLight: 'Switch to light mode',
    themeDark: 'Switch to dark mode',
    topK: 'Passages',
    footer: 'Quoted, not generated. Every passage links to its official source.',
    library: 'Official sources',
    libraryText: 'Public-health publications, downloaded from their original websites.',
    you: 'Your question',
    skip: 'Skip to main content',
    page: 'page',
    fragment: 'part',
    sourceFilter: 'Sources',
    allSources: 'All languages',
    langNames: { fr: 'French', en: 'English' },
    langBadge: { fr: 'French source', en: 'English source' },
    match: { close: 'Close match', good: 'Good match', partial: 'Partial match' },
    score: 'similarity',
    endorsement:
      'CDC and FDA excerpts are quoted unchanged from cdc.gov and fda.gov, where they are available at no charge. This does not imply endorsement by the U.S. Government, HHS, CDC or FDA.',
    language: 'Language',
    settings: 'Settings',
    eyebrow: 'Official sources only · English & French',
    titleAccent: 'Quoted from official sources.',
    mSources: 'official sources',
    mPassages: 'indexed passages',
    mEval: (h: number, n: number) => `hit@4 on our eval (${h}/${n})`,
    mLatency: 'API response time',
    live: 'live',
    liveTitle: 'Read from the running service when this page loaded',
    metricsLabel: 'Key figures',
    principlesLabel: 'How MedSource works',
    p1: 'Quoted, never generated',
    p1Text:
      'Every answer is an exact passage from an official publication, with its page and a link.',
    p2: 'Refuses when unsure',
    p2Text: 'If no passage matches clearly, MedSource says so instead of guessing.',
    p3: 'English & French',
    p3Text: 'Ask in either language; passages are found across both corpora.',
  },
  fr: {
    tagline: 'Des réponses santé tirées de sources officielles',
    sources: 'Sources',
    newChat: 'Nouvelle question',
    disclaimerTitle: 'Information, pas un avis médical.',
    disclaimer:
      'Les réponses sont des extraits de pages officielles de santé publique, qui peuvent être datées. Pour votre santé, parlez-en à un médecin ou à un pharmacien. En cas d’urgence, appelez le 15 ou le 112.',
    close: 'Fermer',
    title: 'Des réponses santé fiables.',
    subtitle:
      'Posez une question de santé en français ou en anglais. MedSource cite le passage exact de publications officielles de santé publique, avec sa source. Aucun passage pertinent, aucune réponse : il ne devine jamais.',
    ask: 'Posez votre question en français ou en anglais…',
    askLabel: 'Votre question de santé',
    send: 'Envoyer',
    suggestions: 'Vous pouvez demander',
    from: 'Sources consultées',
    basedOn: (n: number, s: number) =>
      `D’après ${n} ${n === 1 ? 'passage' : 'passages'} de ${s} ${s === 1 ? 'source officielle' : 'sources officielles'}`,
    jump: 'Aller au passage',
    full: 'Lire le passage complet',
    less: 'Réduire',
    official: 'Ouvrir la page officielle',
    copy: 'Copier la citation',
    copied: 'Citation copiée',
    copyError: 'Copie indisponible ici. Sélectionnez le texte pour le copier.',
    searching: 'Recherche dans les sources officielles…',
    refusal: 'Nous n’avons pas trouvé cela dans les sources officielles',
    refusalText:
      'MedSource ne répond que lorsqu’un passage officiel correspond clairement à votre question.',
    hint: 'Reformulez, ou posez une question sur le paracétamol, le lavage des mains, la vaccination contre la grippe ou la tension artérielle.',
    error: 'La recherche n’a pas abouti.',
    errorHint: 'Vérifiez votre connexion puis réessayez.',
    retry: 'Réessayer',
    index: 'Index de recherche',
    chunks: 'passages indexés',
    model: 'Modèle d’embedding',
    filters: 'Règles de pertinence',
    minimum: 'Score minimum',
    margin: 'Écart maximal au meilleur passage',
    pending: 'Connexion…',
    unavailable: 'Index indisponible',
    sourceError: 'Impossible de charger la liste des sources.',
    refresh: 'Actualiser',
    themeLight: 'Passer en mode clair',
    themeDark: 'Passer en mode sombre',
    topK: 'Passages',
    footer: 'Cité, pas généré. Chaque passage renvoie à sa source officielle.',
    library: 'Sources officielles',
    libraryText: 'Publications de santé publique, téléchargées depuis leur site d’origine.',
    you: 'Votre question',
    skip: 'Aller au contenu principal',
    page: 'page',
    fragment: 'partie',
    sourceFilter: 'Sources',
    allSources: 'Toutes les langues',
    langNames: { fr: 'Français', en: 'Anglais' },
    langBadge: { fr: 'Source en français', en: 'Source en anglais' },
    match: { close: 'Très pertinent', good: 'Pertinent', partial: 'Partiellement pertinent' },
    score: 'similarité',
    endorsement:
      'Les extraits CDC et FDA sont repris tels quels depuis cdc.gov et fda.gov, où ils sont disponibles gratuitement. Cela n’implique aucune approbation par le gouvernement américain, le HHS, les CDC ou la FDA.',
    language: 'Langue',
    settings: 'Réglages',
    eyebrow: 'Sources officielles uniquement · français & anglais',
    titleAccent: 'Citées depuis les sources officielles.',
    mSources: 'sources officielles',
    mPassages: 'passages indexés',
    mEval: (h: number, n: number) => `hit@4 sur notre évaluation (${h}/${n})`,
    mLatency: 'Temps de réponse de l’API',
    live: 'en direct',
    liveTitle: 'Lu depuis le service au chargement de la page',
    metricsLabel: 'Chiffres clés',
    principlesLabel: 'Comment fonctionne MedSource',
    p1: 'Cité, jamais généré',
    p1Text:
      'Chaque réponse est un passage exact d’une publication officielle, avec sa page et son lien.',
    p2: 'Refuse en cas de doute',
    p2Text: 'Si aucun passage ne correspond clairement, MedSource le dit au lieu de deviner.',
    p3: 'Français & anglais',
    p3Text:
      'Posez la question dans l’une ou l’autre langue ; les passages sont cherchés dans les deux corpus.',
  },
}
export type Labels = (typeof copy)['en']

/** Browser language decides the default UI language; English is the fallback. */
export function browserLanguage(): Language {
  const list = typeof navigator === 'undefined' ? [] : navigator.languages || [navigator.language]
  for (const l of list) {
    const code = (l || '').slice(0, 2).toLowerCase()
    if (code === 'fr' || code === 'en') return code
  }
  return 'en'
}

/** Similarity scores are not probabilities: show a plain-language match level instead. */
export function matchLevel(score: number): 'close' | 'good' | 'partial' {
  return score >= 0.75 ? 'close' : score >= 0.65 ? 'good' : 'partial'
}

export const questions: Record<Language, string[]> = {
  en: [
    'What is the maximum daily dose of acetaminophen for adults?',
    'When should I use hand sanitizer instead of soap and water?',
    'Who should get a flu vaccine every season?',
    'Which blood pressure reading is stage 2 hypertension?',
  ],
  fr: [
    'Quelle est la dose maximale de paracétamol par jour ?',
    'Combien de temps faut-il se laver les mains ?',
    'Qui doit se faire vacciner contre la grippe ?',
    'Quelle est la cible tensionnelle à 6 mois ?',
  ],
}

export const publisherShort: Record<string, string> = {
  'has_sfhta_fiche_memo_hta_adulte_2016.pdf': 'HAS · SFHTA',
  'ansm_paracetamol.txt': 'ANSM',
  'santefr_lavage_des_mains.txt': 'Santé.fr',
  'vaccination_info_service_grippe.txt': 'Vaccination Info Service',
  'fda_acetaminophen.txt': 'FDA',
  'fda_dont_overuse_acetaminophen.txt': 'FDA',
  'cdc_handwashing.txt': 'CDC',
  'cdc_flu_vaccine_key_facts.txt': 'CDC',
  'cdc_high_blood_pressure.txt': 'CDC',
}
export function shortName(source: string, publisher?: string | null): string {
  const file = source.split('/').pop() || source
  return publisherShort[file] || (publisher || file).split(' (')[0]!
}
