"""
Download Small LLM Model for Flood Warning System
Recommended: TinyLlama-1.1B-Chat (669MB quantized)
Alternative: Qwen2-0.5B-Instruct (352MB quantized)
"""

import os
import requests
from tqdm import tqdm
from pathlib import Path

# Model options ranked by quality vs size
MODELS = {
    "tinyllama": {
        "name": "TinyLlama-1.1B-Chat-v1.0-GGUF",
        "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "669 MB",
        "quality": "Good for simple tasks",
        "recommended": True
    },
    "qwen": {
        "name": "Qwen2-0.5B-Instruct-GGUF",
        "file": "qwen2-0_5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0_5b-instruct-q4_k_m.gguf",
        "size": "352 MB",
        "quality": "Smallest, decent quality",
        "recommended": False
    },
    "phi2": {
        "name": "Phi-2-GGUF",
        "file": "phi-2.Q4_K_M.gguf",
        "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "size": "1.6 GB",
        "quality": "Best quality, larger size",
        "recommended": False
    }
}

def download_file(url: str, destination: str):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as file, tqdm(
        desc=os.path.basename(destination),
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def download_model(model_key: str = "tinyllama"):
    """Download and setup LLM model"""
    
    if model_key not in MODELS:
        print(f"❌ Unknown model: {model_key}")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return False
    
    model_info = MODELS[model_key]
    
    # Create models directory
    models_dir = Path("models/llm")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    destination = models_dir / model_info["file"]
    
    # Check if already downloaded and valid size (>100MB)
    if destination.exists():
        size_mb = destination.stat().st_size / (1024**2)
        if size_mb < 100:
            print(f"⚠️ Found existing model but small ({size_mb:.1f} MB). Re-downloading...")
            destination.unlink()
        else:
            print(f"✅ Model already exists: {destination}")
            print(f"   Size: {size_mb:.1f} MB")
            return True
    
    print(f"📥 Downloading {model_info['name']}...")
    print(f"   Size: {model_info['size']}")
    print(f"   Quality: {model_info['quality']}")
    print(f"   URL: {model_info['url']}")
    print()
    
    try:
        download_file(model_info['url'], str(destination))
        print()
        print(f"✅ Model downloaded successfully!")
        print(f"   Location: {destination}")
        print(f"   Size: {destination.stat().st_size / (1024**2):.1f} MB")
        print()
        print("🔧 Next steps:")
        print("   1. Update .env:")
        print(f"      LLM_ENABLED=true")
        print(f"      LLM_PROVIDER=local")
        print(f"      LLM_MODEL_FILE={model_info['file']}")
        print("   2. Install llama-cpp-python: pip install llama-cpp-python")
        print("   3. Restart your backend")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        if destination.exists():
            destination.unlink()
        return False

def show_models():
    """Display available models"""
    print("\n📦 Available Models:\n")
    for key, info in MODELS.items():
        marker = "⭐ RECOMMENDED" if info['recommended'] else "  "
        print(f"{marker} {key}")
        print(f"   Name: {info['name']}")
        print(f"   Size: {info['size']}")
        print(f"   Quality: {info['quality']}")
        print()

if __name__ == "__main__":
    import sys
    
    print("🌊 Rainly - LLM Model Downloader")
    print("=" * 50)
    
    # Check for environment variable or CLI arg first
    env_model = os.getenv("MODEL_TO_DOWNLOAD", "").lower()
    if len(sys.argv) > 1:
        model_key = sys.argv[1]
    elif env_model and env_model in MODELS:
        model_key = env_model
        print(f"🤖 Auto-selected model from environment: {model_key}")
    else:
        # Default for automated deployment if no interaction possible
        # Or ask user if interactive
        if sys.stdin.isatty():
            show_models()
            print("Which model would you like to download?")
            print("Enter: tinyllama, qwen (recommended for speed/size), or phi2")
            model_key = input("> ").strip().lower() or "qwen"
        else:
            print("🤖 Non-interactive mode detected. Defaulting to 'qwen'.")
            model_key = "qwen"
    
    print()
    success = download_model(model_key)
    
    if success:
        print(f"\n✅ Setup complete! {MODELS[model_key]['name']} is ready to use.")
    else:
        print("\n❌ Setup failed. Please try again or check your internet connection.")
        sys.exit(1)
