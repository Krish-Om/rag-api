from typing import List

import numpy as np
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer
import torch
import os
from pathlib import Path
import warnings


class EmbeddingService:
    def __init__(self) -> None:
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

        # Suppress ALL warnings during model loading
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            print(f"Loading ONNX model: {model_name}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Check if we have a local ONNX model and it has the required files
            local_onnx_path = Path(f"./sentence-transformers_all-MiniLM-L6-v2_onnx")

            if local_onnx_path.exists() and (local_onnx_path / "model.onnx").exists():
                # Load existing ONNX model without re-conversion
                print("Loading existing ONNX model...")
                self.model = ORTModelForFeatureExtraction.from_pretrained(
                    local_onnx_path, provider="CPUExecutionProvider"
                )
            else:
                # First time: convert to ONNX but don't export again if it's already converted
                print("Setting up ONNX model...")
                try:
                    # Try loading without export first (in case it's already in cache)
                    self.model = ORTModelForFeatureExtraction.from_pretrained(
                        model_name,
                        export=False,  # Don't force export
                        provider="CPUExecutionProvider",
                    )
                except:
                    # Only export if absolutely necessary
                    self.model = ORTModelForFeatureExtraction.from_pretrained(
                        model_name, export=True, provider="CPUExecutionProvider"
                    )

                # Save for next time
                if local_onnx_path.exists():
                    import shutil

                    shutil.rmtree(local_onnx_path)
                self.model.save_pretrained(local_onnx_path)
                print(f"ONNX model saved to {local_onnx_path}")

        self.dimension = 384  # all-MiniLM-L6-v2 output dimension
        print(f"ONNX Embedding service initialized with {self.dimension}D vectors")

    def _mean_pooling(self, model_output, attention_mask):
        """Apply mean pooling to get sentence embeddings"""
        token_embeddings = model_output[0]  # First element contains token embeddings
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        if not texts:
            return []

        # Tokenize texts
        encoded_input = self.tokenizer(
            texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )

        # Generate embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)

        # Apply mean pooling
        sentence_embeddings = self._mean_pooling(
            model_output, encoded_input["attention_mask"]
        )

        # Normalize embeddings
        sentence_embeddings = torch.nn.functional.normalize(
            sentence_embeddings, p=2, dim=1
        )

        return sentence_embeddings.numpy().tolist()

    def generate_single_embeddings(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
