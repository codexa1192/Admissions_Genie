"""
File storage service supporting both local filesystem and AWS S3.
Automatically uses S3 in production when configured.
"""

import os
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from datetime import datetime
from config.settings import Config


class FileStorage:
    """Unified file storage interface supporting local and S3 storage."""

    def __init__(self):
        """Initialize file storage based on configuration."""
        self.use_s3 = Config.USE_S3

        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_S3_REGION
            )
            self.bucket = Config.AWS_S3_BUCKET
        else:
            self.s3_client = None
            self.bucket = None
            # Ensure upload folder exists for local storage
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    def save_file(self, file, filename: str = None) -> str:
        """
        Save an uploaded file to storage.

        Args:
            file: FileStorage object from request.files
            filename: Optional custom filename (will be secured)

        Returns:
            Storage key/path for the saved file

        Raises:
            Exception: If file save fails
        """
        if not filename:
            filename = file.filename

        # Secure the filename and add timestamp
        secure_name = secure_filename(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{secure_name}"

        if self.use_s3:
            return self._save_to_s3(file, unique_filename)
        else:
            return self._save_to_local(file, unique_filename)

    def _save_to_s3(self, file, filename: str) -> str:
        """Save file to S3 with server-side encryption."""
        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket,
                filename,
                ExtraArgs={
                    'ServerSideEncryption': Config.AWS_S3_ENCRYPTION,
                    'ContentType': file.content_type or 'application/octet-stream'
                }
            )
            return f"s3://{self.bucket}/{filename}"
        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")

    def _save_to_local(self, file, filename: str) -> str:
        """Save file to local filesystem."""
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        return filepath

    def get_file(self, file_key: str) -> bytes:
        """
        Retrieve file content from storage.

        Args:
            file_key: Storage key/path returned from save_file()

        Returns:
            File content as bytes

        Raises:
            Exception: If file retrieval fails
        """
        if file_key.startswith('s3://'):
            return self._get_from_s3(file_key)
        else:
            return self._get_from_local(file_key)

    def _get_from_s3(self, s3_key: str) -> bytes:
        """Retrieve file from S3."""
        # Parse s3://bucket/key format
        key = s3_key.replace(f"s3://{self.bucket}/", "")

        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to retrieve from S3: {str(e)}")

    def _get_from_local(self, filepath: str) -> bytes:
        """Retrieve file from local filesystem."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, 'rb') as f:
            return f.read()

    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_key: Storage key/path returned from save_file()

        Returns:
            True if successful, False otherwise
        """
        try:
            if file_key.startswith('s3://'):
                return self._delete_from_s3(file_key)
            else:
                return self._delete_from_local(file_key)
        except Exception:
            return False

    def _delete_from_s3(self, s3_key: str) -> bool:
        """Delete file from S3."""
        key = s3_key.replace(f"s3://{self.bucket}/", "")
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def _delete_from_local(self, filepath: str) -> bool:
        """Delete file from local filesystem."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except OSError:
            return False

    def file_exists(self, file_key: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_key: Storage key/path to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            if file_key.startswith('s3://'):
                key = file_key.replace(f"s3://{self.bucket}/", "")
                self.s3_client.head_object(Bucket=self.bucket, Key=key)
                return True
            else:
                return os.path.exists(file_key)
        except:
            return False
