import sys
sys.path.append(r"C:/Users/dell/OneDrive/Desktop/ai-interview-agent-master")

try:
    from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
    print("API key:", (OPENAI_API_KEY[:4] + "..." if OPENAI_API_KEY else "<empty>"))
    print("Base URL:", OPENAI_BASE_URL if OPENAI_BASE_URL else "<empty>")
    print("Model:", OPENAI_MODEL)
except Exception as e:
    print("Import error:", e)
    raise
