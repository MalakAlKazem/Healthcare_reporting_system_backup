"""
Configuration settings for Python service
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # Paths
    UPLOAD_DIR: str = "../storage/uploads"
    CHARTS_DIR: str = "../storage/charts"
    TEMP_DIR: str = "../storage/temp"
    TEMPLATES_DIR: str = "../shared/templates"
    
    # AI Settings (Phase 2)
    ENABLE_AI: bool = False
    MODEL_PATH: Optional[str] = "./models/flan-t5-base"
    MODEL_NAME: str = "google/flan-t5-base"
    
    # Processing
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".xlsx", ".xls"]
    
    # Excel Chart Export
    USE_EXCEL_EXPORT: bool = True
    POWERSHELL_SCRIPT: str = "../scripts/export-charts.ps1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()