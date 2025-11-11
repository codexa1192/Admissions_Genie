"""
Password validation utilities for HIPAA-compliant password policies.
Enforces strong password requirements.
"""

import re
from typing import Tuple, List


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against HIPAA-compliant strength requirements.

    HIPAA Compliance: §164.308(a)(5)(ii)(D) - Password Management
    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common patterns

    Args:
        password: The password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check minimum length
    if len(password) < 12:
        errors.append("Password must be at least 12 characters long")

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    # Check for digit
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    # Check for special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append("Password must contain at least one special character (!@#$%^&* etc.)")

    # Check for common patterns (optional, but recommended)
    common_patterns = [
        'password', '12345', 'qwerty', 'admin', 'letmein',
        'welcome', 'monkey', 'dragon', 'master', 'sunshine'
    ]

    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            errors.append(f"Password contains common pattern '{pattern}'")
            break

    # Check for sequential characters
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)', password_lower):
        errors.append("Password contains sequential characters (e.g., abc, 123)")

    # Check for repeated characters
    if re.search(r'(.)\1{2,}', password):
        errors.append("Password contains repeated characters (e.g., aaa, 111)")

    is_valid = len(errors) == 0
    return is_valid, errors


def get_password_strength_message(password: str) -> str:
    """
    Get a user-friendly message about password strength.

    Args:
        password: The password to evaluate

    Returns:
        Human-readable strength message
    """
    is_valid, errors = validate_password_strength(password)

    if is_valid:
        return "Strong password"

    return "Weak password: " + "; ".join(errors)


def generate_password_requirements_html() -> str:
    """
    Generate HTML for displaying password requirements to users.

    Returns:
        HTML string with password requirements
    """
    return """
    <div class="password-requirements">
        <p><strong>Password Requirements:</strong></p>
        <ul>
            <li>At least 12 characters long</li>
            <li>Contains uppercase letter (A-Z)</li>
            <li>Contains lowercase letter (a-z)</li>
            <li>Contains number (0-9)</li>
            <li>Contains special character (!@#$%^&* etc.)</li>
            <li>No common patterns or sequential characters</li>
        </ul>
    </div>
    """


if __name__ == '__main__':
    # Test password validation
    test_passwords = [
        'weak',
        'StrongPass123!',
        'MyP@ssw0rd2024',
        'password123',
        'ALLUPPERCASE123!',
        'alllowercase123!',
        'NoSpecialChar123',
        'Short1!',
    ]

    for pwd in test_passwords:
        is_valid, errors = validate_password_strength(pwd)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\n{status}: '{pwd}'")
        if errors:
            for error in errors:
                print(f"  - {error}")
