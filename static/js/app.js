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

// ========================================
// FORM VALIDATION
// ========================================

// Validate file upload
function validateFile(file, maxSize = 10 * 1024 * 1024, allowedTypes = []) {
    const errors = [];

    // Check file size (default 10MB)
    if (file.size > maxSize) {
        errors.push(`File "${file.name}" is too large. Maximum size is ${maxSize / 1024 / 1024}MB.`);
    }

    // Check file type if specified
    if (allowedTypes.length > 0) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(ext) && !allowedTypes.includes('.' + ext)) {
            errors.push(`File "${file.name}" has invalid type. Allowed: ${allowedTypes.join(', ')}`);
        }
    }

    return errors;
}

// Validate admission form
function validateAdmissionForm(formElement) {
    const errors = [];

    // Check facility selection
    const facilityId = formElement.querySelector('#facility_id');
    if (!facilityId || !facilityId.value) {
        errors.push('Please select a facility');
        facilityId?.classList.add('is-invalid');
    }

    // Check payer selection
    const payerId = formElement.querySelector('#payer_id');
    if (!payerId || !payerId.value) {
        errors.push('Please select a payer');
        payerId?.classList.add('is-invalid');
    }

    // Check projected LOS
    const los = formElement.querySelector('#projected_los');
    if (los && los.value) {
        const losValue = parseInt(los.value);
        if (losValue < 1 || losValue > 100) {
            errors.push('Projected LOS must be between 1 and 100 days');
            los.classList.add('is-invalid');
        }
    }

    // Validate file uploads
    const fileInputs = formElement.querySelectorAll('input[type="file"]');
    const allowedTypes = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'];

    fileInputs.forEach(input => {
        if (input.files && input.files.length > 0) {
            for (let file of input.files) {
                const fileErrors = validateFile(file, 10 * 1024 * 1024, allowedTypes);
                errors.push(...fileErrors);
            }
        }
    });

    return errors;
}

// Add real-time validation to admission form
function initializeFormValidation() {
    const admissionForm = document.getElementById('admissionForm');
    if (!admissionForm) return;

    // Clear invalid state on input
    admissionForm.querySelectorAll('.form-control, .form-select').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('is-invalid');
            const feedback = this.nextElementSibling;
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.remove();
            }
        });
    });

    // Validate on submit
    admissionForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Clear previous validation
        this.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        this.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        // Validate form
        const errors = validateAdmissionForm(this);

        if (errors.length > 0) {
            // Show errors
            const errorMsg = errors.join('<br>');
            showToast(errorMsg, 'danger');
            return false;
        }

        // Show loading state
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        // Check if files are uploaded
        const hasFiles = Array.from(this.querySelectorAll('input[type="file"]'))
            .some(input => input.files && input.files.length > 0);

        if (hasFiles) {
            showLoading('Uploading documents and analyzing admission...<br><small>This may take 30-60 seconds</small>');
        } else {
            showLoading('Analyzing admission...');
        }

        // Submit form
        this.submit();
    });
}

// ========================================
// FILE UPLOAD UX ENHANCEMENTS
// ========================================

// Show file preview and validation feedback
function enhanceFileInputs() {
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const files = this.files;
            if (!files || files.length === 0) return;

            // Create feedback container
            let feedback = this.parentElement.querySelector('.file-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'file-feedback mt-2';
                this.parentElement.appendChild(feedback);
            }

            // Display file info
            const fileList = Array.from(files).map(file => {
                const size = (file.size / 1024).toFixed(1);
                const icon = getFileIcon(file.name);
                const errors = validateFile(file, 10 * 1024 * 1024, ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png']);
                const statusClass = errors.length > 0 ? 'text-danger' : 'text-success';
                const statusIcon = errors.length > 0 ? 'fa-times-circle' : 'fa-check-circle';

                return `
                    <div class="d-flex align-items-center mb-1 ${statusClass}">
                        <i class="fas ${icon} me-2"></i>
                        <span class="me-2">${file.name}</span>
                        <small class="text-muted me-2">(${size} KB)</small>
                        <i class="fas ${statusIcon}"></i>
                    </div>
                `;
            }).join('');

            feedback.innerHTML = fileList;
        });
    });
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image'
    };
    return iconMap[ext] || 'fa-file';
}

// ========================================
// RANGE SLIDER UX
// ========================================

// Show current value for range inputs
function enhanceRangeSliders() {
    const rangeInputs = document.querySelectorAll('input[type="range"]');

    rangeInputs.forEach(input => {
        // Create value display
        const valueDisplay = document.createElement('span');
        valueDisplay.className = 'range-value fw-bold text-primary ms-2';
        valueDisplay.textContent = input.value;

        // Insert after input
        input.parentElement.appendChild(valueDisplay);

        // Update on input
        input.addEventListener('input', function() {
            valueDisplay.textContent = this.value;
        });
    });
}

// ========================================
// TOOLTIPS FOR COMPLEX FIELDS
// ========================================

// Add helpful tooltips to complex fields
function addTooltips() {
    const tooltipData = {
        'facility_id': 'Select the SNF where the patient will be admitted',
        'payer_id': 'Select the primary payer responsible for reimbursement',
        'projected_los': 'Estimated length of stay in days (typically 14-30 for SNF)',
        'auth_status': 'Authorization status from the payer - affects denial risk calculation'
    };

    Object.entries(tooltipData).forEach(([id, text]) => {
        const element = document.getElementById(id);
        if (element) {
            element.setAttribute('data-bs-toggle', 'tooltip');
            element.setAttribute('data-bs-placement', 'top');
            element.setAttribute('title', text);
        }
    });

    // Reinitialize tooltips
    initializeTooltips();
}

// ========================================
// INITIALIZE ALL ENHANCEMENTS
// ========================================

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFormValidation();
    enhanceFileInputs();
    enhanceRangeSliders();
    addTooltips();
});
