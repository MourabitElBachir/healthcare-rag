"""Explicit embedding providers; hashing never downloads a model."""
from hashlib import sha256
from math import sqrt
import re
from typing import Protocol


class Embedder(Protocol):
    @property
    def identity(self) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    """Load sentence-transformers only when embeddings are requested."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    @property
    def identity(self) -> str:
        return f"st:{self.model_name}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model.encode(texts, normalize_embeddings=True).tolist()


class OnnxEmbedder:
    """ONNX embeddings with onnxruntime + SentencePiece (no PyTorch).

    Memory-lean version of ``paraphrase-multilingual-MiniLM-L12-v2`` for small
    instances (e.g. 512 MB RAM):

    * model: Xenova ONNX export, ``fp32`` (default, same vectors as sentence-transformers)
      or ``int8`` (``HEALTHCARE_RAG_ONNX_VARIANT=int8``, slightly lower quality), converted
      once to ONNX *external data* so onnxruntime memory-maps the weights instead of
      copying them: only the embedding rows actually used are paged in;
    * tokenizer: the original XLM-R ``sentencepiece.bpe.model`` with the fairseq id
      mapping, which yields exactly the same token ids as the Hugging Face
      ``tokenizer.json`` but uses ~190 MB less RAM;
    * mean pooling + L2 normalisation, as in sentence-transformers.

    Files go to ``HEALTHCARE_RAG_MODEL_DIR`` (default ``~/.cache/healthcare-rag``);
    ``HEALTHCARE_RAG_THREADS`` sets the onnxruntime thread count.
    """

    ONNX_REPO = "Xenova/paraphrase-multilingual-MiniLM-L12-v2"
    ONNX_REVISION = "2c4055b12046f11709e9df2c122e59ffbdc2f900"
    ONNX_FILES = {"fp32": "onnx/model.onnx", "int8": "onnx/model_quantized.onnx"}
    SPM_REPO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    SPM_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
    SPM_FILE = "sentencepiece.bpe.model"
    MAX_TOKENS = 128  # max_seq_length of the original sentence-transformers model
    BOS, PAD, EOS, UNK = 0, 1, 2, 3  # XLM-R special token ids

    def __init__(self, model_name: str, variant: str | None = None):
        import os
        self.model_name = model_name
        self.variant = variant or os.getenv("HEALTHCARE_RAG_ONNX_VARIANT", "fp32")
        if self.variant not in self.ONNX_FILES:
            raise ValueError(f"ONNX variant must be one of {sorted(self.ONNX_FILES)}")
        self._session = None
        self._spm = None

    @property
    def identity(self) -> str:
        return f"onnx-{self.variant}:{self.ONNX_REPO}@{self.ONNX_REVISION[:7]}"

    @staticmethod
    def model_dir():
        import os
        from pathlib import Path
        default = Path.home() / ".cache" / "healthcare-rag"
        return Path(os.getenv("HEALTHCARE_RAG_MODEL_DIR", default))

    def prepare(self):
        """Download the files and write the external-data ONNX model (idempotent)."""
        import shutil
        from huggingface_hub import hf_hub_download
        target = self.model_dir() / f"onnx-{self.variant}-{self.ONNX_REVISION[:7]}"
        model_path, spm_path = target / "model.onnx", target / self.SPM_FILE
        if not (model_path.is_file() and (target / "model.onnx.data").is_file()):
            import onnx  # only needed once, for the conversion
            target.mkdir(parents=True, exist_ok=True)
            source = hf_hub_download(self.ONNX_REPO, self.ONNX_FILES[self.variant],
                                     revision=self.ONNX_REVISION)
            onnx.save_model(onnx.load(source), str(model_path), save_as_external_data=True,
                            all_tensors_to_one_file=True, location="model.onnx.data",
                            size_threshold=1024)
        if not spm_path.is_file():
            shutil.copyfile(hf_hub_download(self.SPM_REPO, self.SPM_FILE,
                                            revision=self.SPM_REVISION), spm_path)
        return model_path, spm_path

    def _load(self) -> None:
        import os
        import onnxruntime as ort
        import sentencepiece as spm
        model_path, spm_path = self.prepare()
        options = ort.SessionOptions()
        options.enable_cpu_mem_arena = False  # lower resident memory on small instances
        threads = os.getenv("HEALTHCARE_RAG_THREADS")
        if threads:
            options.intra_op_num_threads = int(threads)
            options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(str(model_path), options,
                                             providers=["CPUExecutionProvider"])
        self._spm = spm.SentencePieceProcessor(model_file=str(spm_path))

    def token_ids(self, text: str) -> list[int]:
        """XLM-R ids: <s> + (spm id + 1, spm <unk> -> 3) + </s>, truncated to 128."""
        if self._spm is None:
            self._load()
        pieces = [i + 1 if i != 0 else self.UNK for i in self._spm.encode(text)]
        return [self.BOS] + pieces[:self.MAX_TOKENS - 2] + [self.EOS]

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._session is None:
            self._load()
        import numpy as np
        vectors: list[list[float]] = []
        input_names = {i.name for i in self._session.get_inputs()}
        for start in range(0, len(texts), 16):
            encoded = [self.token_ids(t) for t in texts[start:start + 16]]
            width = max(len(e) for e in encoded)
            ids = np.full((len(encoded), width), self.PAD, dtype=np.int64)
            mask = np.zeros((len(encoded), width), dtype=np.int64)
            for row, e in enumerate(encoded):
                ids[row, :len(e)] = e
                mask[row, :len(e)] = 1
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in input_names:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = self._session.run(None, feeds)[0]  # (batch, tokens, 384)
            weights = mask[..., None].astype(np.float32)
            pooled = (hidden * weights).sum(axis=1) / np.clip(weights.sum(axis=1), 1e-9, None)
            pooled /= np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)
            vectors.extend(pooled.tolist())
        return vectors


EMBEDDERS = ("onnx", "st", "hashing")


def default_embedder() -> str:
    """Embedder used when none is given: HEALTHCARE_RAG_EMBEDDER or onnx."""
    import os
    return os.getenv("HEALTHCARE_RAG_EMBEDDER", "onnx")


class HashingEmbedder:
    """Tiny normalized signed bag-of-words baseline; no semantic understanding."""

    def __init__(self, dimensions: int = 512):
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    @property
    def identity(self) -> str:
        return f"hashing-v1:{self.dimensions}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"\w+", text.casefold()):
                digest = sha256(token.encode()).digest()
                vector[int.from_bytes(digest[:8], "big") % self.dimensions] += (
                    1.0 if digest[8] % 2 else -1.0)
            norm = sqrt(sum(value * value for value in vector)) or 1.0
            result.append([value / norm for value in vector])
        return result
