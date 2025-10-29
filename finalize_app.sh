#!/bin/bash

# Create error pages
cat > templates/errors/404.html << 'EOF'
{% extends "base.html" %}
{% block title %}404 - Page Not Found{% endblock %}
{% block content %}
<div class="text-center mt-5">
    <h1 class="display-1">404</h1>
    <h3>Page Not Found</h3>
    <p class="text-muted">The page you're looking for doesn't exist.</p>
    <a href="{{ url_for('dashboard') }}" class="btn btn-primary"><i class="fas fa-home"></i> Go to Dashboard</a>
</div>
{% endblock %}
EOF

cat > templates/errors/500.html << 'EOF'
{% extends "base.html" %}
{% block title %}500 - Server Error{% endblock %}
{% block content %}
<div class="text-center mt-5">
    <h1 class="display-1">500</h1>
    <h3>Internal Server Error</h3>
    <p class="text-muted">Something went wrong. Please try again later.</p>
    <a href="{{ url_for('dashboard') }}" class="btn btn-primary"><i class="fas fa-home"></i> Go to Dashboard</a>
</div>
{% endblock %}
EOF

cat > templates/errors/403.html << 'EOF'
{% extends "base.html" %}
{% block title %}403 - Forbidden{% endblock %}
{% block content %}
<div class="text-center mt-5">
    <h1 class="display-1">403</h1>
    <h3>Access Forbidden</h3>
    <p class="text-muted">You don't have permission to access this page.</p>
    <a href="{{ url_for('dashboard') }}" class="btn btn-primary"><i class="fas fa-home"></i> Go to Dashboard</a>
</div>
{% endblock %}
EOF

# Create .env file with secure secret key
cat > .env << 'EOF'
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-CHANGE-IN-PRODUCTION-$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=sqlite:///admissions.db

# Azure OpenAI Configuration (HIPAA-compliant)
# IMPORTANT: Add your actual credentials here
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Application Settings
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,jpg,jpeg,png
PHI_STRICT_MODE=false

# Security Settings
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
RATELIMIT_DEFAULT=100 per hour

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/admissions-genie.log
EOF

# Create JavaScript file
cat > static/js/app.js << 'EOF'
// Admissions Genie - Client-Side JavaScript

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admissions Genie initialized');
    
    // Add any global event listeners here
    initializeTooltips();
    initializeConfirmations();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Initialize confirmation dialogs for destructive actions
function initializeConfirmations() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

// Show loading spinner
function showLoading(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">${message}</p>
    `;
    document.body.appendChild(overlay);
}

// Hide loading spinner
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Display toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}
EOF

# Create logs directory
mkdir -p logs

echo "✅ Finalization complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your Azure OpenAI credentials"
echo "2. Run: python3 app.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "🔐 Login credentials:"
echo "   Admin: admin@admissionsgenie.com / admin123"
echo "   User:  user@admissionsgenie.com / user123"

