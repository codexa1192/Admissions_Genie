#!/bin/bash

# Admin dashboard
cat > templates/admin/dashboard.html << 'EOF'
{% extends "base.html" %}
{% block title %}Admin Dashboard - Admissions Genie{% endblock %}
{% block content %}
<h2><i class="fas fa-cog"></i> Admin Dashboard</h2>
<div class="row g-4 mb-4">
    <div class="col-md-3"><div class="card bg-primary text-white"><div class="card-body"><h5>Facilities</h5><h2>{{ stats.total_facilities }}</h2><a href="{{ url_for('admin.facilities') }}" class="btn btn-light btn-sm">Manage</a></div></div></div>
    <div class="col-md-3"><div class="card bg-success text-white"><div class="card-body"><h5>Payers</h5><h2>{{ stats.total_payers }}</h2><a href="{{ url_for('admin.payers') }}" class="btn btn-light btn-sm">Manage</a></div></div></div>
    <div class="col-md-3"><div class="card bg-info text-white"><div class="card-body"><h5>Users</h5><h2>{{ stats.total_users }}</h2><a href="{{ url_for('admin.users') }}" class="btn btn-light btn-sm">Manage</a></div></div></div>
    <div class="col-md-3"><div class="card bg-warning"><div class="card-body"><h5>Active Users</h5><h2>{{ stats.active_users }}</h2></div></div></div>
</div>
<div class="row">
    <div class="col-md-12"><h4>Quick Actions</h4><a href="{{ url_for('admin.new_facility') }}" class="btn btn-primary me-2"><i class="fas fa-plus"></i> New Facility</a><a href="{{ url_for('admin.new_payer') }}" class="btn btn-success me-2"><i class="fas fa-plus"></i> New Payer</a><a href="{{ url_for('admin.upload_rates') }}" class="btn btn-info me-2"><i class="fas fa-upload"></i> Upload Rates</a><a href="{{ url_for('admin.new_cost_model') }}" class="btn btn-warning"><i class="fas fa-plus"></i> New Cost Model</a></div>
</div>
{% endblock %}
EOF

# Facilities list
cat > templates/admin/facilities.html << 'EOF'
{% extends "base.html" %}
{% block title %}Facilities - Admin{% endblock %}
{% block content %}
<h2><i class="fas fa-hospital"></i> Facilities</h2>
<a href="{{ url_for('admin.new_facility') }}" class="btn btn-primary mb-3"><i class="fas fa-plus"></i> New Facility</a>
<table class="table table-hover"><thead><tr><th>ID</th><th>Name</th><th>Wage Index</th><th>VBP Multiplier</th><th>Actions</th></tr></thead><tbody>{% for facility in facilities %}<tr><td>{{ facility.id }}</td><td>{{ facility.name }}</td><td>{{ facility.wage_index }}</td><td>{{ facility.vbp_multiplier }}</td><td><a href="{{ url_for('admin.edit_facility', facility_id=facility.id) }}" class="btn btn-sm btn-primary">Edit</a></td></tr>{% endfor %}</tbody></table>
{% endblock %}
EOF

# Facility form
cat > templates/admin/facility_form.html << 'EOF'
{% extends "base.html" %}
{% block title %}{% if facility %}Edit{% else %}New{% endif %} Facility - Admin{% endblock %}
{% block content %}
<h2>{% if facility %}Edit{% else %}New{% endif %} Facility</h2>
<form method="POST"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="mb-3"><label>Name</label><input type="text" class="form-control" name="name" value="{{ facility.name if facility else '' }}" required></div><div class="mb-3"><label>Wage Index</label><input type="number" step="0.0001" class="form-control" name="wage_index" value="{{ facility.wage_index if facility else 1.0 }}" required></div><div class="mb-3"><label>VBP Multiplier</label><input type="number" step="0.01" class="form-control" name="vbp_multiplier" value="{{ facility.vbp_multiplier if facility else 1.0 }}" required></div><div class="mb-3"><label>Capabilities</label><div class="form-check"><input class="form-check-input" type="checkbox" name="dialysis" {% if facility and facility.capabilities.dialysis %}checked{% endif %}><label class="form-check-label">Dialysis</label></div><div class="form-check"><input class="form-check-input" type="checkbox" name="iv_abx" {% if facility and facility.capabilities.iv_abx %}checked{% endif %}><label class="form-check-label">IV Antibiotics</label></div><div class="form-check"><input class="form-check-input" type="checkbox" name="wound_vac" {% if facility and facility.capabilities.wound_vac %}checked{% endif %}><label class="form-check-label">Wound Vac</label></div><div class="form-check"><input class="form-check-input" type="checkbox" name="trach" {% if facility and facility.capabilities.trach %}checked{% endif %}><label class="form-check-label">Tracheostomy</label></div><div class="form-check"><input class="form-check-input" type="checkbox" name="ventilator" {% if facility and facility.capabilities.ventilator %}checked{% endif %}><label class="form-check-label">Ventilator</label></div><div class="form-check"><input class="form-check-input" type="checkbox" name="bariatric" {% if facility and facility.capabilities.bariatric %}checked{% endif %}><label class="form-check-label">Bariatric</label></div></div><button type="submit" class="btn btn-primary">Save</button><a href="{{ url_for('admin.facilities') }}" class="btn btn-secondary">Cancel</a></form>
{% endblock %}
EOF

# Payers list and form
cat > templates/admin/payers.html << 'EOF'
{% extends "base.html" %}
{% block title %}Payers - Admin{% endblock %}
{% block content %}
<h2><i class="fas fa-money-bill"></i> Payers</h2>
<a href="{{ url_for('admin.new_payer') }}" class="btn btn-primary mb-3"><i class="fas fa-plus"></i> New Payer</a>
<table class="table table-hover"><thead><tr><th>ID</th><th>Type</th><th>Plan Name</th><th>Network Status</th><th>Actions</th></tr></thead><tbody>{% for payer in payers %}<tr><td>{{ payer.id }}</td><td>{{ payer.type }}</td><td>{{ payer.plan_name or 'N/A' }}</td><td>{{ payer.network_status }}</td><td><a href="{{ url_for('admin.edit_payer', payer_id=payer.id) }}" class="btn btn-sm btn-primary">Edit</a></td></tr>{% endfor %}</tbody></table>
{% endblock %}
EOF

cat > templates/admin/payer_form.html << 'EOF'
{% extends "base.html" %}
{% block title %}{% if payer %}Edit{% else %}New{% endif %} Payer - Admin{% endblock %}
{% block content %}
<h2>{% if payer %}Edit{% else %}New{% endif %} Payer</h2>
<form method="POST"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="mb-3"><label>Type</label><select class="form-select" name="type" required>{% for payer_type in payer_types %}<option value="{{ payer_type }}" {% if payer and payer.type == payer_type %}selected{% endif %}>{{ payer_type }}</option>{% endfor %}</select></div><div class="mb-3"><label>Plan Name (optional)</label><input type="text" class="form-control" name="plan_name" value="{{ payer.plan_name if payer else '' }}"></div><div class="mb-3"><label>Network Status</label><select class="form-select" name="network_status"><option value="in_network" {% if payer and payer.network_status == 'in_network' %}selected{% endif %}>In Network</option><option value="out_of_network" {% if payer and payer.network_status == 'out_of_network' %}selected{% endif %}>Out of Network</option><option value="single_case" {% if payer and payer.network_status == 'single_case' %}selected{% endif %}>Single Case</option></select></div><button type="submit" class="btn btn-primary">Save</button><a href="{{ url_for('admin.payers') }}" class="btn btn-secondary">Cancel</a></form>
{% endblock %}
EOF

# Rates, cost models, users - simplified
cat > templates/admin/rates.html << 'EOF'
{% extends "base.html" %}
{% block title %}Rates - Admin{% endblock %}
{% block content %}
<h2><i class="fas fa-dollar-sign"></i> Rates Management</h2>
<a href="{{ url_for('admin.upload_rates') }}" class="btn btn-primary mb-3"><i class="fas fa-upload"></i> Upload Rates</a>
<p class="text-muted">Select a facility to view rates.</p>
<form method="GET" class="mb-3"><select class="form-select" name="facility_id" onchange="this.form.submit()"><option value="">Select Facility...</option>{% for facility in facilities %}<option value="{{ facility.id }}" {% if selected_facility and selected_facility.id == facility.id %}selected{% endif %}>{{ facility.name }}</option>{% endfor %}</select></form>
{% if rates %}<table class="table"><thead><tr><th>ID</th><th>Payer</th><th>Type</th><th>Effective Date</th></tr></thead><tbody>{% for rate in rates %}<tr><td>{{ rate.id }}</td><td>{{ rate.payer_id }}</td><td>{{ rate.payer_type }}</td><td>{{ rate.effective_date }}</td></tr>{% endfor %}</tbody></table>{% endif %}
{% endblock %}
EOF

cat > templates/admin/upload_rates.html << 'EOF'
{% extends "base.html" %}
{% block title %}Upload Rates - Admin{% endblock %}
{% block content %}
<h2><i class="fas fa-upload"></i> Upload Rates</h2>
<form method="POST" enctype="multipart/form-data"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="mb-3"><label>Facility</label><select class="form-select" name="facility_id" required>{% for facility in facilities %}<option value="{{ facility.id }}">{{ facility.name }}</option>{% endfor %}</select></div><div class="mb-3"><label>Payer</label><select class="form-select" name="payer_id" required>{% for payer in payers %}<option value="{{ payer.id }}">{{ payer.get_display_name() }}</option>{% endfor %}</select></div><div class="mb-3"><label>Rate Type</label><select class="form-select" name="rate_type" required>{% for rate_type in rate_types %}<option value="{{ rate_type }}">{{ rate_type }}</option>{% endfor %}</select></div><div class="mb-3"><label>CSV File</label><input type="file" class="form-control" name="csv_file" accept=".csv" required></div><div class="mb-3"><label>Effective Date</label><input type="date" class="form-control" name="effective_date" required></div><button type="submit" class="btn btn-primary">Upload</button><a href="{{ url_for('admin.rates') }}" class="btn btn-secondary">Cancel</a></form>
{% endblock %}
EOF

cat > templates/admin/cost_models.html << 'EOF'
{% extends "base.html" %}
{% block title %}Cost Models - Admin{% endblock %}
{% block content %}
<h2><i class="fas fa-calculator"></i> Cost Models</h2>
<a href="{{ url_for('admin.new_cost_model') }}" class="btn btn-primary mb-3"><i class="fas fa-plus"></i> New Cost Model</a>
<form method="GET" class="mb-3"><select class="form-select" name="facility_id" onchange="this.form.submit()"><option value="">Select Facility...</option>{% for facility in facilities %}<option value="{{ facility.id }}" {% if selected_facility and selected_facility.id == facility.id %}selected{% endif %}>{{ facility.name }}</option>{% endfor %}</select></form>
{% if cost_models %}<table class="table"><thead><tr><th>Acuity Band</th><th>Nursing Hours/Day</th><th>Hourly Rate</th><th>Supply Cost</th><th>Actions</th></tr></thead><tbody>{% for cm in cost_models %}<tr><td>{{ cm.acuity_band }}</td><td>{{ cm.nursing_hours }}</td><td>{{ cm.hourly_rate | currency }}</td><td>{{ cm.supply_cost | currency }}</td><td><a href="{{ url_for('admin.edit_cost_model', cost_model_id=cm.id) }}" class="btn btn-sm btn-primary">Edit</a></td></tr>{% endfor %}</tbody></table>{% endif %}
{% endblock %}
EOF

cat > templates/admin/cost_model_form.html << 'EOF'
{% extends "base.html" %}
{% block title %}{% if cost_model %}Edit{% else %}New{% endif %} Cost Model - Admin{% endblock %}
{% block content %}
<h2>{% if cost_model %}Edit{% else %}New{% endif %} Cost Model</h2>
<form method="POST"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}">{% if not cost_model %}<div class="mb-3"><label>Facility</label><select class="form-select" name="facility_id" required>{% for facility in facilities %}<option value="{{ facility.id }}">{{ facility.name }}</option>{% endfor %}</select></div><div class="mb-3"><label>Acuity Band</label><select class="form-select" name="acuity_band" required>{% for band in acuity_bands %}<option value="{{ band }}">{{ band }}</option>{% endfor %}</select></div>{% endif %}<div class="mb-3"><label>Nursing Hours/Day</label><input type="number" step="0.1" class="form-control" name="nursing_hours" value="{{ cost_model.nursing_hours if cost_model else 4.0 }}" required></div><div class="mb-3"><label>Hourly Rate ($)</label><input type="number" step="0.01" class="form-control" name="hourly_rate" value="{{ cost_model.hourly_rate if cost_model else 35.00 }}" required></div><div class="mb-3"><label>Supply Cost/Day ($)</label><input type="number" step="0.01" class="form-control" name="supply_cost" value="{{ cost_model.supply_cost if cost_model else 50.00 }}" required></div><div class="mb-3"><label>Pharmacy Addon ($)</label><input type="number" step="0.01" class="form-control" name="pharmacy_addon" value="{{ cost_model.pharmacy_addon if cost_model else 50.00 }}"></div><div class="mb-3"><label>Transport Cost ($)</label><input type="number" step="0.01" class="form-control" name="transport_cost" value="{{ cost_model.transport_cost if cost_model else 150.00 }}"></div><button type="submit" class="btn btn-primary">Save</button><a href="{{ url_for('admin.cost_models') }}" class="btn btn-secondary">Cancel</a></form>
{% endblock %}
EOF

cat > templates/admin/users.html << 'EOF'
{% extends "base.html" %}
{% block title %}Users - Admin{% endblock %}
{% block content %}
<h2><i class="fas fa-users"></i> Users</h2>
<table class="table table-hover"><thead><tr><th>ID</th><th>Email</th><th>Name</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead><tbody>{% for user in users %}<tr><td>{{ user.id }}</td><td>{{ user.email }}</td><td>{{ user.full_name or 'N/A' }}</td><td><span class="badge bg-{% if user.role == 'admin' %}danger{% else %}primary{% endif %}">{{ user.role }}</span></td><td><span class="badge bg-{% if user.is_active %}success{% else %}secondary{% endif %}">{% if user.is_active %}Active{% else %}Inactive{% endif %}</span></td><td><form method="POST" action="{{ url_for('admin.toggle_user_active', user_id=user.id) }}" class="d-inline"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button type="submit" class="btn btn-sm btn-{% if user.is_active %}warning{% else %}success{% endif %}">{% if user.is_active %}Deactivate{% else %}Activate{% endif %}</button></form></td></tr>{% endfor %}</tbody></table>
{% endblock %}
EOF

echo "✅ All admin templates created!"

