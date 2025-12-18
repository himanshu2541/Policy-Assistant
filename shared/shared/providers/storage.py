import shutil
import os
from pathlib import Path
from fastapi import UploadFile
# import boto3
from shared.interfaces import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir

    def save_file(self, file: UploadFile) -> str:
        filename = file.filename or "unknown"
        os.makedirs(self.upload_dir, exist_ok=True)
        file_location = Path(self.upload_dir) / filename

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(file_location)


class S3StorageProvider(StorageProvider):
    def __init__(self, bucket_name: str):
        self.bucket = bucket_name

    def save_file(self, file: UploadFile) -> str:
        # s3_client.upload_fileobj(...)
        return f"s3://{self.bucket}/{file.filename}"