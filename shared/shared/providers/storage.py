import shutil
import os
from pathlib import Path
from typing import Dict, Type
from fastapi import UploadFile
from shared.interfaces import StorageProvider
from shared.config import Config, config as global_config

# Registry
_STORAGE_REGISTRY: Dict[str, Type[StorageProvider]] = {}

def register_storage_strategy(name: str):
    def decorator(cls):
        _STORAGE_REGISTRY[name] = cls
        return cls
    return decorator

@register_storage_strategy("local")
class LocalStorageProvider(StorageProvider):
    def __init__(self, upload_dir: str = "uploads"):
        # We can pull defaults from config in the Factory if preferred, 
        # or pass them during initialization.
        self.upload_dir = upload_dir

    def save_file(self, file: UploadFile) -> str:
        filename = file.filename or "unknown"
        os.makedirs(self.upload_dir, exist_ok=True)
        file_location = Path(self.upload_dir) / filename

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer) #

        return str(file_location)

@register_storage_strategy("s3")
class S3StorageProvider(StorageProvider):
    def __init__(self, bucket_name: str):
        self.bucket = bucket_name

    def save_file(self, file: UploadFile) -> str:
        # Placeholder for actual S3 logic
        return f"s3://{self.bucket}/{file.filename}" #

class StorageFactory:
    """
    Factory to retrieve Storage Providers.
    """
    @staticmethod
    def get_storage_provider(settings: Config = global_config) -> StorageProvider:
        # Assuming there is a STORAGE_PROVIDER field in settings, default to local
        provider = getattr(settings, "STORAGE_PROVIDER", "local").lower()
        
        strategy_cls = _STORAGE_REGISTRY.get(provider)
        if not strategy_cls:
            raise ValueError(f"Unknown Storage Provider: {provider}")
            
        # Here we handle specific initialization logic based on the provider type
        if provider == "local":
            return strategy_cls(upload_dir=getattr(settings, "UPLOAD_DIR", "uploads")) # type: ignore
        elif provider == "s3":
            return strategy_cls(bucket_name=getattr(settings, "S3_BUCKET_NAME", "my-bucket")) # type: ignore
            
        return strategy_cls()