from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Document Intelligence System"
    ENV: str = "development"
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "doc_ai"
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    
    # JWT settings
    SECRET_KEY: str  
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
