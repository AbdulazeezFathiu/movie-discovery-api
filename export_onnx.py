
from pathlib import Path

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

OUTPUT_DIR = Path("onnx_model")


def export_model():
    print("Loading model for ONNX export...")

    model = SentenceTransformer(
        MODEL_NAME,
        backend="onnx",
        device="cpu",
        model_kwargs={
            "export": True,
            "provider": "CPUExecutionProvider",
        },
    )

    print("Testing ONNX model...")

    embedding = model.encode_query(
        "Movies about space exploration",
        normalize_embeddings=True,
    )

    print("Embedding dimensions:", len(embedding))

    if len(embedding) != 384:
        raise ValueError(
            "Expected a 384-dimensional embedding."
        )

    print("Saving ONNX model...")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model.save_pretrained(str(OUTPUT_DIR))

    onnx_files = list(
        OUTPUT_DIR.rglob("*.onnx")
    )

    if not onnx_files:
        raise RuntimeError(
            "No ONNX model file was exported."
        )

    print("ONNX files:")
    for file in onnx_files:
        print(file)

    print("ONNX export completed successfully!")


if __name__ == "__main__":
    export_model()
