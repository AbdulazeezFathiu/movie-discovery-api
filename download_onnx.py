
from huggingface_hub import snapshot_download

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("Downloading pre-exported ONNX model...")

model_path = snapshot_download(
    repo_id=MODEL_NAME,
    local_dir="onnx_model",
    allow_patterns=[
        "onnx/model.onnx",
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
        "modules.json",
        "sentence_bert_config.json",
        "config_sentence_transformers.json",
        "1_Pooling/config.json",
    ],
)

print("Download completed!")
print("Model saved to:", model_path)
