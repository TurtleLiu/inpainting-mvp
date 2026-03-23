from minio import Minio
from minio.error import S3Error
import os

def get_minio_client():
    client = Minio(
        os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "admin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "password"),
        secure=False
    )
    return client

def ensure_bucket_exists(bucket_name="inpainting"):
    client = get_minio_client()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    return bucket_name

def upload_file(file_path, object_name, bucket_name="inpainting"):
    client = get_minio_client()
    ensure_bucket_exists(bucket_name)
    
    try:
        client.fput_object(
            bucket_name,
            object_name,
            file_path,
            content_type="image/png"
        )
        return True
    except S3Error as e:
        print(f"Error uploading file: {e}")
        return False

def download_file(object_name, file_path, bucket_name="inpainting"):
    client = get_minio_client()
    
    try:
        client.fget_object(
            bucket_name,
            object_name,
            file_path
        )
        return True
    except S3Error as e:
        print(f"Error downloading file: {e}")
        return False