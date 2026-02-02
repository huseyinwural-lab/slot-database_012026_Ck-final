import os
import io
import boto3
from typing import List, BinaryIO
from config import settings

class StorageClient:
    """Abstract storage client for audit archival."""
    
    def put_object(self, key: str, data: BinaryIO) -> None:
        raise NotImplementedError

    def get_object(self, key: str) -> bytes:
        raise NotImplementedError

    def list_objects(self, prefix: str) -> List[str]:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError

class LocalFileSystemStorage(StorageClient):
    """Local filesystem implementation for dev/test environments."""
    
    def __init__(self, root_path: str):
        self.root_path = root_path
        os.makedirs(self.root_path, exist_ok=True)

    def put_object(self, key: str, data: BinaryIO) -> None:
        full_path = os.path.join(self.root_path, key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data.read())

    def get_object(self, key: str) -> bytes:
        full_path = os.path.join(self.root_path, key)
        with open(full_path, "rb") as f:
            return f.read()

    def list_objects(self, prefix: str) -> List[str]:
        # Walk directory
        results = []
        full_prefix = os.path.join(self.root_path, prefix)
        # Note: os.walk lists everything, we need to filter relative paths
        # This naive implementation is sufficient for expected usage patterns
        for root, _, files in os.walk(self.root_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.root_path)
                if rel_path.startswith(prefix):
                    results.append(rel_path)
        return sorted(results)

    def exists(self, key: str) -> bool:
        return os.path.exists(os.path.join(self.root_path, key))

class S3Storage(StorageClient):
    """S3 implementation for prod/stage."""
    
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.audit_s3_endpoint,
            region_name=settings.audit_s3_region,
            aws_access_key_id=settings.audit_s3_access_key,
            aws_secret_access_key=settings.audit_s3_secret_key
        )
        self.bucket = settings.audit_s3_bucket

    def put_object(self, key: str, data: BinaryIO) -> None:
        self.s3.upload_fileobj(data, self.bucket, key)

    def get_object(self, key: str) -> bytes:
        obj = io.BytesIO()
        self.s3.download_fileobj(self.bucket, key, obj)
        return obj.getvalue()

    def list_objects(self, prefix: str) -> List[str]:
        paginator = self.s3.get_paginator("list_objects_v2")
        results = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    results.append(obj["Key"])
        return results

    def exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False

def get_storage_client() -> StorageClient:
    if settings.audit_archive_backend == "s3":
        return S3Storage()
    return LocalFileSystemStorage(settings.audit_archive_path)
