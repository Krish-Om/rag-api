#!/usr/bin/env python3
"""
One-time model conversion script.
This converts sentence-transformers/all-MiniLM-L6-v2 to pure ONNX format.

Run this once with full dependencies, then switch to minimal requirements.
"""

import os
import sys
from pathlib import Path


def convert_model_to_onnx():
    """Convert HuggingFace model to ONNX format for production use"""

    try:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        from transformers import AutoTokenizer
        import json

        print("🚀 Starting model conversion to ONNX...")

        # Model configuration
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        output_dir = Path("./onnx_models/all-MiniLM-L6-v2")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"📥 Loading model: {model_name}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load and convert model to ONNX
        print("🔄 Converting to ONNX format...")
        model = ORTModelForFeatureExtraction.from_pretrained(
            model_name, export=True, provider="CPUExecutionProvider"
        )

        # Save converted model and tokenizer
        print(f"💾 Saving to {output_dir}")
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        # Save fast tokenizer format
        tokenizer_path = output_dir / "tokenizer.json"
        if hasattr(tokenizer, "backend_tokenizer"):
            tokenizer.backend_tokenizer.save(str(tokenizer_path))
            print(f"✅ Fast tokenizer saved to {tokenizer_path}")

        # Create model configuration
        config = {
            "model_type": "sentence-transformers",
            "model_name": model_name,
            "max_seq_length": 512,
            "dimension": 384,
            "do_lower_case": True,
            "converted_by": "ONNX conversion script",
            "runtime": "onnxruntime",
            "providers": ["CPUExecutionProvider"],
        }

        config_path = output_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ Configuration saved to {config_path}")

        # Verify the conversion
        model_onnx_path = output_dir / "model.onnx"
        if model_onnx_path.exists():
            file_size = model_onnx_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ ONNX model created: {model_onnx_path} ({file_size:.1f} MB)")
        else:
            print("❌ ONNX model file not found!")
            return False

        # Test the converted model
        print("🧪 Testing converted model...")
        try:
            import onnxruntime as ort

            session = ort.InferenceSession(
                str(model_onnx_path), providers=["CPUExecutionProvider"]
            )
            print("✅ ONNX model loads successfully!")

            # Show model inputs/outputs
            inputs = session.get_inputs()
            outputs = session.get_outputs()

            print("📊 Model Information:")
            print(f"  Inputs: {[inp.name for inp in inputs]}")
            print(f"  Outputs: {[out.name for out in outputs]}")
            print(f"  Input shape: {inputs[0].shape}")
            print(f"  Output shape: {outputs[0].shape}")

        except Exception as e:
            print(f"❌ Error testing ONNX model: {e}")
            return False

        print("\n🎉 Conversion completed successfully!")
        print("\n📋 Next steps:")
        print(
            "1. Switch to minimal requirements: pip install -r requirements.minimal.txt"
        )
        print("2. Update your embedding service to use OptimizedEmbeddingService")
        print("3. Remove torch, transformers, and CUDA packages")
        print("4. Enjoy ~1GB+ smaller Docker images! 🚀")

        return True

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install conversion dependencies:")
        print("pip install optimum[onnxruntime] transformers torch")
        return False
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ONNX Model Conversion Script")
    print("=" * 60)

    # Check if model already exists
    model_path = Path("./onnx_models/all-MiniLM-L6-v2/model.onnx")
    if model_path.exists():
        print(f"⚠️  Model already exists at {model_path}")
        response = input("Do you want to reconvert? (y/N): ").lower()
        if response != "y":
            print("✋ Conversion cancelled")
            sys.exit(0)

    # Run conversion
    success = convert_model_to_onnx()

    if success:
        print("\n✅ Conversion completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)
