from typing import List, Dict, Any
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
import json
import os
from pathlib import Path
import urllib.request
import warnings


class OptimizedEmbeddingService:
    """
    Pure ONNX Runtime embedding service with minimal dependencies.
    No PyTorch, no transformers - just onnxruntime + tokenizers.
    """

    def __init__(self) -> None:
        # Model configuration
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.dimension = 384
        self.max_length = 512

        # Paths for local model storage
        self.model_dir = Path("./onnx_models/all-MiniLM-L6-v2")
        self.model_path = self.model_dir / "model.onnx"
        self.tokenizer_path = self.model_dir / "tokenizer.json"
        self.config_path = self.model_dir / "config.json"

        # Ensure model directory exists
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Load or download model components
        self._setup_model()

        print(
            f"✅ Optimized ONNX Embedding service initialized with {self.dimension}D vectors"
        )
        print(f"📦 Memory footprint: ~100MB (vs ~1GB+ with PyTorch)")

    def _setup_model(self) -> None:
        """Setup ONNX model and tokenizer with minimal dependencies"""

        # If model doesn't exist locally, we need to convert it
        if not self.model_path.exists():
            print("🔄 Converting model to ONNX format (one-time setup)...")
            self._convert_to_onnx()

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

    def _convert_to_onnx(self) -> None:
        """
        Convert HuggingFace model to ONNX format.
        This is a one-time conversion step that requires transformers.
        """
        try:
            # Import only for conversion (this will be removed in production)
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            from transformers import AutoTokenizer

            print(
                "🔄 Converting model to ONNX (requires transformers - will be removed after conversion)..."
            )

            # Load and convert model
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = ORTModelForFeatureExtraction.from_pretrained(
                self.model_name, export=True, provider="CPUExecutionProvider"
            )

            # Save converted model
            model.save_pretrained(self.model_dir)
            tokenizer.save_pretrained(self.model_dir)

            # Save tokenizer in fast tokenizers format
            tokenizer_fast = tokenizer
            if hasattr(tokenizer_fast, "backend_tokenizer"):
                tokenizer_fast.backend_tokenizer.save(str(self.tokenizer_path))

            # Create config
            config = {
                "model_type": "sentence-transformers",
                "max_seq_length": self.max_length,
                "do_lower_case": True,
                "dimension": self.dimension,
            }

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)

            print(f"✅ Model converted and saved to {self.model_dir}")

        except ImportError:
            raise ImportError(
                "Model conversion requires 'optimum[onnxruntime]' and 'transformers'. "
                "Run: pip install optimum[onnxruntime] transformers"
            )

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

        for encoding in encodings:
            # Truncate to max length
            ids = encoding.ids[: self.max_length]
            attention = encoding.attention_mask[: self.max_length]

            # Pad to max length
            if len(ids) < self.max_length:
                padding_length = self.max_length - len(ids)
                ids.extend([0] * padding_length)  # 0 is typically the pad token
                attention.extend([0] * padding_length)

            input_ids.append(ids)
            attention_masks.append(attention)

        # Convert to numpy arrays
        input_ids = np.array(input_ids, dtype=np.int64)
        attention_masks = np.array(attention_masks, dtype=np.int64)

        # Run inference
        inputs = {"input_ids": input_ids, "attention_mask": attention_masks}

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
