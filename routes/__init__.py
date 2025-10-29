"""
Route blueprints for Admissions Genie.
"""

from .auth import auth_bp
from .admission import admission_bp
from .admin import admin_bp

__all__ = ['auth_bp', 'admission_bp', 'admin_bp']
