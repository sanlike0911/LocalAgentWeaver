"""
アプリケーション設定
"""

import os
from pathlib import Path

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
VECTOR_DB_DIR = PROJECT_ROOT / "vector_db"

# 必要なディレクトリを作成
for directory in [DATA_DIR, LOGS_DIR, VECTOR_DB_DIR]:
    directory.mkdir(exist_ok=True)

# Ollama設定
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"
OLLAMA_TEMPERATURE = 0.7

# データベース設定
DATABASE_PATH = DATA_DIR / "projects.db"

# サポートされるファイル形式
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md']

# ログ設定
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'