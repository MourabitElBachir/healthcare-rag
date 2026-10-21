"""Streamlit demo UI.  Run:  streamlit run src/healthcare_rag/app.py

The embedding model and the Chroma store are loaded once per server process
(st.cache_resource), so only the first question pays the model-loading cost.
"""
from __future__ import annotations

import os

import streamlit as st

from healthcare_rag.config import Config
from healthcare_rag.pipeline import answer_question, load_components
from healthcare_rag.sources import SOURCES

st.set_page_config(page_title="healthcare-rag", page_icon="🩺", layout="wide")


@st.cache_resource(show_spinner="Chargement du modèle d'embeddings et de l'index…")
def get_components(embedder: str = "st"):
    encoder, store = load_components(embedder)
    encoder.embed(["warm-up"])  # load the model now, not on the first question
    return encoder, store


config = Config.from_env()

with st.sidebar:
    st.warning("**Pas un avis médical / Not medical advice.**\n\n"
               "Démo portfolio : les réponses sont des extraits de documents publics "
               "officiels, qui peuvent être datés. Consultez un professionnel de santé.")
    st.subheader("Sources officielles")
    for source in SOURCES:
        st.markdown(f"- [{source.title}]({source.url})  \n  _{source.publisher}_")
    st.caption(f"Filtre : score ≥ {config.min_score} et ≥ meilleur − {config.score_margin}")

st.title("🩺 healthcare-rag")
st.caption("Réponses uniquement à partir de sources officielles, avec citation exacte "
           "(fichier, page, score). Recherche locale, sans LLM, sans API payante.")

question = st.text_input("Votre question", value=st.query_params.get("q", ""),
                         placeholder="Combien de temps faut-il se laver les mains ?")
k = st.slider("Nombre de passages candidats (top-k)", min_value=1, max_value=10,
              value=config.top_k)

if question.strip():
    encoder, store = get_components(os.getenv("HEALTHCARE_RAG_EMBEDDER", "st"))
    answer = answer_question(question, encoder, store, k=k, config=config)
    if not answer.citations:
        st.error("Je ne peux pas répondre à partir des sources disponibles. / "
                 "I cannot answer from the available source passages.")
    else:
        st.success(f"{len(answer.citations)} passage(s) cité(s)")
        for i, passage in enumerate(answer.citations, 1):
            with st.container(border=True):
                st.markdown(f"**[{i}] {passage.source}** — page {passage.page}, "
                            f"fragment {passage.chunk_index} · score **{passage.score:.2f}**")
                st.text(passage.text)
