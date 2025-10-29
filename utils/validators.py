"""
Input validation utilities for Admissions Genie.
Provides comprehensive validation for forms, files, and business logic.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from werkzeug.datastructures import FileStorage


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class AdmissionValidator:
    """Validates admission form data."""

    MIN_LOS = 1
    MAX_LOS = 100
    MAX_PATIENT_INITIALS_LENGTH = 5

    @staticmethod
    def validate_facility_id(facility_id: any) -> Tuple[bool, str]:
        """Validate facility ID."""
        try:
            fac_id = int(facility_id)
            if fac_id <= 0:
                return False, "Facility ID must be positive"
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid facility ID"

    @staticmethod
    def validate_payer_id(payer_id: any) -> Tuple[bool, str]:
        """Validate payer ID."""
        try:
            pay_id = int(payer_id)
            if pay_id <= 0:
                return False, "Payer ID must be positive"
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid payer ID"

    @staticmethod
    def validate_los(los: any) -> Tuple[bool, str]:
        """Validate length of stay."""
        try:
            los_value = int(los)
            if los_value < AdmissionValidator.MIN_LOS:
                return False, f"Length of stay must be at least {AdmissionValidator.MIN_LOS} day"
            if los_value > AdmissionValidator.MAX_LOS:
                return False, f"Length of stay cannot exceed {AdmissionValidator.MAX_LOS} days"
            return True, ""
        except (ValueError, TypeError):
            return False, "Length of stay must be a number"

    @staticmethod
    def validate_patient_initials(initials: str) -> Tuple[bool, str]:
        """Validate patient initials."""
        if not initials:
            return False, "Patient initials are required"

        # Only allow letters
        if not re.match(r'^[A-Za-z]+$', initials):
            return False, "Patient initials must contain only letters"

        if len(initials) > AdmissionValidator.MAX_PATIENT_INITIALS_LENGTH:
            return False, f"Patient initials cannot exceed {AdmissionValidator.MAX_PATIENT_INITIALS_LENGTH} characters"

        return True, ""

    @staticmethod
    def validate_auth_status(auth_status: str) -> Tuple[bool, str]:
        """Validate authorization status."""
        valid_statuses = ['approved', 'pending', 'denied', 'unknown']
        if auth_status.lower() not in valid_statuses:
            return False, f"Authorization status must be one of: {', '.join(valid_statuses)}"
        return True, ""

    @staticmethod
    def validate_census_percentage(census_pct: any) -> Tuple[bool, str]:
        """Validate census percentage."""
        try:
            pct = float(census_pct)
            if pct < 0 or pct > 100:
                return False, "Census percentage must be between 0 and 100"
            return True, ""
        except (ValueError, TypeError):
            return False, "Census percentage must be a number"

    @classmethod
    def validate_admission_form(cls, form_data: Dict) -> List[str]:
        """
        Validate entire admission form.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Required fields
        if 'facility_id' not in form_data or not form_data['facility_id']:
            errors.append("Facility is required")
        else:
            valid, msg = cls.validate_facility_id(form_data['facility_id'])
            if not valid:
                errors.append(msg)

        if 'payer_id' not in form_data or not form_data['payer_id']:
            errors.append("Payer is required")
        else:
            valid, msg = cls.validate_payer_id(form_data['payer_id'])
            if not valid:
                errors.append(msg)

        # Optional fields with validation
        if 'estimated_los' in form_data and form_data['estimated_los']:
            valid, msg = cls.validate_los(form_data['estimated_los'])
            if not valid:
                errors.append(msg)

        if 'patient_initials' in form_data and form_data['patient_initials']:
            valid, msg = cls.validate_patient_initials(form_data['patient_initials'])
            if not valid:
                errors.append(msg)

        if 'auth_status' in form_data and form_data['auth_status']:
            valid, msg = cls.validate_auth_status(form_data['auth_status'])
            if not valid:
                errors.append(msg)

        if 'current_census_pct' in form_data and form_data['current_census_pct']:
            valid, msg = cls.validate_census_percentage(form_data['current_census_pct'])
            if not valid:
                errors.append(msg)

        return errors


class FileValidator:
    """Validates file uploads."""

    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB total

    # Allowed extensions
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'}

    # Allowed MIME types (for additional security)
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png'
    }

    @staticmethod
    def validate_file_extension(filename: str) -> Tuple[bool, str]:
        """Validate file has allowed extension."""
        if '.' not in filename:
            return False, "File must have an extension"

        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            return False, f"File type '.{ext}' not allowed. Allowed types: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"

        return True, ""

    @staticmethod
    def validate_file_size(file: FileStorage) -> Tuple[bool, str]:
        """Validate file size."""
        # Seek to end to get size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)  # Reset to beginning

        if size > FileValidator.MAX_FILE_SIZE:
            size_mb = size / 1024 / 1024
            max_mb = FileValidator.MAX_FILE_SIZE / 1024 / 1024
            return False, f"File too large ({size_mb:.1f}MB). Maximum size is {max_mb:.0f}MB"

        return True, ""

    @staticmethod
    def validate_mime_type(file: FileStorage) -> Tuple[bool, str]:
        """Validate MIME type for security."""
        if file.mimetype not in FileValidator.ALLOWED_MIME_TYPES:
            return False, f"File type '{file.mimetype}' not allowed"
        return True, ""

    @classmethod
    def validate_file(cls, file: FileStorage, check_mime: bool = True) -> List[str]:
        """
        Comprehensive file validation.

        Args:
            file: FileStorage object from Flask
            check_mime: Whether to check MIME type (requires file content)

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not file or not file.filename:
            errors.append("No file provided")
            return errors

        # Validate extension
        valid, msg = cls.validate_file_extension(file.filename)
        if not valid:
            errors.append(msg)

        # Validate size
        valid, msg = cls.validate_file_size(file)
        if not valid:
            errors.append(msg)

        # Validate MIME type (optional - more secure but requires file content)
        if check_mime:
            valid, msg = cls.validate_mime_type(file)
            if not valid:
                errors.append(msg)

        return errors

    @classmethod
    def validate_multiple_files(cls, files: List[FileStorage]) -> Tuple[List[str], int]:
        """
        Validate multiple files.

        Returns:
            Tuple of (error_messages, total_size)
        """
        errors = []
        total_size = 0

        for file in files:
            if not file or not file.filename:
                continue

            # Validate individual file
            file_errors = cls.validate_file(file)
            errors.extend(file_errors)

            # Track total size
            file.seek(0, os.SEEK_END)
            total_size += file.tell()
            file.seek(0)

        # Check total size
        if total_size > cls.MAX_TOTAL_SIZE:
            total_mb = total_size / 1024 / 1024
            max_mb = cls.MAX_TOTAL_SIZE / 1024 / 1024
            errors.append(f"Total upload size ({total_mb:.1f}MB) exceeds maximum ({max_mb:.0f}MB)")

        return errors, total_size


class BusinessLogicValidator:
    """Validates business logic rules."""

    @staticmethod
    def validate_margin_score(score: float) -> Tuple[bool, str]:
        """Validate margin score is in valid range."""
        if score < 0 or score > 100:
            return False, "Margin score must be between 0 and 100"
        return True, ""

    @staticmethod
    def validate_revenue(revenue: float) -> Tuple[bool, str]:
        """Validate projected revenue."""
        if revenue < 0:
            return False, "Revenue cannot be negative"
        if revenue > 1000000:  # $1M sanity check
            return False, "Revenue seems unrealistic (exceeds $1M)"
        return True, ""

    @staticmethod
    def validate_cost(cost: float) -> Tuple[bool, str]:
        """Validate projected cost."""
        if cost < 0:
            return False, "Cost cannot be negative"
        if cost > 1000000:  # $1M sanity check
            return False, "Cost seems unrealistic (exceeds $1M)"
        return True, ""

    @staticmethod
    def validate_denial_risk(risk: float) -> Tuple[bool, str]:
        """Validate denial risk probability."""
        if risk < 0 or risk > 1:
            return False, "Denial risk must be between 0 and 1"
        return True, ""


def validate_admission_request(form_data: Dict, files: Dict) -> List[str]:
    """
    Master validation function for admission requests.

    Args:
        form_data: Form data dictionary
        files: Dictionary of file lists (field_name -> list of FileStorage)

    Returns:
        List of all validation errors
    """
    errors = []

    # Validate form data
    form_errors = AdmissionValidator.validate_admission_form(form_data)
    errors.extend(form_errors)

    # Validate files
    all_files = []
    for file_list in files.values():
        all_files.extend(file_list)

    if all_files:
        file_errors, _ = FileValidator.validate_multiple_files(all_files)
        errors.extend(file_errors)

    return errors
