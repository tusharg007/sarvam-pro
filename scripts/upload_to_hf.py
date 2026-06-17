"""Upload dataset to HuggingFace Hub. Requires env vars: HF_TOKEN, HF_USERNAME."""
import os, sys

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_USERNAME = os.environ.get("HF_USERNAME", "")
REPO_NAME = "indian-english-hindi-tts-sarvam"
HF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hf_dataset")

if not HF_TOKEN or not HF_USERNAME:
    print("ERROR: Set HF_TOKEN and HF_USERNAME environment variables.")
    print("  $env:HF_TOKEN = 'hf_xxx'")
    print("  $env:HF_USERNAME = 'your_username'")
    sys.exit(1)

from huggingface_hub import HfApi, create_repo

repo_id = f"{HF_USERNAME}/{REPO_NAME}"
api = HfApi(token=HF_TOKEN)
create_repo(repo_id=repo_id, repo_type="dataset", token=HF_TOKEN, exist_ok=True, private=False)
print(f"Uploading to {repo_id}...")
api.upload_folder(folder_path=HF_DIR, repo_id=repo_id, repo_type="dataset",
                  commit_message="Upload Indian EN+HI TTS dataset")
print(f"DONE: https://huggingface.co/datasets/{repo_id}")
