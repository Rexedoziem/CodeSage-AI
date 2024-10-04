import os
from pathlib import Path
import torch

# Project root directory
ROOT_DIR = Path(__file__).resolve().parent

# Model configurations
MODEL_NAME = "llama2-7b"
MODEL_PATH = os.path.join(ROOT_DIR, "models", MODEL_NAME)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Language server configurations
SERVER_HOST = "localhost"
SERVER_PORT = 8080

# VSCode extension configurations
EXTENSION_NAME = "advanced-python-copilot"

# Database configurations
DB_PATH = os.path.join(ROOT_DIR, "data", "copilot.db")

# Retrieval configurations
RETRIEVAL_TOP_K = 5
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Caching configurations
CACHE_SIZE = 1000
CACHE_EXPIRATION = 3600  # in seconds

# Telemetry configurations
TELEMETRY_ENABLED = True
TELEMETRY_ENDPOINT = "https://telemetry.example.com/log"

# Security configurations
MAX_REQUESTS_PER_MINUTE = 60
TOKEN_EXPIRATION = 3600  # in seconds

# Logging configurations
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(ROOT_DIR, "logs", "copilot.log")