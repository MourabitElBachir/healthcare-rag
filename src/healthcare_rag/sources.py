"""Download the official public documents listed in data/public/SOURCES.md.

Third-party documents are NOT committed to the repository (their reuse terms
belong to each publisher). This module fetches them from their original URLs
into an ignored folder (default: data/public/raw). PDFs are saved unchanged;
HTML pages are reduced to their main text with trafilatura and prefixed with a
short provenance header.
"""
from __future__ import annotations

import datetime as _dt
import urllib.request
from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) healthcare-rag/0.1 (+portfolio demo)"


@dataclass(frozen=True)
class Source:
    filename: str
    title: str
    publisher: str
    url: str
    kind: str  # "pdf" or "html"


SOURCES: tuple[Source, ...] = (
    Source("has_sfhta_fiche_memo_hta_adulte_2016.pdf",
           "Fiche mémo - Prise en charge de l'hypertension artérielle de l'adulte (2016)",
           "Haute Autorité de Santé (HAS) & Société Française d'Hypertension Artérielle (SFHTA)",
           "https://sfhta.eu/wp-content/uploads/2021/09/"
           "SFHTA_HAS_Fiche-Memo-HTA_PRISE-EN-CHARGE-HTA-ESSENTIELLE.pdf", "pdf"),
    Source("ansm_paracetamol.txt", "Dossier thématique - Le paracétamol",
           "ANSM (Agence nationale de sécurité du médicament et des produits de santé)",
           "https://ansm.sante.fr/dossiers-thematiques/medicaments-de-la-douleur/le-paracetamol",
           "html"),
    Source("santefr_lavage_des_mains.txt",
           "Pourquoi, quand et comment bien se laver les mains ?",
           "Santé.fr - Service Public d'Information en Santé",
           "https://www.sante.fr/gestes-barrieres/pourquoi-quand-et-comment-bien-se-laver-les-mains",
           "html"),
    Source("vaccination_info_service_grippe.txt", "Grippe (Les maladies et leurs vaccins)",
           "Vaccination Info Service (Santé publique France)",
           "https://vaccination-info-service.fr/Les-maladies-et-leurs-vaccins/Grippe", "html"),
)


def _download(url: str, timeout: float = 60) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def html_to_text(html: str) -> str:
    """Extract the main readable text of an HTML page (same settings as the demo)."""
    import trafilatura
    return trafilatura.extract(html, include_comments=False, include_tables=True,
                               favor_precision=True) or ""


def fetch_source(source: Source, out_dir: Path) -> Path:
    """Download one source; raise ValueError if the response is not real content."""
    data, content_type = _download(source.url)
    target = out_dir / source.filename
    if source.kind == "pdf":
        if not data.startswith(b"%PDF"):
            raise ValueError(f"{source.url} did not return a PDF ({content_type})")
        target.write_bytes(data)
        return target
    text = html_to_text(data.decode("utf-8", errors="replace"))
    if len(text) < 500:
        raise ValueError(f"{source.url}: extracted text too short ({len(text)} chars)")
    header = (f"SOURCE: {source.title}\nÉDITEUR / PUBLISHER: {source.publisher}\n"
              f"URL: {source.url}\nRÉCUPÉRÉ LE / RETRIEVED: {_dt.date.today().isoformat()} "
              "(texte extrait du HTML / text extracted from HTML)\n\n")
    target.write_text(header + text + "\n", encoding="utf-8")
    return target


def fetch_all(out_dir: str | Path = "data/public/raw") -> list[tuple[Source, Path | None, str]]:
    """Fetch every source; returns (source, path or None, status message)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for source in SOURCES:
        try:
            path = fetch_source(source, out)
            results.append((source, path, f"ok ({path.stat().st_size} bytes)"))
        except Exception as exc:  # report and continue with the other sources
            results.append((source, None, f"FAILED: {exc}"))
    return results
