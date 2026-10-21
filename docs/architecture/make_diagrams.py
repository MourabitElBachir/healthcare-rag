"""Generate the architecture diagrams (SVG) for the README.

    python docs/architecture/make_diagrams.py            # writes *.svg
    python docs/architecture/make_diagrams.py --png      # + *.png (needs playwright + Chrome)

Hand-crafted SVG (no external fonts or icons) so it renders identically on GitHub.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent
FONT = "Inter, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', 'JetBrains Mono', 'DejaVu Sans Mono', Consolas, monospace"

C = {  # dark theme palette
    "bg0": "#070b12", "bg1": "#0b1220", "panel": "#0f1a2b", "panel2": "#111f33",
    "border": "#22324a", "text": "#e6edf6", "muted": "#8fa1b8", "dim": "#5d6f86",
    "teal": "#2dd4bf", "cyan": "#38bdf8", "indigo": "#818cf8", "amber": "#fbbf24",
    "violet": "#c084fc", "rose": "#fb7185", "green": "#34d399", "azure": "#3b9cff",
}


class Svg:
    def __init__(self, w: int, h: int):
        self.w, self.h, self.parts = w, h, []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size=14, color=None, weight=400, anchor="start", mono=False,
             italic=False, opacity=1.0):
        self.add(f'<text x="{x}" y="{y}" font-family="{MONO if mono else FONT}" '
                 f'font-size="{size}" font-weight="{weight}" fill="{color or C["text"]}" '
                 f'text-anchor="{anchor}" opacity="{opacity}"'
                 f'{" font-style=\"italic\"" if italic else ""}>{escape(s)}</text>')

    def group(self, x, y, w, h, label, color, sub=None, dashed=False):
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{color}" '
                 f'fill-opacity="0.045" stroke="{color}" stroke-opacity="0.55" '
                 f'stroke-width="1.4"{dash}/>')
        self.add(f'<rect x="{x + 18}" y="{y - 13}" width="{len(label) * 7.9 + 26}" height="26" '
                 f'rx="13" fill="{C["bg1"]}" stroke="{color}" stroke-opacity="0.7"/>')
        self.text(x + 31, y + 5, label, 13, color, 650, mono=True)
        if sub:
            self.text(x + w - 18, y + 24, sub, 12, C["muted"], 400, "end", mono=True)

    def box(self, x, y, w, h, title, lines=(), color=None, tag=None, dashed=False,
            title_size=16):
        color = color or C["teal"]
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
                 f'fill="url(#card)" stroke="{C["border"]}" stroke-width="1.2"{dash}/>')
        self.add(f'<rect x="{x}" y="{y + 14}" width="3.5" height="{h - 28}" rx="1.75" '
                 f'fill="{color}"/>')
        self.add(f'<circle cx="{x + 22}" cy="{y + 25}" r="5" fill="{color}"/>')
        self.add(f'<circle cx="{x + 22}" cy="{y + 25}" r="10" fill="{color}" opacity="0.18"/>')
        self.text(x + 38, y + 31, title, title_size, C["text"], 650)
        tw = len(tag) * 7.2 + 16 if tag else 0
        if tag and 38 + len(title) * title_size * 0.58 + tw + 24 <= w:
            self.add(f'<rect x="{x + w - tw - 12}" y="{y + 14}" width="{tw}" height="22" rx="11" '
                     f'fill="{color}" fill-opacity="0.14" stroke="{color}" stroke-opacity="0.5"/>')
            self.text(x + w - tw / 2 - 12, y + 29, tag, 11.5, color, 600, "middle", mono=True)
        for i, line in enumerate(lines):
            self.text(x + 20, y + 56 + i * 19, line, 13, C["muted"])

    def arrow(self, pts, color, label=None, lx=None, ly=None, dashed=False, anchor="middle",
              width=2.0, label_color=None, both=False):
        d = "M " + " L ".join(f"{px} {py}" for px, py in pts)
        start = ""
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        marker = {C["teal"]: "t", C["amber"]: "a", C["violet"]: "v", C["cyan"]: "c",
                  C["indigo"]: "i", C["azure"]: "z", C["green"]: "g", C["muted"]: "m"}[color]
        if both:
            start = f' marker-start="url(#ah-{marker})"'
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                 f'stroke-linejoin="round"{dash} marker-end="url(#ah-{marker})"'
                 f'{start} opacity="0.95"/>')
        if label:
            self.text(lx, ly, label, 12.5, label_color or C["muted"], 500, anchor)

    def badge(self, x, y, s, color):
        self.add(f'<circle cx="{x}" cy="{y}" r="13" fill="{C["bg0"]}" stroke="{color}" '
                 f'stroke-width="2"/>')
        self.text(x, y + 4.5, s, 13, color, 750, "middle", mono=True)

    def pill(self, x, y, s, color, size=13):
        w = len(s) * size * 0.62 + 28
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{size + 15}" rx="{(size + 15) / 2}" '
                 f'fill="{color}" fill-opacity="0.13" stroke="{color}" stroke-opacity="0.65"/>')
        self.text(x + w / 2, y + size + 3, s, size, color, 650, "middle", mono=True)
        return w

    def render(self) -> str:
        markers = "".join(
            f'<marker id="ah-{k}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" '
            f'fill="{v}"/></marker>'
            for k, v in {"t": C["teal"], "a": C["amber"], "v": C["violet"], "c": C["cyan"],
                         "i": C["indigo"], "z": C["azure"], "g": C["green"],
                         "m": C["muted"]}.items())
        defs = f'''<defs>
<linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{C["panel2"]}"/><stop offset="1" stop-color="{C["panel"]}"/>
</linearGradient>
<radialGradient id="glow1" cx="0.12" cy="0.08" r="0.6">
  <stop offset="0" stop-color="#14b8a6" stop-opacity="0.16"/><stop offset="1" stop-color="#14b8a6" stop-opacity="0"/>
</radialGradient>
<radialGradient id="glow2" cx="0.92" cy="0.95" r="0.6">
  <stop offset="0" stop-color="#6366f1" stop-opacity="0.16"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/>
</radialGradient>
<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
  <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#ffffff" stroke-opacity="0.025"/>
</pattern>{markers}</defs>'''
        bg = (f'<rect width="{self.w}" height="{self.h}" fill="{C["bg0"]}"/>'
              f'<rect width="{self.w}" height="{self.h}" fill="url(#grid)"/>'
              f'<rect width="{self.w}" height="{self.h}" fill="url(#glow1)"/>'
              f'<rect width="{self.w}" height="{self.h}" fill="url(#glow2)"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">{defs}{bg}{"".join(self.parts)}</svg>\n')


def header(s: Svg, title: str, subtitle: str, pill: tuple[str, str] | None = None):
    s.add(f'<rect x="40" y="34" width="44" height="44" rx="12" fill="{C["teal"]}" fill-opacity="0.16" '
          f'stroke="{C["teal"]}" stroke-opacity="0.6"/>')
    s.add(f'<path d="M50 57 h7 l4 -9 l6 18 l4 -9 h7" fill="none" stroke="{C["teal"]}" '
          f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    s.text(100, 56, title, 26, C["text"], 700)
    s.text(100, 80, subtitle, 14.5, C["muted"])
    if pill:
        text, color = pill
        w = len(text) * 13 * 0.62 + 28
        s.pill(s.w - 40 - w, 40, text, color)


def legend(s: Svg, y: int, items: list[tuple[str, str, bool]]):
    x = 40
    for label, color, dashed in items:
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        s.add(f'<line x1="{x}" y1="{y}" x2="{x + 34}" y2="{y}" stroke="{color}" '
              f'stroke-width="2.4"{dash}/>')
        s.text(x + 44, y + 4.5, label, 13, C["muted"], 500)
        x += 44 + len(label) * 7.3 + 34


# --------------------------------------------------------------------------- A
def current() -> Svg:
    s = Svg(1720, 900)
    header(s, "MedSource RAG — current architecture",
           "Deployed: one Docker container on Render free · local ONNX embeddings · zero paid API",
           ("LIVE · medsource-rag.onrender.com", C["green"]))

    # client side
    s.group(30, 140, 270, 390, "CLIENT", C["cyan"])
    s.box(50, 180, 230, 120, "Browser", ["desktop · mobile", "FR / EN · dark / light"], C["cyan"])
    s.box(50, 360, 230, 150, "React SPA", ["React 19 · Vite · TS", "Tailwind v4 · motion",
                                           "citation cards · refusal"], C["cyan"])

    # Render container
    s.group(330, 140, 930, 680, "RENDER FREE WEB SERVICE · DOCKER", C["teal"],
            "512 MB RAM · 0.1 CPU · sleeps when idle · $PORT")
    s.box(355, 180, 880, 104, "FastAPI + uvicorn", [
        "serves the built SPA (static files)  +  GET /api/health · GET /api/sources · POST /api/ask",
        "model + index loaded once per process  ·  ~300 MB peak RAM  ·  warm answer ≈ 0.2 s round-trip"],
        C["teal"], tag="api.py")

    y = 352
    s.text(600, y - 14, "QUERY PIPELINE · PER REQUEST", 12, C["teal"], 650, mono=True)
    row = [(355, "Embedder", ["MiniLM-L12 multilingual", "ONNX Runtime, no torch",
                              "SentencePiece · mmap"], C["indigo"]),
           (582, "Chroma", ["persistent local index", "cosine · 384 dims",
                            "top-k nearest chunks"], C["violet"]),
           (809, "Relevance filter", ["score ≥ 0.55 (floor)", "≥ best − 0.08 (margin)",
                                      "≤ 2 per source", "else → refusal"], C["amber"]),
           (1036, "Extractive answer", ["no LLM, no generation", "exact passages with",
                                        "source · page · score"], C["green"])]
    for x, t, lines, col in row:
        s.box(x, y, 200, 140, t, lines, col)

    y2 = 580
    s.text(357, y2 - 14, "INGESTION · RUNS AT DOCKER BUILD", 12, C["amber"], 650, mono=True)
    row2 = [(355, "fetch", ["9 official URLs (EN+FR)", "PDF kept as-is", "HTML → main text"]),
            (582, "clean + chunk", ["PDF de-hyphenation", "800 chars · 150 overlap",
                                    "source / page / chunk id"]),
            (809, "embed", ["same ONNX model", "batches of 16", "L2-normalised"]),
            (1036, "index", ["upsert into Chroma", "135 chunks today", "baked into the image"])]
    for x, t, lines in row2:
        s.box(x, y2, 200, 140, t, lines, C["amber"])

    # right column
    s.box(1310, 160, 380, 124, "GitHub · master", ["MIT code · tests · eval set",
                                                   "push → Render auto-deploy (Blueprint)"],
          C["violet"], tag="CI/CD")
    s.group(1310, 340, 380, 480, "OFFICIAL SOURCES · EN + FR", C["amber"])
    srcs = [("CDC (U.S.)", ["hand washing · flu vaccine", "high blood pressure"], "EN"),
            ("FDA (U.S.)", ["acetaminophen · 2 pages"], "EN"),
            ("HAS · SFHTA · ANSM", ["hypertension memo (PDF)", "paracetamol"], "FR"),
            ("Santé.fr · Vaccination Info", ["hand washing", "flu vaccination"], "FR")]
    for i, (t, sub, lang) in enumerate(srcs):
        s.box(1335, 372 + i * 108, 330, 90, t, sub, C["amber"], tag=lang, title_size=15)

    # request flow
    t, c = C["teal"], C["cyan"]
    s.arrow([(280, 220), (355, 220)], c)
    s.badge(317, 220, "1", c)
    s.text(317, 200, "GET /", 12, c, 600, "middle")
    s.arrow([(165, 300), (165, 360)], c)
    s.text(175, 335, "loads & runs", 12, C["muted"])
    s.arrow([(280, 440), (315, 440), (315, 262), (355, 262)], t, both=True)
    s.badge(315, 350, "2", t)
    s.text(50, 552, "2 · POST /api/ask ⇄ cited JSON", 12.5, t, 600, "start")
    s.arrow([(455, 284), (455, 352)], t)
    s.badge(455, 318, "3", t)
    s.text(472, 312, "embed question", 12, t, 500)
    s.arrow([(555, 422), (582, 422)], t)
    s.badge(568, 396, "4", t)
    s.arrow([(782, 422), (809, 422)], t)
    s.badge(795, 396, "5", t)
    s.arrow([(1009, 422), (1036, 422)], t)
    s.arrow([(1136, 352), (1136, 284)], t)
    s.badge(1136, 318, "6", t)
    s.text(1121, 312, "citations or refusal", 12, t, 500, "end")

    # ingestion flow
    a = C["amber"]
    s.arrow([(1335, 750), (1290, 750), (1290, 775), (455, 775), (455, 720)], a)
    s.badge(870, 775, "A", a)
    s.text(890, 797, "HTTPS download during docker build", 12, a, 500)
    for i, x in enumerate((555, 782, 1009)):
        s.arrow([(x, 650), (x + 27, 650)], a)
        s.badge(x + 13, 624, "BCD"[i], a)
    s.arrow([(1136, 580), (1136, 536), (682, 536), (682, 492)], a, dashed=True)
    s.text(909, 529, "same index served at runtime", 12, a, 500, "middle")

    # deploy
    s.arrow([(1310, 222), (1262, 222)], C["violet"], dashed=True)
    s.text(1286, 206, "deploy", 12, C["violet"], 600, "middle")

    legend(s, 862, [("request flow 1–6", C["teal"], False),
                    ("ingestion flow A–D (docker build)", C["amber"], False),
                    ("deploy on push", C["violet"], True),
                    ("not medical advice · retrieval only, no generation", C["muted"], True)])
    return s


# --------------------------------------------------------------------------- B
def target() -> Svg:
    s = Svg(1900, 1170)
    header(s, "MedSource RAG — target architecture on Azure",
           "Large-scale design: managed search, grounded generation, scheduled ingestion, eval-gated CI/CD",
           ("TARGET DESIGN · NOT DEPLOYED", C["amber"]))
    A = C["azure"]

    s.box(40, 170, 230, 132, "Users", ["clinicians · patients", "web · mobile"], C["cyan"])
    s.group(320, 140, 560, 330, "EDGE & IDENTITY", A)
    s.box(345, 175, 250, 128, "Static Web Apps", ["React SPA · global CDN", "preview env per PR"], A)
    s.box(615, 175, 240, 128, "Entra ID", ["sign-in (External ID)", "JWT validated by the API"],
          C["indigo"], tag="auth")
    s.box(345, 325, 510, 118, "API Management (optional)",
          ["rate limits · quotas · API keys · OpenAPI portal", "response cache · request logging"],
          A, tag="gateway", dashed=True)

    s.group(930, 140, 440, 330, "COMPUTE", C["teal"])
    s.box(955, 175, 390, 268, "Container Apps · API", [
        "FastAPI image from Container Registry",
        "autoscale 0 → N replicas (HTTP / KEDA)",
        "retrieve → relevance filter → generate",
        "citation check: each sentence must map",
        "to a retrieved passage, else refuse",
        "managed identity to Search, OpenAI, KV"], C["teal"], tag="api")

    s.group(1520, 140, 350, 520, "AI & RETRIEVAL", C["violet"])
    s.box(1545, 175, 300, 150, "Azure OpenAI", ["embeddings (text-embedding-3)",
                                                "chat model: answer grounded", "on cited passages only"],
          C["violet"], tag="LLM")
    s.box(1545, 345, 300, 150, "Azure AI Search", ["hybrid: vector + BM25", "semantic ranker · filters",
                                                   "(source, date, audience)"], C["violet"])
    s.box(1545, 515, 300, 120, "alt: Postgres + pgvector", ["Azure Database for PostgreSQL",
                                                            "or Supabase (cheaper start)"],
          C["violet"], dashed=True)

    s.group(40, 560, 1440, 330, "INGESTION · SCHEDULED (DATABRICKS WORKFLOWS OR AZURE FUNCTIONS)",
            C["amber"])
    ing = [(65, 230, "Scheduler", ["daily / weekly trigger", "Workflows or Functions", "timer"]),
           (325, 250, "Crawler", ["CDC · FDA · HAS · ANSM", "Santé.fr · Santé publique France",
                                  "sitemaps / RSS · robots.txt"]),
           (605, 250, "ADLS Gen2 / Blob", ["bronze: raw PDF / HTML", "silver: text + chunks",
                                           "versioned, licence kept"]),
           (885, 270, "Parse · chunk · embed", ["Databricks job (Spark)", "or Functions for small loads",
                                                "embeds via Azure OpenAI"]),
           (1185, 270, "Index upsert", ["push to AI Search", "delete stale chunks",
                                        "doc version metadata"])]
    for x, w, t, lines in ing:
        s.box(x, 600, w, 150, t, lines, C["amber"])
    s.box(325, 778, 1130, 92, "Official public-health publishers (internet)",
          ["new recommendations, safety alerts, patient pages — provenance & reuse terms kept per document"],
          C["dim"], title_size=15)

    s.group(40, 940, 1830, 170, "SECURITY · OBSERVABILITY · DELIVERY", C["green"])
    s.box(65, 975, 300, 112, "Key Vault", ["secrets & keys", "read via managed identity"],
          C["green"], tag="secrets")
    s.box(395, 975, 380, 112, "Application Insights · Monitor", ["traces, latency, refusal rate",
                                                                 "token usage & cost alerts"],
          C["green"])
    s.box(805, 975, 1040, 112, "GitHub Actions CI/CD", [
        "tests → eval gate (hit@k, refusal accuracy, faithfulness on a golden set; block if below baseline)",
        "→ build image → push to ACR → new Container Apps revision · Static Web Apps deploy · index rebuild job"],
        C["green"], tag="pipeline")

    t = C["teal"]
    s.arrow([(270, 220), (345, 220)], t)
    s.badge(307, 220, "1", t)
    s.arrow([(270, 270), (295, 270), (295, 500), (600, 500), (600, 443)], t)
    s.badge(295, 400, "2", t)
    s.text(320, 522, "POST /api/ask (+ token)", 12.5, t, 500)
    s.arrow([(855, 384), (955, 384)], t)
    s.badge(905, 384, "3", t)
    s.arrow([(1345, 420), (1545, 420)], t)
    s.badge(1445, 420, "4", t)
    s.text(1445, 404, "embed + hybrid top-k", 12, t, 500, "middle")
    s.arrow([(1345, 250), (1545, 250)], t)
    s.badge(1445, 250, "5", t)
    s.text(1445, 234, "grounded generation", 12, t, 500, "middle")
    s.arrow([(1150, 175), (1150, 112), (155, 112), (155, 170)], t, dashed=True)
    s.badge(650, 112, "6", t)
    s.text(672, 106, "answer + verified citations (or refusal)", 12.5, t, 500)

    a = C["amber"]
    for x, lab in ((295, "A"), (575, "B"), (855, "C"), (1155, "D")):
        s.arrow([(x, 675), (x + 30, 675)], a)
        s.badge(x + 15, 650, lab, a)
    s.arrow([(450, 778), (450, 750)], a)
    s.arrow([(1455, 675), (1500, 675), (1500, 470), (1545, 470)], a)
    s.badge(1500, 580, "E", a)

    g = C["green"]
    s.arrow([(215, 975), (215, 890)], g, dashed=True)
    s.text(225, 912, "secrets", 12, g, 500)
    s.arrow([(585, 975), (585, 890)], g, dashed=True)
    s.text(595, 912, "telemetry", 12, g, 500)

    legend(s, 1140, [("request flow 1–6", C["teal"], False),
                     ("ingestion flow A–E", C["amber"], False),
                     ("ops / delivery", C["green"], True),
                     ("optional component", C["muted"], True)])
    return s


def main() -> None:
    files = {"current-architecture": current(), "azure-target-architecture": target()}
    for name, svg in files.items():
        (OUT / f"{name}.svg").write_text(svg.render(), encoding="utf-8")
        print("wrote", OUT / f"{name}.svg")
    if "--png" in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path="/usr/bin/google-chrome",
                                        args=["--no-sandbox"])
            for name, svg in files.items():
                page = browser.new_page(viewport={"width": svg.w, "height": svg.h},
                                        device_scale_factor=2)
                page.goto((OUT / f"{name}.svg").as_uri())
                page.screenshot(path=str(OUT / f"{name}.png"))
                print("wrote", OUT / f"{name}.png")
            browser.close()


if __name__ == "__main__":
    main()
