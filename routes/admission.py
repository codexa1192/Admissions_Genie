"""
Admission workflow routes for document upload, analysis, and decision tracking.
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename

from routes.auth import login_required
from models.admission import Admission
from models.facility import Facility
from models.payer import Payer
from models.rates import Rate
from models.cost_model import CostModel
from services.document_parser import DocumentParser
from services.pdpm_classifier import PDPMClassifier
from services.reimbursement_calc import ReimbursementCalculator
from services.cost_estimator import CostEstimator
from services.scoring_engine import ScoringEngine
from services.file_storage import FileStorage
from utils.audit_logger import log_audit_event
from config.settings import Config

admission_bp = Blueprint('admission', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@admission_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_admission():
    """New admission upload and analysis."""
    if request.method == 'POST':
        try:
            # Get form data
            facility_id = int(request.form.get('facility_id'))
            payer_id = int(request.form.get('payer_id'))
            patient_initials = request.form.get('patient_initials', '').strip().upper()[:3]
            estimated_los = int(request.form.get('estimated_los', Config.DEFAULT_LOS_ESTIMATE))
            auth_status = request.form.get('auth_status', 'unknown')
            current_census_pct = float(request.form.get('current_census_pct', 85.0))

            # Handle file uploads using FileStorage (S3 or local)
            file_storage = FileStorage()
            uploaded_files = {}
            saved_file_paths = []

            for field_name in ['discharge_summary', 'therapy_evals', 'nursing_notes']:
                files = request.files.getlist(field_name)
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        # Use FileStorage service (handles S3 or local storage)
                        file_key = file_storage.save_file(file, file.filename)
                        saved_file_paths.append(file_key)

                        if field_name not in uploaded_files:
                            uploaded_files[field_name] = []
                        uploaded_files[field_name].append(file_key)

            if not saved_file_paths:
                flash('Please upload at least one document (PDF, Word, or image file). Supported formats: .pdf, .docx, .doc, .png, .jpg, .jpeg', 'danger')
                return redirect(url_for('admission.new_admission'))

            # Initialize services
            parser = DocumentParser()
            classifier = PDPMClassifier()
            reimb_calc = ReimbursementCalculator()
            cost_est = CostEstimator()
            scorer = ScoringEngine()

            # Step 1: Parse and extract clinical features from documents
            all_extracted_data = {}
            for file_key in saved_file_paths:
                try:
                    # Get file from storage (S3, Azure, or local)
                    if file_key.startswith('s3://') or file_key.startswith('azure://'):
                        # For cloud storage, download to temp location for parsing
                        import tempfile
                        file_content = file_storage.get_file(file_key)
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp_file:
                            tmp_file.write(file_content)
                            temp_path = tmp_file.name
                        extracted = parser.parse_and_extract(temp_path)
                        os.unlink(temp_path)  # Clean up temp file
                    else:
                        # Local file, use directly
                        extracted = parser.parse_and_extract(file_key)

                    # Merge extracted data (later files can override earlier ones)
                    all_extracted_data.update(extracted)
                except Exception as e:
                    flash(f'Error parsing {file_key.split("/")[-1]}: {str(e)}', 'warning')

            if not all_extracted_data:
                flash('Failed to extract clinical data from documents. Please ensure the discharge summary contains patient diagnoses, functional status, and therapy needs. If the problem persists, check your Azure OpenAI configuration.', 'danger')
                return redirect(url_for('admission.new_admission'))

            # Use estimated_los if not extracted from documents
            if not all_extracted_data.get('estimated_los'):
                all_extracted_data['estimated_los'] = estimated_los

            # Step 2: Classify into PDPM groups
            pdpm_groups = classifier.classify_patient(all_extracted_data)

            # Step 3: Get facility and payer data
            facility = Facility.get_by_id(facility_id)
            payer = Payer.get_by_id(payer_id)

            if not facility or not payer:
                flash('Invalid facility or payer selection.', 'danger')
                return redirect(url_for('admission.new_admission'))

            # Step 4: Get rate data
            # Map payer type to rate type
            rate_type_mapping = {
                'Medicare FFS': Rate.MEDICARE_FFS,
                'Medicare Advantage': Rate.MA_COMMERCIAL,
                'Medicaid FFS': Rate.MEDICAID_WI,
                'Family Care': Rate.FAMILY_CARE_WI,
                'Commercial': Rate.MA_COMMERCIAL
            }

            payer_type = rate_type_mapping.get(payer.type, Rate.MEDICARE_FFS)
            rate = Rate.get_current_rate(facility_id, payer_id, payer_type)

            if not rate:
                flash(f'No rate configuration found for {payer.get_display_name()} at {facility.name}.', 'danger')
                return redirect(url_for('admission.new_admission'))

            # Step 5: Calculate reimbursement
            final_los = all_extracted_data.get('estimated_los', estimated_los)
            revenue_result = reimb_calc.calculate_revenue(
                payer_type,
                rate.rate_data,
                pdpm_groups,
                final_los,
                facility_data={'wage_index': facility.wage_index, 'vbp_multiplier': facility.vbp_multiplier}
            )

            projected_revenue = revenue_result['total_revenue']

            # Step 6: Get cost model and estimate costs
            # Determine acuity band based on PDPM groups
            nursing_group = pdpm_groups.get('nursing_group', 'LBS2')
            if nursing_group in ['ES1', 'ES2']:
                acuity_band = CostModel.COMPLEX
            elif nursing_group in ['HBS1', 'HBS2']:
                acuity_band = CostModel.HIGH
            elif nursing_group in ['LBS1']:
                acuity_band = CostModel.MEDIUM
            else:
                acuity_band = CostModel.LOW

            cost_model = CostModel.get_for_facility(facility_id, acuity_band)

            if not cost_model:
                # Use default cost model
                cost_model_data = {
                    'acuity_band': acuity_band,
                    'nursing_hours': 4.0,
                    'hourly_rate': 35.00,
                    'supply_cost': 50.00
                }
            else:
                cost_model_data = cost_model.to_dict()

            cost_result = cost_est.estimate_total_cost(
                cost_model_data,
                final_los,
                special_services=all_extracted_data.get('special_services', {}),
                needs_transport=True,  # Assume transport needed
                projected_revenue=projected_revenue,
                payer_type=payer_type,
                auth_status=auth_status
            )

            projected_cost = cost_result['total_cost']

            # Step 7: Calculate margin score and recommendation
            score_result = scorer.calculate_margin_score(
                projected_revenue,
                projected_cost,
                final_los,
                pdpm_groups,
                special_services=all_extracted_data.get('special_services', {}),
                denial_risk=cost_result['denial_risk']['denial_probability'],
                current_census_pct=current_census_pct,
                target_census_pct=90.0,  # Default target
                clinical_notes=all_extracted_data.get('clinical_notes', '')
            )

            margin_score = int(score_result['final_score'])
            recommendation = scorer.get_recommendation(margin_score)
            rationale = scorer.get_recommendation_rationale(margin_score, score_result)

            # Step 8: Save admission to database
            explanation = {
                'revenue_breakdown': revenue_result,
                'cost_breakdown': cost_result,
                'score_details': score_result,
                'rationale': rationale
            }

            admission = Admission.create(
                facility_id=facility_id,
                payer_id=payer_id,
                patient_initials=patient_initials,
                uploaded_files=uploaded_files,
                extracted_data=all_extracted_data,
                pdpm_groups=pdpm_groups,
                projected_revenue=projected_revenue,
                projected_cost=projected_cost,
                projected_los=final_los,
                margin_score=margin_score,
                recommendation=recommendation,
                explanation=explanation
            )

            # HIPAA audit log: admission created with PHI access
            log_audit_event(
                action='admission_created',
                resource_type='admission',
                resource_id=admission.id,
                changes={
                    'patient_initials': patient_initials,
                    'facility_id': facility_id,
                    'margin_score': margin_score,
                    'recommendation': recommendation
                }
            )

            flash('Admission analysis complete!', 'success')
            return redirect(url_for('admission.view_admission', admission_id=admission.id))

        except Exception as e:
            flash(f'Error processing admission: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
            return redirect(url_for('admission.new_admission'))

    # GET request - show upload form
    facilities = Facility.get_all()
    payers = Payer.get_all()

    return render_template('admission/new.html', facilities=facilities, payers=payers)


@admission_bp.route('/<int:admission_id>')
@login_required
def view_admission(admission_id):
    """View admission analysis results."""
    admission = Admission.get_by_id(admission_id)

    if not admission:
        flash('Admission not found.', 'danger')
        return redirect(url_for('dashboard'))

    # HIPAA audit log: PHI accessed
    log_audit_event(
        action='admission_viewed',
        resource_type='admission',
        resource_id=admission_id,
        changes={'patient_initials': admission.patient_initials}
    )

    # Get facility and payer details
    facility = Facility.get_by_id(admission.facility_id)
    payer = Payer.get_by_id(admission.payer_id)

    return render_template(
        'admission/view.html',
        admission=admission,
        facility=facility,
        payer=payer
    )


@admission_bp.route('/<int:admission_id>/decide', methods=['POST'])
@login_required
def record_decision(admission_id):
    """Record the actual decision made by staff."""
    admission = Admission.get_by_id(admission_id)

    if not admission:
        flash('Admission not found.', 'danger')
        return redirect(url_for('dashboard'))

    decision = request.form.get('decision')

    if decision not in Admission.RECOMMENDATIONS:
        flash('Invalid decision.', 'danger')
        return redirect(url_for('admission.view_admission', admission_id=admission_id))

    try:
        admission.record_decision(decision, session['user_id'])

        # HIPAA audit log: decision recorded
        log_audit_event(
            action='admission_decision_recorded',
            resource_type='admission',
            resource_id=admission_id,
            changes={
                'decision': decision,
                'patient_initials': admission.patient_initials
            }
        )

        flash(f'Decision recorded: {decision}', 'success')
    except Exception as e:
        flash(f'Error recording decision: {str(e)}', 'danger')

    return redirect(url_for('admission.view_admission', admission_id=admission_id))


@admission_bp.route('/history')
@login_required
def admission_history():
    """View admission history."""
    facility_id = session.get('facility_id')

    if facility_id:
        admissions = Admission.get_all_for_facility(facility_id, limit=50)
    else:
        admissions = Admission.get_recent(limit=50)

    # Get facility and payer details for each admission
    admission_details = []
    for admission in admissions:
        facility = Facility.get_by_id(admission.facility_id)
        payer = Payer.get_by_id(admission.payer_id)
        admission_details.append({
            'admission': admission,
            'facility': facility,
            'payer': payer
        })

    return render_template('admission/history.html', admission_details=admission_details)


@admission_bp.route('/<int:admission_id>/recalculate', methods=['POST'])
@login_required
def recalculate(admission_id):
    """Recalculate score with adjusted parameters (what-if analysis)."""
    admission = Admission.get_by_id(admission_id)

    if not admission:
        return jsonify({'error': 'Admission not found'}), 404

    try:
        # Get adjusted parameters from request
        adjusted_los = int(request.form.get('los', admission.projected_los))
        current_census_pct = float(request.form.get('census_pct', 85.0))

        # Recalculate with new parameters
        scorer = ScoringEngine()

        # Get original revenue and cost (scaled to new LOS)
        original_los = admission.projected_los
        per_diem_revenue = admission.projected_revenue / original_los
        per_diem_cost = admission.projected_cost / original_los

        new_revenue = per_diem_revenue * adjusted_los
        new_cost = per_diem_cost * adjusted_los

        # Recalculate score
        score_result = scorer.calculate_margin_score(
            new_revenue,
            new_cost,
            adjusted_los,
            admission.pdpm_groups,
            special_services=admission.extracted_data.get('special_services', {}),
            denial_risk=0.05,  # Use default
            current_census_pct=current_census_pct,
            target_census_pct=90.0,
            clinical_notes=admission.extracted_data.get('clinical_notes', '')
        )

        margin_score = int(score_result['final_score'])
        recommendation = scorer.get_recommendation(margin_score)

        return jsonify({
            'score': margin_score,
            'recommendation': recommendation,
            'revenue': new_revenue,
            'cost': new_cost,
            'margin': new_revenue - new_cost,
            'per_diem_margin': (new_revenue - new_cost) / adjusted_los
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
