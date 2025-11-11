"""
Virus scanning utilities for HIPAA-compliant malware protection.
Uses ClamAV via clamd daemon for scanning uploaded files.
"""

import os
import logging
from typing import Tuple, Optional
from pathlib import Path

# ClamAV integration
try:
    import clamd
    CLAMD_AVAILABLE = True
except ImportError:
    CLAMD_AVAILABLE = False

logger = logging.getLogger(__name__)


class VirusScanner:
    """
    Manages virus scanning for uploaded files.

    HIPAA Compliance: §164.308(a)(5)(ii)(B) - Protection from Malicious Software
    Scans all uploaded files before processing or storage.
    """

    def __init__(self, use_clamd: bool = True):
        """
        Initialize virus scanner.

        Args:
            use_clamd: Use ClamAV daemon (recommended for production)
        """
        self.use_clamd = use_clamd and CLAMD_AVAILABLE
        self.clamd_client = None

        if self.use_clamd:
            try:
                # Try to connect to ClamAV daemon
                self.clamd_client = clamd.ClamdUnixSocket()
                # Test connection
                self.clamd_client.ping()
                logger.info("✅ ClamAV daemon connected successfully")
            except (clamd.ConnectionError, FileNotFoundError) as e:
                logger.warning(f"⚠️  ClamAV daemon not available: {e}")
                logger.warning("⚠️  Virus scanning will be DISABLED - NOT RECOMMENDED FOR PRODUCTION")
                self.use_clamd = False
                self.clamd_client = None
        else:
            if not CLAMD_AVAILABLE:
                logger.warning("⚠️  python-clamd not installed. Install with: pip install python-clamd")
            logger.warning("⚠️  Virus scanning DISABLED - NOT RECOMMENDED FOR PRODUCTION")

    def scan_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Scan a file for viruses.

        Args:
            file_path: Path to file to scan

        Returns:
            Tuple of (is_clean, threat_name)
            - is_clean: True if file is safe, False if infected
            - threat_name: Name of detected threat, None if clean
        """
        if not self.use_clamd or not self.clamd_client:
            # Scanning disabled - log warning and allow file
            logger.warning(f"⚠️  Virus scanning bypassed for {file_path} - ClamAV not available")
            return (True, None)

        try:
            # Scan the file
            result = self.clamd_client.scan(file_path)

            if result is None:
                # File is clean
                logger.info(f"✅ Virus scan passed: {file_path}")
                return (True, None)

            # File is infected
            file_result = result.get(file_path)
            if file_result:
                status, threat_name = file_result
                if status == 'FOUND':
                    logger.error(f"🦠 VIRUS DETECTED: {file_path} - {threat_name}")
                    return (False, threat_name)

            # Unknown result
            logger.warning(f"⚠️  Unknown scan result for {file_path}: {result}")
            return (True, None)

        except clamd.ConnectionError as e:
            logger.error(f"❌ ClamAV connection error: {e}")
            # Fail-safe: deny file if scanner is unavailable in production
            if os.getenv('FLASK_ENV') == 'production':
                logger.critical("🚨 SECURITY: Rejecting file due to scanner unavailability in PRODUCTION")
                return (False, "Scanner unavailable")
            else:
                logger.warning("⚠️  Development mode: allowing file despite scanner error")
                return (True, None)

        except Exception as e:
            logger.error(f"❌ Virus scan error for {file_path}: {e}")
            # Fail-safe: deny file on error in production
            if os.getenv('FLASK_ENV') == 'production':
                logger.critical("🚨 SECURITY: Rejecting file due to scan error in PRODUCTION")
                return (False, "Scan error")
            else:
                logger.warning("⚠️  Development mode: allowing file despite scan error")
                return (True, None)

    def scan_bytes(self, data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Scan bytes in memory for viruses.

        Args:
            data: Bytes to scan

        Returns:
            Tuple of (is_clean, threat_name)
        """
        if not self.use_clamd or not self.clamd_client:
            logger.warning("⚠️  Virus scanning bypassed for bytes - ClamAV not available")
            return (True, None)

        try:
            # Scan the bytes
            result = self.clamd_client.instream(data)

            if result.get('stream') == ('OK', None):
                # Data is clean
                logger.info("✅ Virus scan passed: in-memory data")
                return (True, None)

            # Data is infected
            status, threat_name = result.get('stream', (None, None))
            if status == 'FOUND':
                logger.error(f"🦠 VIRUS DETECTED in bytes - {threat_name}")
                return (False, threat_name)

            # Unknown result
            logger.warning(f"⚠️  Unknown scan result for bytes: {result}")
            return (True, None)

        except clamd.ConnectionError as e:
            logger.error(f"❌ ClamAV connection error: {e}")
            # Fail-safe: deny on error in production
            if os.getenv('FLASK_ENV') == 'production':
                return (False, "Scanner unavailable")
            return (True, None)

        except Exception as e:
            logger.error(f"❌ Virus scan error for bytes: {e}")
            # Fail-safe: deny on error in production
            if os.getenv('FLASK_ENV') == 'production':
                return (False, "Scan error")
            return (True, None)

    def is_available(self) -> bool:
        """
        Check if virus scanning is available.

        Returns:
            True if ClamAV is connected and working
        """
        return self.use_clamd and self.clamd_client is not None

    def get_version(self) -> Optional[str]:
        """
        Get ClamAV version information.

        Returns:
            Version string or None if not available
        """
        if not self.is_available():
            return None

        try:
            return self.clamd_client.version()
        except Exception as e:
            logger.error(f"Error getting ClamAV version: {e}")
            return None


# Global virus scanner instance
_virus_scanner: Optional[VirusScanner] = None


def get_virus_scanner() -> VirusScanner:
    """
    Get the global virus scanner instance.

    Returns:
        VirusScanner singleton instance
    """
    global _virus_scanner

    if _virus_scanner is None:
        _virus_scanner = VirusScanner()

    return _virus_scanner


# Convenience functions
def scan_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Scan a file for viruses.

    Returns:
        Tuple of (is_clean, threat_name)
    """
    return get_virus_scanner().scan_file(file_path)


def scan_bytes(data: bytes) -> Tuple[bool, Optional[str]]:
    """
    Scan bytes for viruses.

    Returns:
        Tuple of (is_clean, threat_name)
    """
    return get_virus_scanner().scan_bytes(data)


def is_scanner_available() -> bool:
    """
    Check if virus scanning is available.

    Returns:
        True if ClamAV is working
    """
    return get_virus_scanner().is_available()


if __name__ == '__main__':
    # Test virus scanner
    scanner = VirusScanner()

    print(f"ClamAV available: {scanner.is_available()}")

    if scanner.is_available():
        version = scanner.get_version()
        print(f"ClamAV version: {version}")

        # Test EICAR file (standard test virus)
        print("\nTesting with EICAR test file...")
        print("Create test file with: echo 'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.txt")
