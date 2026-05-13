"""HuggingFace Spaces entry point.

Architecture Improvement #3: thin wrapper that launches the Streamlit
app in a HF Spaces environment.  HF Spaces serves the app on port 7860.

Deploy to HuggingFace Spaces
-----------------------------
1.  Create a new Space at https://huggingface.co/new-space
2.  Choose SDK = Docker
3.  Push this repo (or just this spaces/ folder) to the Space repo
4.  Set the following Secrets in Space Settings:
      HF_TOKEN        - your HuggingFace token (for Mistral inference)
      MONGODB_URI     - your MongoDB Atlas connection string
      OPENAI_API_KEY  - (optional) if you want GPT fallback
5.  The Space will build using spaces/Dockerfile.spaces and start on port 7860

Local test
----------
    cd spaces && docker build -f Dockerfile.spaces -t interview-agent-spaces . && docker run -p 7860:7860 interview-agent-spaces
"""

import os
import subprocess
import sys


def main() -> None:
    """Launch the Streamlit app on port 7860 for HF Spaces."""
    app_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend",
        "app.py",
    )
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        app_path,
        "--server.port", "7860",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
