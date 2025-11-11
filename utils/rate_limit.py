"""
Rate limiting configuration for HIPAA security.
Prevents DoS attacks and resource exhaustion.
"""

# Placeholder module - limiter is initialized in app.py and accessed via current_app
# This module exists for documentation purposes

# Rate limiting is enforced via:
# 1. Global default: 100 requests per hour (set in .env: RATELIMIT_DEFAULT)
# 2. File uploads: Limited to 10 per hour per IP (configured in app.py)
# 3. Admin rate uploads: Limited to 20 per hour per IP (configured in app.py)

# HIPAA Compliance: §164.308(a)(5)(ii)(C) - Log-in Monitoring and Access Control
# Rate limiting prevents:
# - Denial of Service (DoS) attacks
# - Resource exhaustion
# - Brute force attacks
# - Excessive API usage
