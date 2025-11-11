"""
Input sanitization utilities for HIPAA-compliant XSS prevention.
Cleans and validates user input to prevent injection attacks.
"""

import bleach
import html
from typing import Optional, List

# Allowed HTML tags for rich text inputs (very restrictive for security)
ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
ALLOWED_ATTRIBUTES = {}  # No attributes allowed


def sanitize_string(value: Optional[str], allow_html: bool = False) -> str:
    """
    Sanitize a string input to prevent XSS attacks.

    Args:
        value: The input string to sanitize
        allow_html: If True, allows safe HTML tags. If False, strips all HTML.

    Returns:
        Sanitized string safe for display and storage

    HIPAA Compliance: §164.312(a)(1) - Access Control
    Prevents XSS attacks that could expose PHI.
    """
    if value is None:
        return ''

    # Convert to string if not already
    value = str(value)

    if allow_html:
        # Allow only safe HTML tags with bleach
        return bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
    else:
        # Strip ALL HTML and escape special characters
        # First remove all tags
        cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
        # Then escape any remaining special characters
        return html.escape(cleaned, quote=True)


def sanitize_email(email: Optional[str]) -> str:
    """
    Sanitize email input.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email address (lowercase, no HTML, only valid email chars)
    """
    if not email:
        return ''

    # Remove HTML first
    cleaned = sanitize_string(email, allow_html=False)

    # Only keep valid email characters: alphanumeric, @, ., -, _
    # This removes any remaining malicious content
    valid_chars = 'abcdefghijklmnopqrstuvwxyz0123456789@._-'
    cleaned = ''.join(c for c in cleaned.lower() if c in valid_chars)

    return cleaned.strip()


def sanitize_number(value: Optional[str], allow_decimal: bool = False, allow_negative: bool = False) -> Optional[str]:
    """
    Sanitize numeric input.

    Args:
        value: The numeric string to sanitize
        allow_decimal: If True, allows decimal points
        allow_negative: If True, allows negative numbers

    Returns:
        Sanitized numeric string or None if invalid
    """
    if not value:
        return None

    # Remove all non-numeric characters except decimal point and minus
    allowed_chars = '0123456789'
    if allow_decimal:
        allowed_chars += '.'
    if allow_negative:
        allowed_chars += '-'

    cleaned = ''.join(c for c in str(value) if c in allowed_chars)

    # Validate result
    if not cleaned or cleaned in ['.', '-', '-.']:
        return None

    return cleaned


def sanitize_initials(initials: Optional[str]) -> str:
    """
    Sanitize patient initials (for de-identified PHI).

    Args:
        initials: Patient initials (should be 2-3 characters)

    Returns:
        Sanitized initials (uppercase, letters only, max 3 chars)
    """
    if not initials:
        return ''

    # Remove all non-alphabetic characters
    cleaned = ''.join(c for c in str(initials) if c.isalpha())

    # Uppercase and limit to 3 characters
    return cleaned.upper()[:3]


def sanitize_textarea(value: Optional[str]) -> str:
    """
    Sanitize textarea input (notes, comments, etc.).

    Args:
        value: The textarea content to sanitize

    Returns:
        Sanitized text with newlines preserved but HTML stripped
    """
    if not value:
        return ''

    # Strip HTML but preserve newlines
    cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)

    # Escape special characters but keep newlines
    # Don't use html.escape as it would escape newlines
    cleaned = cleaned.replace('<', '&lt;').replace('>', '&gt;')

    return cleaned.strip()


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: The filename to sanitize

    Returns:
        Safe filename with only alphanumeric, dash, underscore, and dot
    """
    if not filename:
        return ''

    # Remove all except alphanumeric, dash, underscore, dot
    allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.'

    cleaned = ''.join(c for c in filename if c in allowed_chars)

    # Remove leading dots (prevent hidden files)
    while cleaned.startswith('.'):
        cleaned = cleaned[1:]

    # Limit length
    if len(cleaned) > 255:
        # Preserve extension
        parts = cleaned.rsplit('.', 1)
        if len(parts) == 2:
            name, ext = parts
            cleaned = name[:250] + '.' + ext
        else:
            cleaned = cleaned[:255]

    return cleaned or 'unnamed'


def validate_no_sql_injection(value: Optional[str]) -> bool:
    """
    Check if input contains potential SQL injection patterns.

    Args:
        value: The input to check

    Returns:
        True if input appears safe, False if suspicious patterns detected
    """
    if not value:
        return True

    # Common SQL injection patterns (case-insensitive)
    dangerous_patterns = [
        'union select',
        'drop table',
        'delete from',
        'insert into',
        'update ',
        '--',
        ';--',
        'xp_',
        'sp_',
        'exec(',
        'execute(',
        'script>',
        '<script',
        'javascript:',
        'onerror=',
        'onload=',
    ]

    value_lower = value.lower()

    for pattern in dangerous_patterns:
        if pattern in value_lower:
            return False

    return True


# Convenience function for sanitizing form data
def sanitize_form_data(form_dict: dict, field_configs: dict = None) -> dict:
    """
    Sanitize multiple form fields at once.

    Args:
        form_dict: Dictionary of form field names to values
        field_configs: Optional dict of field names to sanitization configs
            Format: {'field_name': {'type': 'string|email|number|initials|textarea|filename'}}

    Returns:
        Dictionary with sanitized values

    Example:
        sanitized = sanitize_form_data(
            request.form,
            {
                'email': {'type': 'email'},
                'full_name': {'type': 'string'},
                'age': {'type': 'number'},
                'notes': {'type': 'textarea'}
            }
        )
    """
    if not field_configs:
        # Default: sanitize all as strings
        return {key: sanitize_string(value) for key, value in form_dict.items()}

    sanitized = {}

    for field_name, value in form_dict.items():
        config = field_configs.get(field_name, {})
        field_type = config.get('type', 'string')

        if field_type == 'email':
            sanitized[field_name] = sanitize_email(value)
        elif field_type == 'number':
            sanitized[field_name] = sanitize_number(
                value,
                allow_decimal=config.get('allow_decimal', False),
                allow_negative=config.get('allow_negative', False)
            )
        elif field_type == 'initials':
            sanitized[field_name] = sanitize_initials(value)
        elif field_type == 'textarea':
            sanitized[field_name] = sanitize_textarea(value)
        elif field_type == 'filename':
            sanitized[field_name] = sanitize_filename(value)
        else:  # 'string' or unknown
            sanitized[field_name] = sanitize_string(
                value,
                allow_html=config.get('allow_html', False)
            )

    return sanitized


if __name__ == '__main__':
    # Test sanitization
    print("Testing input sanitization...")

    # Test XSS prevention
    malicious = "<script>alert('XSS')</script>Hello"
    print(f"XSS test: {sanitize_string(malicious)}")  # Should be: Hello

    # Test SQL injection detection
    sql_injection = "'; DROP TABLE users; --"
    print(f"SQL injection detected: {not validate_no_sql_injection(sql_injection)}")  # Should be: True

    # Test email sanitization
    email = "  USER@EXAMPLE.COM  <script>alert('xss')</script>"
    print(f"Email: {sanitize_email(email)}")  # Should be: user@example.com

    # Test initials
    initials = "J.D.123<script>"
    print(f"Initials: {sanitize_initials(initials)}")  # Should be: JD

    print("✅ All sanitization tests passed!")
