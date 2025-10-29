#!/bin/bash

# Create admission/history.html
cat > templates/admission/history.html << 'EOF'
{% extends "base.html" %}
{% block title %}Admission History - Admissions Genie{% endblock %}
{% block content %}
<h2><i class="fas fa-history"></i> Admission History</h2>
<div class="table-responsive">
    <table class="table table-hover">
        <thead><tr><th>ID</th><th>Patient</th><th>Date</th><th>Score</th><th>Recommendation</th><th>Margin</th><th>Decision</th><th>Actions</th></tr></thead>
        <tbody>
            {% for detail in admission_details %}
            <tr>
                <td>{{ detail.admission.id }}</td>
                <td>{{ detail.admission.patient_initials or 'N/A' }}</td>
                <td>{{ detail.admission.created_at.strftime('%Y-%m-%d') if detail.admission.created_at else 'N/A' }}</td>
                <td><span class="badge bg-{% if detail.admission.margin_score >= 70 %}success{% elif detail.admission.margin_score >= 40 %}warning{% else %}danger{% endif %}">{{ detail.admission.margin_score }}/100</span></td>
                <td><span class="badge bg-{% if detail.admission.recommendation == 'Accept' %}success{% elif detail.admission.recommendation == 'Defer' %}warning{% else %}danger{% endif %}">{{ detail.admission.recommendation }}</span></td>
                <td>{{ (detail.admission.projected_revenue - detail.admission.projected_cost) | currency }}</td>
                <td>{% if detail.admission.actual_decision %}<span class="badge bg-secondary">{{ detail.admission.actual_decision }}</span>{% else %}<span class="text-muted">Pending</span>{% endif %}</td>
                <td><a href="{{ url_for('admission.view_admission', admission_id=detail.admission.id) }}" class="btn btn-sm btn-primary"><i class="fas fa-eye"></i> View</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
EOF

# Create register.html
cat > templates/register.html << 'EOF'
{% extends "base.html" %}
{% block title %}Register - Admissions Genie{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow">
            <div class="card-body">
                <h3 class="card-title text-center mb-4"><i class="fas fa-user-plus text-primary"></i> Create Account</h3>
                <form method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" name="email" required></div>
                    <div class="mb-3"><label class="form-label">Full Name</label><input type="text" class="form-control" name="full_name" required></div>
                    <div class="mb-3"><label class="form-label">Password</label><input type="password" class="form-control" name="password" required></div>
                    <div class="mb-3"><label class="form-label">Confirm Password</label><input type="password" class="form-control" name="confirm_password" required></div>
                    <div class="mb-3"><label class="form-label">Facility</label><select class="form-select" name="facility_id"><option value="">No Facility</option>{% for facility in facilities %}<option value="{{ facility.id }}">{{ facility.name }}</option>{% endfor %}</select></div>
                    <div class="d-grid"><button type="submit" class="btn btn-primary btn-lg"><i class="fas fa-user-plus"></i> Register</button></div>
                </form>
                <hr>
                <p class="text-center mb-0">Already have an account? <a href="{{ url_for('auth.login') }}">Login here</a></p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

# Create profile.html
cat > templates/profile.html << 'EOF'
{% extends "base.html" %}
{% block title %}Profile - Admissions Genie{% endblock %}
{% block content %}
<h2><i class="fas fa-user"></i> User Profile</h2>
<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <form method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div class="mb-3"><label class="form-label">Email</label><input type="email" class="form-control" value="{{ user.email }}" disabled></div>
                    <div class="mb-3"><label class="form-label">Full Name</label><input type="text" class="form-control" name="full_name" value="{{ user.full_name or '' }}"></div>
                    <div class="mb-3"><label class="form-label">Facility</label><select class="form-select" name="facility_id"><option value="">No Facility</option>{% for facility in facilities %}<option value="{{ facility.id }}" {% if facility.id == user.facility_id %}selected{% endif %}>{{ facility.name }}</option>{% endfor %}</select></div>
                    <button type="submit" class="btn btn-primary">Update Profile</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

# Create change_password.html
cat > templates/change_password.html << 'EOF'
{% extends "base.html" %}
{% block title %}Change Password - Admissions Genie{% endblock %}
{% block content %}
<h2><i class="fas fa-key"></i> Change Password</h2>
<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <form method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <div class="mb-3"><label class="form-label">Current Password</label><input type="password" class="form-control" name="current_password" required></div>
                    <div class="mb-3"><label class="form-label">New Password</label><input type="password" class="form-control" name="new_password" required></div>
                    <div class="mb-3"><label class="form-label">Confirm New Password</label><input type="password" class="form-control" name="confirm_password" required></div>
                    <button type="submit" class="btn btn-primary">Change Password</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

echo "✅ All critical templates created!"

