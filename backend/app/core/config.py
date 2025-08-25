from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/localagentweaver"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # LLM Providers
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LM_STUDIO_BASE_URL: str = "http://localhost:1234"
    
    # Embeddings / Vector DB
    EMBEDDING_PROVIDER: str = "ollama"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    LANCE_DB_DIR: str = "data/lancedb"
    
    # Node Parser / Chunking Settings
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 128
    PARAGRAPH_SEPARATOR: str = "\n\n\n"
    
    # File Upload
    UPLOAD_MAX_SIZE_MB: int = 30
    UPLOAD_DIR: str = "uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()