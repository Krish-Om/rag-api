from typing import List

import numpy as np
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer
import torch


class EmbeddingService:
    def __init__(self) -> None:
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"Loading ONNX model: {model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load ONNX model (converts automatically if needed)
        self.model = ORTModelForFeatureExtraction.from_pretrained(
            model_name,
            export=True,  # Auto-convert to ONNX if not available
            provider="CPUExecutionProvider"  # CPU optimized
        )
        
        self.dimension = 384  # all-MiniLM-L6-v2 output dimension
        print(f"ONNX Embedding service initialized with {self.dimension}D vectors")
        
    def _mean_pooling(self, model_output, attention_mask):
        """Apply mean pooling to get sentence embeddings"""
        token_embeddings = model_output[0]  # First element contains token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        if not texts:
            return []
        
        # Tokenize texts
        encoded_input = self.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            max_length=512,
            return_tensors='pt'
        )
        
        # Generate embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)
            
        # Apply mean pooling
        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Normalize embeddings
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        
        return sentence_embeddings.numpy().tolist()

    def generate_single_embeddings(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []


