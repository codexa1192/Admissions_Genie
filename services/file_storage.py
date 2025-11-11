"""
File storage service supporting local filesystem, AWS S3, and Azure Blob Storage.
Automatically uses cloud storage in production when configured.
Includes HIPAA-compliant encryption for local file storage.
"""

import os
import logging
from werkzeug.utils import secure_filename
from datetime import datetime
from config.settings import Config
from utils.encryption import get_encryption_manager
from utils.virus_scanner import get_virus_scanner
from utils.audit_logger import log_audit_event

logger = logging.getLogger(__name__)

# Conditionally import cloud storage libraries
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    from azure.storage.blob import BlobServiceClient, ContentSettings
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False


class FileStorage:
    """Unified file storage interface supporting local, S3, and Azure Blob storage."""

    def __init__(self):
        """Initialize file storage based on configuration."""
        self.use_s3 = Config.USE_S3
        self.use_azure = Config.USE_AZURE

        # Validate configuration
        if self.use_s3 and self.use_azure:
            raise ValueError("Cannot use both S3 and Azure Blob Storage. Set only one.")

        if self.use_s3:
            if not HAS_BOTO3:
                raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_S3_REGION
            )
            self.bucket = Config.AWS_S3_BUCKET
        elif self.use_azure:
            if not HAS_AZURE:
                raise ImportError("azure-storage-blob is required for Azure storage. Install with: pip install azure-storage-blob")
            self.blob_service_client = BlobServiceClient(
                account_url=f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
                credential=Config.AZURE_STORAGE_ACCOUNT_KEY
            )
            self.container_name = Config.AZURE_STORAGE_CONTAINER_NAME
        else:
            # Local storage
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
        elif self.use_azure:
            return self._save_to_azure(file, unique_filename)
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

    def _save_to_azure(self, file, filename: str) -> str:
        """Save file to Azure Blob Storage with encryption."""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=filename
            )

            # Upload with content type
            content_settings = ContentSettings(content_type=file.content_type or 'application/octet-stream')

            # Reset file pointer to beginning
            file.seek(0)

            # Upload to Azure (encryption is automatic at storage account level)
            blob_client.upload_blob(
                file,
                overwrite=True,
                content_settings=content_settings
            )

            return f"azure://{self.container_name}/{filename}"
        except Exception as e:
            raise Exception(f"Failed to upload to Azure Blob Storage: {str(e)}")

    def _save_to_local(self, file, filename: str) -> str:
        """
        Save file to local filesystem with virus scanning and encryption.

        HIPAA Compliance:
        - §164.308(a)(5)(ii)(B) - Malware Protection (virus scanning)
        - §164.312(a)(2)(iv) - Encryption at rest
        """
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)

        # Save to temporary file first (for scanning and encryption)
        temp_path = filepath + '.tmp'
        file.save(temp_path)

        try:
            # HIPAA REQUIRED: Virus scan before processing
            virus_scanner = get_virus_scanner()
            is_clean, threat_name = virus_scanner.scan_file(temp_path)

            if not is_clean:
                # SECURITY: File is infected - delete and log
                os.remove(temp_path)

                # Log security incident
                log_audit_event(
                    action='virus_detected',
                    resource_type='file',
                    resource_id=filename,
                    changes={
                        'filename': filename,
                        'threat': threat_name,
                        'action': 'rejected'
                    }
                )

                logger.error(f"🦠 VIRUS DETECTED: {filename} - {threat_name}")
                raise Exception(f"File rejected: Virus detected ({threat_name})")

            # File is clean - log successful scan
            logger.info(f"✅ Virus scan passed: {filename}")
            log_audit_event(
                action='file_uploaded',
                resource_type='file',
                resource_id=filename,
                changes={
                    'filename': filename,
                    'scanned': True,
                    'encrypted': os.getenv('ENCRYPTION_KEY') is not None
                }
            )

            # Check if encryption is enabled
            encryption_enabled = os.getenv('ENCRYPTION_KEY') is not None

            if encryption_enabled:
                # Encrypt the file
                try:
                    encryption_manager = get_encryption_manager()
                    encrypted_path = encryption_manager.encrypt_file(temp_path, filepath + '.encrypted')

                    # Remove temporary unencrypted file
                    os.remove(temp_path)

                    return encrypted_path
                except Exception as e:
                    # Clean up temp file on error
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise Exception(f"Failed to encrypt file: {str(e)}")
            else:
                # Development mode: no encryption, but still scanned
                os.rename(temp_path, filepath)
                return filepath

        except Exception as e:
            # Clean up temp file on any error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

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
        elif file_key.startswith('azure://'):
            return self._get_from_azure(file_key)
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

    def _get_from_azure(self, azure_key: str) -> bytes:
        """Retrieve file from Azure Blob Storage."""
        # Parse azure://container/blob format
        blob_name = azure_key.replace(f"azure://{self.container_name}/", "")

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        except Exception as e:
            raise Exception(f"Failed to retrieve from Azure Blob Storage: {str(e)}")

    def _get_from_local(self, filepath: str) -> bytes:
        """
        Retrieve file from local filesystem with decryption.

        HIPAA Compliance: Decrypts encrypted files when ENCRYPTION_KEY is set.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Check if encryption is enabled and file is encrypted
        encryption_enabled = os.getenv('ENCRYPTION_KEY') is not None
        is_encrypted = filepath.endswith('.encrypted')

        if encryption_enabled and is_encrypted:
            # Decrypt the file
            try:
                encryption_manager = get_encryption_manager()

                # Decrypt to temporary file
                temp_decrypted = filepath.replace('.encrypted', '.decrypted.tmp')
                encryption_manager.decrypt_file(filepath, temp_decrypted)

                # Read decrypted content
                with open(temp_decrypted, 'rb') as f:
                    content = f.read()

                # Remove temporary decrypted file
                os.remove(temp_decrypted)

                return content
            except Exception as e:
                # Clean up temp file on error
                temp_decrypted = filepath.replace('.encrypted', '.decrypted.tmp')
                if os.path.exists(temp_decrypted):
                    os.remove(temp_decrypted)
                raise Exception(f"Failed to decrypt file: {str(e)}")
        else:
            # Read unencrypted file (development mode or legacy data)
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
            elif file_key.startswith('azure://'):
                return self._delete_from_azure(file_key)
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

    def _delete_from_azure(self, azure_key: str) -> bool:
        """Delete file from Azure Blob Storage."""
        blob_name = azure_key.replace(f"azure://{self.container_name}/", "")
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            return True
        except Exception:
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
            elif file_key.startswith('azure://'):
                blob_name = file_key.replace(f"azure://{self.container_name}/", "")
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                return blob_client.exists()
            else:
                return os.path.exists(file_key)
        except:
            return False
