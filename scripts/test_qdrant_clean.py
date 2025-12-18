import subprocess
import os

env = {
    "QDRANT_LOCAL_PATH": r"C:\Users\Rau\Desktop\CasareRPA\.qdrant",
    "COLLECTION_NAME": "casare_codebase",
    "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "PATH": os.environ.get("PATH", ""),
}

cmd = [
    r"C:\Users\Rau\AppData\Local\Programs\Python\Python313\Scripts\mcp-server-qdrant.exe"
]

print(f"Running with env: {env}")
result = subprocess.run(cmd, env=env, capture_output=True, text=True)
print(f"Return code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")
