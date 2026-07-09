import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "")

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
VOYAGE_EMBED_MODEL = os.environ.get("VOYAGE_EMBED_MODEL", "voyage-4-lite")

TOP_K = int(os.environ.get("TOP_K", "5"))

DOCS_DIR = BASE_DIR / os.environ.get("DOCS_DIR", "docs")
CHROMA_DB_DIR = BASE_DIR / os.environ.get("CHROMA_DB_DIR", ".chroma_db")

COLLECTION_NAME = "infra_docs"
MAX_CHUNK_CHARS = 1500
CHUNK_OVERLAP_CHARS = 150

SERVERS_FILE = BASE_DIR / "servers.yaml"
SSH_CONNECT_TIMEOUT = 8
SSH_COMMAND_TIMEOUT = 15
