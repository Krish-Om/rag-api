from typing import List, Dict, Any
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
import json
from pathlib import Path


class OptimizedEmbeddingService:
    """
    Pure ONNX Runtime embedding service with minimal dependencies.
    No PyTorch, no transformers - just onnxruntime + tokenizers.

    Requires pre-converted ONNX model. Run scripts/convert_to_onnx.py first.
    """

    def __init__(self, model_dir: str = "onnx_models/all-MiniLM-L6-v2") -> None:
        # Model configuration
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.dimension = 384
        self.max_length = 512

        # Paths for model files
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "model.onnx"
        self.tokenizer_path = self.model_dir / "tokenizer.json"
        self.config_path = self.model_dir / "config.json"

        # Verify model exists
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found at {self.model_path}. "
                f"Run 'python scripts/convert_to_onnx.py' first to convert the model."
            )

        # Load model and tokenizer
        self._setup_model()

        print(
            f"✅ Optimized ONNX Embedding service initialized with {self.dimension}D vectors"
        )
        print(f"📦 Memory footprint: ~100MB (vs ~1GB+ with PyTorch)")

    def _setup_model(self) -> None:
        """Load pre-converted ONNX model and tokenizer"""

        # Load the ONNX model
        print(f"📥 Loading ONNX model from {self.model_path}")

        # Configure ONNX Runtime for CPU inference
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

        # Create inference session
        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=sess_options,
            providers=["CPUExecutionProvider"],
        )

        # Load tokenizer
        print(f"📥 Loading tokenizer from {self.tokenizer_path}")
        self.tokenizer = Tokenizer.from_file(str(self.tokenizer_path))

        # Load model config
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = json.load(f)
        else:
            # Default config
            self.config = {"max_seq_length": self.max_length, "do_lower_case": True}

    def _mean_pooling(
        self, token_embeddings: np.ndarray, attention_mask: np.ndarray
    ) -> np.ndarray:
        """Apply mean pooling using pure NumPy (no PyTorch)"""
        # Expand attention mask
        input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
        input_mask_expanded = np.broadcast_to(
            input_mask_expanded, token_embeddings.shape
        ).astype(np.float32)

        # Apply mean pooling
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)

        return sum_embeddings / sum_mask

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalize embeddings using pure NumPy"""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-12, a_max=None)  # Avoid division by zero
        return embeddings / norms

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using pure ONNX runtime"""
        if not texts:
            return []

        # Tokenize texts
        encodings = self.tokenizer.encode_batch(texts)

        # Prepare inputs
        input_ids = []
        attention_masks = []
        token_type_ids = []

        for encoding in encodings:
            # Truncate to max length
            ids = encoding.ids[: self.max_length]
            attention = encoding.attention_mask[: self.max_length]
            type_ids = encoding.type_ids[: self.max_length]

            # Pad to max length
            if len(ids) < self.max_length:
                padding_length = self.max_length - len(ids)
                ids.extend([0] * padding_length)  # 0 is typically the pad token
                attention.extend([0] * padding_length)
                type_ids.extend([0] * padding_length)

            input_ids.append(ids)
            attention_masks.append(attention)
            token_type_ids.append(type_ids)

        # Convert to numpy arrays
        input_ids = np.array(input_ids, dtype=np.int64)
        attention_masks = np.array(attention_masks, dtype=np.int64)
        token_type_ids = np.array(token_type_ids, dtype=np.int64)

        # Run inference
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_masks,
            "token_type_ids": token_type_ids,
        }

        outputs = self.session.run(None, inputs)
        token_embeddings = outputs[0]  # Shape: (batch_size, seq_len, hidden_size)

        # Apply mean pooling
        sentence_embeddings = self._mean_pooling(token_embeddings, attention_masks)

        # Normalize embeddings
        sentence_embeddings = self._normalize(sentence_embeddings)

        return sentence_embeddings.tolist()

    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_length": self.max_length,
            "runtime": "ONNX Runtime (CPU)",
            "memory_efficient": True,
            "dependencies": ["onnxruntime", "tokenizers", "numpy"],
        }
