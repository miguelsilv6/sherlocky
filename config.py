import os
from dotenv import load_dotenv

load_dotenv()

# Configuration variables loaded from the .env file
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
