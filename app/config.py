from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Firebase
    firebase_project_id: str = "your-project-id"
    firebase_private_key: str = "your-private-key"
    firebase_client_email: str = "your-client-email"
    
    # App
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
