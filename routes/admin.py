"""
Admin routes for managing facilities, payers, rates, and cost models.
Includes comprehensive HIPAA audit logging for all administrative actions.
"""

import csv
import io
import json
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session

from routes.auth import admin_required
from models.facility import Facility
from models.payer import Payer
from models.rates import Rate
from models.cost_model import CostModel
from models.user import User
from utils.audit_logger import log_audit_event

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard."""
    # Get current user's organization for multi-tenant data
    current_user = User.get_by_id(session['user_id'])
    facilities = Facility.get_all(organization_id=current_user.organization_id)
    payers = Payer.get_all(organization_id=current_user.organization_id)
    users = User.get_all(organization_id=current_user.organization_id)

    stats = {
        'total_facilities': len(facilities),
        'total_payers': len(payers),
        'total_users': len(users),
        'active_users': len([u for u in users if u.is_active])
    }

    return render_template('admin/dashboard.html', stats=stats, facilities=facilities)


# ===== FACILITY MANAGEMENT =====

@admin_bp.route('/facilities')
@admin_required
def facilities():
    """List all facilities."""
    current_user = User.get_by_id(session['user_id'])
    facilities = Facility.get_all(organization_id=current_user.organization_id)
    return render_template('admin/facilities.html', facilities=facilities)


@admin_bp.route('/facilities/new', methods=['GET', 'POST'])
@admin_required
def new_facility():
    """Create new facility."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        wage_index = float(request.form.get('wage_index', 1.0))
        vbp_multiplier = float(request.form.get('vbp_multiplier', 1.0))

        # Parse capabilities from checkboxes
        capabilities = {
            'dialysis': request.form.get('dialysis') == 'on',
            'iv_abx': request.form.get('iv_abx') == 'on',
            'wound_vac': request.form.get('wound_vac') == 'on',
            'trach': request.form.get('trach') == 'on',
            'ventilator': request.form.get('ventilator') == 'on',
            'bariatric': request.form.get('bariatric') == 'on',
        }

        try:
            facility = Facility.create(name, wage_index, vbp_multiplier, capabilities)

            # HIPAA Audit Log: Facility creation
            log_audit_event(
                action='facility_created',
                resource_type='facility',
                resource_id=facility.id,
                changes={'new': facility.to_dict()}
            )

            flash(f'Facility "{name}" created successfully!', 'success')
            return redirect(url_for('admin.facilities'))
        except Exception as e:
            flash(f'Error creating facility: {str(e)}', 'danger')

    return render_template('admin/facility_form.html', facility=None)


@admin_bp.route('/facilities/<int:facility_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_facility(facility_id):
    """Edit facility."""
    facility = Facility.get_by_id(facility_id)

    if not facility:
        flash('Facility not found.', 'danger')
        return redirect(url_for('admin.facilities'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        wage_index = float(request.form.get('wage_index', 1.0))
        vbp_multiplier = float(request.form.get('vbp_multiplier', 1.0))

        capabilities = {
            'dialysis': request.form.get('dialysis') == 'on',
            'iv_abx': request.form.get('iv_abx') == 'on',
            'wound_vac': request.form.get('wound_vac') == 'on',
            'trach': request.form.get('trach') == 'on',
            'ventilator': request.form.get('ventilator') == 'on',
            'bariatric': request.form.get('bariatric') == 'on',
        }

        try:
            # Capture old values before update
            old_data = facility.to_dict()

            facility.update(name, wage_index, vbp_multiplier, capabilities)

            # HIPAA Audit Log: Facility update
            log_audit_event(
                action='facility_updated',
                resource_type='facility',
                resource_id=facility.id,
                changes={'old': old_data, 'new': facility.to_dict()}
            )

            flash(f'Facility "{name}" updated successfully!', 'success')
            return redirect(url_for('admin.facilities'))
        except Exception as e:
            flash(f'Error updating facility: {str(e)}', 'danger')

    return render_template('admin/facility_form.html', facility=facility)


# ===== PAYER MANAGEMENT =====

@admin_bp.route('/payers')
@admin_required
def payers():
    """List all payers."""
    current_user = User.get_by_id(session['user_id'])
    payers = Payer.get_all(organization_id=current_user.organization_id)
    return render_template('admin/payers.html', payers=payers)


@admin_bp.route('/payers/new', methods=['GET', 'POST'])
@admin_required
def new_payer():
    """Create new payer."""
    if request.method == 'POST':
        payer_type = request.form.get('type')
        plan_name = request.form.get('plan_name', '').strip() or None
        network_status = request.form.get('network_status', 'in_network')

        try:
            payer = Payer.create(payer_type, plan_name, network_status)

            # HIPAA Audit Log: Payer creation
            log_audit_event(
                action='payer_created',
                resource_type='payer',
                resource_id=payer.id,
                changes={'new': payer.to_dict()}
            )

            flash(f'Payer "{payer.get_display_name()}" created successfully!', 'success')
            return redirect(url_for('admin.payers'))
        except Exception as e:
            flash(f'Error creating payer: {str(e)}', 'danger')

    return render_template('admin/payer_form.html', payer=None, payer_types=Payer.PAYER_TYPES)


@admin_bp.route('/payers/<int:payer_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_payer(payer_id):
    """Edit payer."""
    payer = Payer.get_by_id(payer_id)

    if not payer:
        flash('Payer not found.', 'danger')
        return redirect(url_for('admin.payers'))

    if request.method == 'POST':
        payer_type = request.form.get('type')
        plan_name = request.form.get('plan_name', '').strip() or None
        network_status = request.form.get('network_status', 'in_network')

        try:
            # Capture old values before update
            old_data = payer.to_dict()

            payer.update(payer_type, plan_name, network_status)

            # HIPAA Audit Log: Payer update
            log_audit_event(
                action='payer_updated',
                resource_type='payer',
                resource_id=payer.id,
                changes={'old': old_data, 'new': payer.to_dict()}
            )

            flash(f'Payer "{payer.get_display_name()}" updated successfully!', 'success')
            return redirect(url_for('admin.payers'))
        except Exception as e:
            flash(f'Error updating payer: {str(e)}', 'danger')

    return render_template('admin/payer_form.html', payer=payer, payer_types=Payer.PAYER_TYPES)


# ===== RATE MANAGEMENT =====

@admin_bp.route('/rates')
@admin_required
def rates():
    """List all rates."""
    current_user = User.get_by_id(session['user_id'])
    facility_id = request.args.get('facility_id', type=int)

    if facility_id:
        facility = Facility.get_by_id(facility_id)
        rates_list = Rate.get_all_for_facility(facility_id)
    else:
        facility = None
        rates_list = []

    facilities = Facility.get_all(organization_id=current_user.organization_id)

    return render_template('admin/rates.html', rates=rates_list, facilities=facilities,
                          selected_facility=facility)


@admin_bp.route('/rates/upload', methods=['GET', 'POST'])
@admin_required
def upload_rates():
    """Upload rates from CSV file."""
    if request.method == 'POST':
        facility_id = int(request.form.get('facility_id'))
        payer_id = int(request.form.get('payer_id'))
        rate_type = request.form.get('rate_type')
        csv_file = request.files.get('csv_file')

        if not csv_file:
            flash('Please select a CSV file.', 'danger')
            return redirect(url_for('admin.upload_rates'))

        try:
            # Read CSV
            csv_text = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_text))

            # Parse based on rate type
            if rate_type == Rate.MEDICARE_FFS:
                # Expected columns: fiscal_year, pt_component, ot_component, slp_component,
                #                   nursing_component, nta_component, non_case_mix
                for row in csv_reader:
                    rate_data = {
                        'pt_component': float(row['pt_component']),
                        'ot_component': float(row['ot_component']),
                        'slp_component': float(row['slp_component']),
                        'nursing_component': float(row['nursing_component']),
                        'nta_component': float(row['nta_component']),
                        'non_case_mix': float(row['non_case_mix']),
                        'fiscal_year': int(row['fiscal_year'])
                    }
                    effective_date = date(int(row['fiscal_year']), 10, 1)  # FY starts Oct 1

                    Rate.create(facility_id, payer_id, rate_type, rate_data, effective_date)

            elif rate_type == Rate.MA_COMMERCIAL:
                # Expected columns: contract_type, day_range, rate
                rate_data = {'contract_type': 'per_diem', 'day_tiers': {}}
                for row in csv_reader:
                    day_range = row['day_range']
                    rate = float(row['rate'])
                    rate_data['day_tiers'][day_range] = rate

                effective_date = datetime.strptime(request.form.get('effective_date'), '%Y-%m-%d').date()
                Rate.create(facility_id, payer_id, rate_type, rate_data, effective_date)

            elif rate_type == Rate.MEDICAID_WI:
                # Expected columns: per_diem_rate OR component rates
                for row in csv_reader:
                    if 'per_diem_rate' in row:
                        rate_data = {'per_diem_rate': float(row['per_diem_rate'])}
                    else:
                        rate_data = {
                            'component_nursing': float(row['component_nursing']),
                            'component_therapy': float(row['component_therapy']),
                            'component_room': float(row['component_room'])
                        }

                    effective_date = datetime.strptime(row.get('effective_date', request.form.get('effective_date')), '%Y-%m-%d').date()
                    Rate.create(facility_id, payer_id, rate_type, rate_data, effective_date)

            elif rate_type == Rate.FAMILY_CARE_WI:
                # Expected columns: nursing_group, nta_score_range, rate
                nursing_matrix = {}
                nta_matrix = {}

                for row in csv_reader:
                    if 'nursing_group' in row:
                        nursing_matrix[row['nursing_group']] = float(row['rate'])
                    elif 'nta_score_range' in row:
                        nta_matrix[row['nta_score_range']] = float(row['rate'])

                rate_data = {'nursing_matrix': nursing_matrix, 'nta_matrix': nta_matrix}
                effective_date = datetime.strptime(request.form.get('effective_date'), '%Y-%m-%d').date()
                Rate.create(facility_id, payer_id, rate_type, rate_data, effective_date)

            # HIPAA Audit Log: Rate upload
            log_audit_event(
                action='rates_uploaded',
                resource_type='rate',
                resource_id=facility_id,  # Use facility as context
                changes={'facility_id': facility_id, 'payer_id': payer_id, 'rate_type': rate_type}
            )

            flash('Rates uploaded successfully!', 'success')
            return redirect(url_for('admin.rates', facility_id=facility_id))

        except Exception as e:
            flash(f'Error uploading rates: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()

    current_user = User.get_by_id(session['user_id'])
    facilities = Facility.get_all(organization_id=current_user.organization_id)
    payers = Payer.get_all(organization_id=current_user.organization_id)

    return render_template('admin/upload_rates.html', facilities=facilities, payers=payers,
                          rate_types=Rate.RATE_TYPES)


# ===== COST MODEL MANAGEMENT =====

@admin_bp.route('/cost-models')
@admin_required
def cost_models():
    """List cost models."""
    current_user = User.get_by_id(session['user_id'])
    facility_id = request.args.get('facility_id', type=int)

    if facility_id:
        facility = Facility.get_by_id(facility_id)
        cost_models_list = CostModel.get_all_for_facility(facility_id)
    else:
        facility = None
        cost_models_list = []

    facilities = Facility.get_all(organization_id=current_user.organization_id)

    return render_template('admin/cost_models.html', cost_models=cost_models_list,
                          facilities=facilities, selected_facility=facility)


@admin_bp.route('/cost-models/new', methods=['GET', 'POST'])
@admin_required
def new_cost_model():
    """Create new cost model."""
    if request.method == 'POST':
        facility_id = int(request.form.get('facility_id'))
        acuity_band = request.form.get('acuity_band')
        nursing_hours = float(request.form.get('nursing_hours'))
        hourly_rate = float(request.form.get('hourly_rate'))
        supply_cost = float(request.form.get('supply_cost', 0))
        pharmacy_addon = float(request.form.get('pharmacy_addon', 0))
        transport_cost = float(request.form.get('transport_cost', 0))

        try:
            cost_model = CostModel.create(
                facility_id, acuity_band, nursing_hours, hourly_rate,
                supply_cost, pharmacy_addon, transport_cost
            )

            # HIPAA Audit Log: Cost model creation
            log_audit_event(
                action='cost_model_created',
                resource_type='cost_model',
                resource_id=cost_model.id,
                changes={'new': cost_model.to_dict()}
            )

            flash(f'Cost model for {acuity_band} acuity created successfully!', 'success')
            return redirect(url_for('admin.cost_models', facility_id=facility_id))
        except Exception as e:
            flash(f'Error creating cost model: {str(e)}', 'danger')

    current_user = User.get_by_id(session['user_id'])
    facilities = Facility.get_all(organization_id=current_user.organization_id)
    return render_template('admin/cost_model_form.html', cost_model=None,
                          facilities=facilities, acuity_bands=CostModel.ACUITY_BANDS)


@admin_bp.route('/cost-models/<int:cost_model_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_cost_model(cost_model_id):
    """Edit cost model."""
    cost_model = CostModel.get_by_id(cost_model_id)

    if not cost_model:
        flash('Cost model not found.', 'danger')
        return redirect(url_for('admin.cost_models'))

    if request.method == 'POST':
        nursing_hours = float(request.form.get('nursing_hours'))
        hourly_rate = float(request.form.get('hourly_rate'))
        supply_cost = float(request.form.get('supply_cost', 0))
        pharmacy_addon = float(request.form.get('pharmacy_addon', 0))
        transport_cost = float(request.form.get('transport_cost', 0))

        try:
            # Capture old values before update
            old_data = cost_model.to_dict()

            cost_model.update(nursing_hours, hourly_rate, supply_cost, pharmacy_addon, transport_cost)

            # HIPAA Audit Log: Cost model update
            log_audit_event(
                action='cost_model_updated',
                resource_type='cost_model',
                resource_id=cost_model.id,
                changes={'old': old_data, 'new': cost_model.to_dict()}
            )

            flash('Cost model updated successfully!', 'success')
            return redirect(url_for('admin.cost_models', facility_id=cost_model.facility_id))
        except Exception as e:
            flash(f'Error updating cost model: {str(e)}', 'danger')

    current_user = User.get_by_id(session['user_id'])
    facilities = Facility.get_all(organization_id=current_user.organization_id)
    return render_template('admin/cost_model_form.html', cost_model=cost_model,
                          facilities=facilities, acuity_bands=CostModel.ACUITY_BANDS)


# ===== USER MANAGEMENT =====

@admin_bp.route('/users')
@admin_required
def users():
    """List all users."""
    current_user = User.get_by_id(session['user_id'])
    users_list = User.get_all(organization_id=current_user.organization_id)
    return render_template('admin/users.html', users=users_list)


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status."""
    user = User.get_by_id(user_id)

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        # Capture action for audit log
        action = 'user_deactivated' if user.is_active else 'user_activated'
        old_status = user.is_active

        if user.is_active:
            user.deactivate()
            flash(f'User {user.email} deactivated.', 'success')
        else:
            user.activate()
            flash(f'User {user.email} activated.', 'success')

        # HIPAA Audit Log: User status change
        log_audit_event(
            action=action,
            resource_type='user',
            resource_id=user.id,
            changes={'old_status': old_status, 'new_status': user.is_active, 'email': user.email}
        )
    except Exception as e:
        flash(f'Error toggling user status: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))
