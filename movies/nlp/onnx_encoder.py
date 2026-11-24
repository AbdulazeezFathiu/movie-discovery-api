
from functools import lru_cache
from pathlib import Path

import numpy as np

from django.conf import settings


MODEL_DIR = Path(settings.BASE_DIR) / "onnx_model"
MODEL_PATH = MODEL_DIR / "onnx" / "model.onnx"
TOKENIZER_PATH = MODEL_DIR / "tokenizer.json"

EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_onnx_tokenizer():
    """
    Load the pretrained tokenizer without Transformers
    or PyTorch.
    """
    from tokenizers import Tokenizer

    if not TOKENIZER_PATH.is_file():
        raise FileNotFoundError(
            f"ONNX tokenizer not found: {TOKENIZER_PATH}"
        )

    tokenizer = Tokenizer.from_file(
        str(TOKENIZER_PATH)
    )

    tokenizer.enable_truncation(max_length=256)

    return tokenizer


@lru_cache(maxsize=1)
def get_onnx_session():
    """
    Load ONNX Runtime once per Django worker.
    """
    import onnxruntime as ort

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"ONNX model not found: {MODEL_PATH}"
        )

    options = ort.SessionOptions()

    # Limit CPU threads to reduce resource usage
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    options.execution_mode = (
        ort.ExecutionMode.ORT_SEQUENTIAL
    )

    # Start with conservative memory settings
    options.enable_cpu_mem_arena = False

    session = ort.InferenceSession(
        str(MODEL_PATH),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )

    return session


def encode_query_onnx(query):
    """
    Convert text into a normalized 384-dimensional
    sentence embedding.

    Uses the same model family, mean pooling and
    L2 normalization as our stored movie embeddings.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must not be empty.")

    tokenizer = get_onnx_tokenizer()
    session = get_onnx_session()

    encoded = tokenizer.encode(query)

    input_ids = np.asarray(
        [encoded.ids],
        dtype=np.int64,
    )

    attention_mask = np.asarray(
        [encoded.attention_mask],
        dtype=np.int64,
    )

    token_type_ids = np.asarray(
        [encoded.type_ids],
        dtype=np.int64,
    )

    available_inputs = {
        item.name for item in session.get_inputs()
    }

    inputs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "token_type_ids": token_type_ids,
    }

    inputs = {
        name: value
        for name, value in inputs.items()
        if name in available_inputs
    }

    outputs = session.run(None, inputs)

    # Transformer output: [batch, tokens, hidden_size]
    token_embeddings = np.asarray(
        outputs[0],
        dtype=np.float32,
    )

    if (
        token_embeddings.ndim != 3
        or token_embeddings.shape[-1] != EMBEDDING_DIMENSION
    ):
        raise ValueError(
            "Unexpected ONNX model output shape: "
            f"{token_embeddings.shape}"
        )

    # Mask padding tokens during mean pooling
    mask = attention_mask[:, :, None].astype(
        np.float32
    )

    summed_embeddings = np.sum(
        token_embeddings * mask,
        axis=1,
    )

    token_counts = np.maximum(
        np.sum(mask, axis=1),
        1e-9,
    )

    sentence_embedding = (
        summed_embeddings / token_counts
    )[0]

    # L2 normalization
    norm = np.linalg.norm(sentence_embedding)

    if not np.isfinite(norm) or norm == 0:
        raise ValueError(
            "Invalid ONNX embedding generated."
        )

    sentence_embedding = (
        sentence_embedding / norm
    )

    return sentence_embedding.astype(np.float32)
