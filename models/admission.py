"""
Admission model for managing admission assessments and decisions.
"""

import json
from typing import Optional, List, Dict
from datetime import datetime
from config.database import db


class Admission:
    """Represents an admission assessment and decision."""

    # Recommendation constants
    ACCEPT = 'Accept'
    DEFER = 'Defer'
    DECLINE = 'Decline'

    RECOMMENDATIONS = [ACCEPT, DEFER, DECLINE]

    def __init__(self, id: Optional[int] = None, facility_id: Optional[int] = None,
                 payer_id: Optional[int] = None, patient_initials: Optional[str] = None,
                 uploaded_files: Optional[Dict] = None, extracted_data: Optional[Dict] = None,
                 pdpm_groups: Optional[Dict] = None, projected_revenue: Optional[float] = None,
                 projected_cost: Optional[float] = None, projected_los: Optional[int] = None,
                 margin_score: Optional[int] = None, recommendation: Optional[str] = None,
                 explanation: Optional[Dict] = None, actual_decision: Optional[str] = None,
                 decided_by: Optional[int] = None, decided_at: Optional[datetime] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.facility_id = facility_id
        self.payer_id = payer_id
        self.patient_initials = patient_initials
        self.uploaded_files = uploaded_files or {}
        self.extracted_data = extracted_data or {}
        self.pdpm_groups = pdpm_groups or {}
        self.projected_revenue = projected_revenue
        self.projected_cost = projected_cost
        self.projected_los = projected_los
        self.margin_score = margin_score
        self.recommendation = recommendation
        self.explanation = explanation or {}
        self.actual_decision = actual_decision
        self.decided_by = decided_by
        self.decided_at = decided_at
        self.created_at = created_at or datetime.now()

    @classmethod
    def create(cls, facility_id: int, payer_id: int, patient_initials: Optional[str] = None,
               uploaded_files: Optional[Dict] = None, extracted_data: Optional[Dict] = None,
               pdpm_groups: Optional[Dict] = None, projected_revenue: Optional[float] = None,
               projected_cost: Optional[float] = None, projected_los: Optional[int] = None,
               margin_score: Optional[int] = None, recommendation: Optional[str] = None,
               explanation: Optional[Dict] = None) -> 'Admission':
        """
        Create a new admission assessment.

        Args:
            facility_id: ID of the facility
            payer_id: ID of the payer
            patient_initials: Patient initials (PHI protection)
            uploaded_files: Dict of uploaded file paths
            extracted_data: Dict of extracted clinical data
            pdpm_groups: Dict of PDPM classification results
            projected_revenue: Projected revenue amount
            projected_cost: Projected cost amount
            projected_los: Projected length of stay
            margin_score: Calculated margin score (0-100)
            recommendation: System recommendation (Accept/Defer/Decline)
            explanation: Detailed explanation of the score

        Returns:
            Admission instance with assigned ID
        """
        uploaded_files_json = json.dumps(uploaded_files or {})
        extracted_data_json = json.dumps(extracted_data or {})
        pdpm_groups_json = json.dumps(pdpm_groups or {})
        explanation_json = json.dumps(explanation or {})

        query = """
            INSERT INTO admissions (
                facility_id, payer_id, patient_initials, uploaded_files, extracted_data,
                pdpm_groups, projected_revenue, projected_cost, projected_los,
                margin_score, recommendation, explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        admission_id = db.execute_query(
            query,
            (facility_id, payer_id, patient_initials, uploaded_files_json, extracted_data_json,
             pdpm_groups_json, projected_revenue, projected_cost, projected_los,
             margin_score, recommendation, explanation_json),
            fetch='none'
        )

        return cls(
            id=admission_id,
            facility_id=facility_id,
            payer_id=payer_id,
            patient_initials=patient_initials,
            uploaded_files=uploaded_files,
            extracted_data=extracted_data,
            pdpm_groups=pdpm_groups,
            projected_revenue=projected_revenue,
            projected_cost=projected_cost,
            projected_los=projected_los,
            margin_score=margin_score,
            recommendation=recommendation,
            explanation=explanation
        )

    @classmethod
    def get_by_id(cls, admission_id: int) -> Optional['Admission']:
        """Get admission by ID."""
        query = "SELECT * FROM admissions WHERE id = ?"
        result = db.execute_query(query, (admission_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_all_for_facility(cls, facility_id: int, limit: int = 100) -> List['Admission']:
        """Get all admissions for a facility."""
        query = """
            SELECT * FROM admissions
            WHERE facility_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        results = db.execute_query(query, (facility_id, limit))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def get_recent(cls, limit: int = 20) -> List['Admission']:
        """Get recent admissions across all facilities."""
        query = "SELECT * FROM admissions ORDER BY created_at DESC LIMIT ?"
        results = db.execute_query(query, (limit,))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def _from_db_row(cls, row) -> 'Admission':
        """Create Admission instance from database row."""
        uploaded_files = json.loads(row['uploaded_files']) if row['uploaded_files'] else {}
        extracted_data = json.loads(row['extracted_data']) if row['extracted_data'] else {}
        pdpm_groups = json.loads(row['pdpm_groups']) if row['pdpm_groups'] else {}
        explanation = json.loads(row['explanation']) if row['explanation'] else {}

        return cls(
            id=row['id'],
            facility_id=row['facility_id'],
            payer_id=row['payer_id'],
            patient_initials=row['patient_initials'],
            uploaded_files=uploaded_files,
            extracted_data=extracted_data,
            pdpm_groups=pdpm_groups,
            projected_revenue=row['projected_revenue'],
            projected_cost=row['projected_cost'],
            projected_los=row['projected_los'],
            margin_score=row['margin_score'],
            recommendation=row['recommendation'],
            explanation=explanation,
            actual_decision=row['actual_decision'],
            decided_by=row['decided_by'],
            decided_at=row['decided_at'],
            created_at=row['created_at']
        )

    def record_decision(self, decision: str, decided_by: int):
        """Record the actual decision made by staff."""
        if decision not in self.RECOMMENDATIONS:
            raise ValueError(f"Invalid decision. Must be one of: {self.RECOMMENDATIONS}")

        self.actual_decision = decision
        self.decided_by = decided_by
        self.decided_at = datetime.now()

        query = """
            UPDATE admissions
            SET actual_decision = ?, decided_by = ?, decided_at = ?
            WHERE id = ?
        """

        db.execute_query(
            query,
            (self.actual_decision, self.decided_by, self.decided_at, self.id),
            fetch='none'
        )

    def update_projections(self, projected_revenue: Optional[float] = None,
                          projected_cost: Optional[float] = None,
                          projected_los: Optional[int] = None,
                          margin_score: Optional[int] = None,
                          recommendation: Optional[str] = None,
                          explanation: Optional[Dict] = None):
        """Update admission projections (e.g., after adjusting parameters)."""
        if projected_revenue is not None:
            self.projected_revenue = projected_revenue
        if projected_cost is not None:
            self.projected_cost = projected_cost
        if projected_los is not None:
            self.projected_los = projected_los
        if margin_score is not None:
            self.margin_score = margin_score
        if recommendation is not None:
            self.recommendation = recommendation
        if explanation is not None:
            self.explanation = explanation

        explanation_json = json.dumps(self.explanation)

        query = """
            UPDATE admissions
            SET projected_revenue = ?, projected_cost = ?, projected_los = ?,
                margin_score = ?, recommendation = ?, explanation = ?
            WHERE id = ?
        """

        db.execute_query(
            query,
            (self.projected_revenue, self.projected_cost, self.projected_los,
             self.margin_score, self.recommendation, explanation_json, self.id),
            fetch='none'
        )

    def to_dict(self) -> Dict:
        """Convert admission to dictionary."""
        return {
            'id': self.id,
            'facility_id': self.facility_id,
            'payer_id': self.payer_id,
            'patient_initials': self.patient_initials,
            'uploaded_files': self.uploaded_files,
            'extracted_data': self.extracted_data,
            'pdpm_groups': self.pdpm_groups,
            'projected_revenue': self.projected_revenue,
            'projected_cost': self.projected_cost,
            'projected_los': self.projected_los,
            'margin_score': self.margin_score,
            'recommendation': self.recommendation,
            'explanation': self.explanation,
            'actual_decision': self.actual_decision,
            'decided_by': self.decided_by,
            'decided_at': str(self.decided_at) if self.decided_at else None,
            'created_at': str(self.created_at) if self.created_at else None
        }

    def __repr__(self):
        return f"<Admission {self.id}: {self.patient_initials or 'Unknown'}, Score {self.margin_score}, {self.recommendation}>"
