"""
Celery tasks for async admission processing.
Moves document parsing and analysis to background workers.
"""

from celery_worker import celery_app
from services.document_parser import DocumentParser
from services.pdpm_classifier import PDPMClassifier
from services.reimbursement_calc import ReimbursementCalculator
from services.cost_estimator import CostEstimator
from services.scoring_engine import ScoringEngine
from models.admission import Admission
from models.facility import Facility
from models.payer import Payer
from models.rates import Rate
from models.cost_model import CostModel
from services.file_storage import FileStorage
import json


@celery_app.task(bind=True, name='tasks.process_admission')
def process_admission_async(self, admission_data):
    """
    Process an admission asynchronously in the background.

    Args:
        self: Celery task instance (for progress updates)
        admission_data: Dict containing:
            - facility_id: int
            - payer_id: int
            - patient_initials: str
            - file_keys: list of storage keys for uploaded files
            - estimated_los: int
            - auth_status: str
            - current_census_pct: float

    Returns:
        Dict with admission_id and processing results
    """
    try:
        # Update task state: Parsing documents
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 5, 'status': 'Parsing documents...'}
        )

        # Initialize services
        file_storage = FileStorage()
        parser = DocumentParser()
        classifier = PDPMClassifier()
        reimb_calc = ReimbursementCalculator()
        cost_est = CostEstimator()
        scorer = ScoringEngine()

        # Step 1: Parse and extract clinical features from documents
        all_extracted_data = {}
        for file_key in admission_data['file_keys']:
            try:
                # Get file content from storage
                file_content = file_storage.get_file(file_key)

                # For now, we need to save temp file for parser
                # TODO: Refactor parser to accept bytes directly
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name

                extracted = parser.parse_and_extract(tmp_path)
                all_extracted_data.update(extracted)

                # Clean up temp file
                os.unlink(tmp_path)

            except Exception as e:
                # Log error but continue with other files
                print(f"Error parsing {file_key}: {str(e)}")

        if not all_extracted_data:
            raise Exception("Failed to extract clinical data from documents")

        # Use estimated_los if not extracted
        if not all_extracted_data.get('estimated_los'):
            all_extracted_data['estimated_los'] = admission_data['estimated_los']

        # Update task state: Classifying PDPM groups
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 5, 'status': 'Classifying PDPM groups...'}
        )

        # Step 2: Classify into PDPM groups
        pdpm_groups = classifier.classify_patient(all_extracted_data)

        # Update task state: Calculating reimbursement
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 5, 'status': 'Calculating reimbursement...'}
        )

        # Step 3: Get facility and payer data
        facility = Facility.get_by_id(admission_data['facility_id'])
        payer = Payer.get_by_id(admission_data['payer_id'])
        rate = Rate.get_active_rate(admission_data['facility_id'], admission_data['payer_id'])

        if not rate:
            raise Exception(f"No active rate found for {facility.name} and {payer.type}")

        # Step 4: Calculate projected reimbursement
        projected_revenue = reimb_calc.calculate_reimbursement(
            pdpm_groups=pdpm_groups,
            rate=rate,
            los=all_extracted_data['estimated_los'],
            facility=facility,
            payer=payer
        )

        # Update task state: Estimating costs
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 5, 'status': 'Estimating costs...'}
        )

        # Step 5: Estimate costs
        cost_model = CostModel.get_by_facility(admission_data['facility_id'])
        projected_cost, cost_breakdown = cost_est.estimate_cost(
            extracted_data=all_extracted_data,
            pdpm_groups=pdpm_groups,
            los=all_extracted_data['estimated_los'],
            cost_model=cost_model,
            facility=facility
        )

        # Update task state: Calculating score
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 5, 'status': 'Calculating margin score...'}
        )

        # Step 6: Calculate margin score and recommendation
        margin_score, recommendation, explanation = scorer.calculate_score(
            projected_revenue=projected_revenue,
            projected_cost=projected_cost,
            pdpm_groups=pdpm_groups,
            extracted_data=all_extracted_data,
            current_census_pct=admission_data['current_census_pct'],
            auth_status=admission_data['auth_status']
        )

        # Step 7: Create admission record
        admission = Admission.create(
            facility_id=admission_data['facility_id'],
            payer_id=admission_data['payer_id'],
            patient_initials=admission_data['patient_initials'],
            uploaded_files=json.dumps(admission_data['file_keys']),
            extracted_data=json.dumps(all_extracted_data),
            pdpm_groups=json.dumps(pdpm_groups),
            projected_revenue=projected_revenue,
            projected_cost=projected_cost,
            projected_los=all_extracted_data['estimated_los'],
            margin_score=margin_score,
            recommendation=recommendation,
            explanation=json.dumps(explanation)
        )

        return {
            'admission_id': admission.id,
            'margin_score': margin_score,
            'recommendation': recommendation,
            'projected_revenue': projected_revenue,
            'projected_cost': projected_cost,
            'status': 'completed'
        }

    except Exception as e:
        # Task failed
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
