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

# An honest bot user agent: some publishers (e.g. cdc.gov) reject browser-like
# user agents that do not behave like browsers.
USER_AGENT = "healthcare-rag/0.2 (+https://github.com/MourabitElBachir/healthcare-rag; portfolio demo)"


@dataclass(frozen=True)
class Source:
    filename: str
    title: str
    publisher: str
    url: str
    kind: str  # "pdf" or "html"
    lang: str = "fr"  # language of the document: "fr" or "en"


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
    # English sources: U.S. federal agencies (public domain, see data/public/SOURCES.md).
    Source("fda_acetaminophen.txt", "Acetaminophen (Safe Use of OTC Pain Relievers and Fever Reducers)",
           "U.S. Food and Drug Administration (FDA)",
           "https://www.fda.gov/drugs/safe-use-over-counter-pain-relievers-and-fever-reducers/"
           "acetaminophen", "html", "en"),
    Source("fda_dont_overuse_acetaminophen.txt", "Don't Overuse Acetaminophen (Consumer Update)",
           "U.S. Food and Drug Administration (FDA)",
           "https://www.fda.gov/consumers/consumer-updates/dont-overuse-acetaminophen", "html", "en"),
    Source("cdc_handwashing.txt", "About Handwashing (Clean Hands)",
           "U.S. Centers for Disease Control and Prevention (CDC)",
           "https://www.cdc.gov/clean-hands/about/index.html", "html", "en"),
    Source("cdc_flu_vaccine_key_facts.txt", "Key Facts About Seasonal Flu Vaccine",
           "U.S. Centers for Disease Control and Prevention (CDC)",
           "https://www.cdc.gov/flu/vaccines/keyfacts.html", "html", "en"),
    Source("cdc_high_blood_pressure.txt", "About High Blood Pressure",
           "U.S. Centers for Disease Control and Prevention (CDC)",
           "https://www.cdc.gov/high-blood-pressure/about/index.html", "html", "en"),
)

SOURCE_BY_FILE = {s.filename: s for s in SOURCES}


def source_language(filename: str) -> str | None:
    """Language ("fr"/"en") of a registered source, by file name or path."""
    source = SOURCE_BY_FILE.get(Path(filename).name)
    return source.lang if source else None


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
