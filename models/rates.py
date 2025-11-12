"""
Rate model for managing facility-specific reimbursement rates.
"""

import json
from typing import Optional, List, Dict
from datetime import date
from config.database import db


class Rate:
    """Represents reimbursement rates for a facility and payer combination."""

    # Rate type constants
    MEDICARE_FFS = 'medicare_ffs'
    MA_COMMERCIAL = 'ma_commercial'
    MEDICAID_WI = 'medicaid_wi'
    FAMILY_CARE_WI = 'family_care_wi'

    RATE_TYPES = [MEDICARE_FFS, MA_COMMERCIAL, MEDICAID_WI, FAMILY_CARE_WI]

    def __init__(self, id: Optional[int] = None, organization_id: Optional[int] = None,
                 facility_id: Optional[int] = None, payer_id: Optional[int] = None,
                 payer_type: str = '', rate_data: Optional[Dict] = None,
                 effective_date: Optional[date] = None, end_date: Optional[date] = None):
        self.id = id
        self.organization_id = organization_id  # MULTI-TENANT
        self.facility_id = facility_id
        self.payer_id = payer_id
        self.payer_type = payer_type
        self.rate_data = rate_data or {}
        self.effective_date = effective_date
        self.end_date = end_date

    @classmethod
    def create(cls, organization_id: int, facility_id: int, payer_id: int, payer_type: str,
               rate_data: Dict, effective_date: date, end_date: Optional[date] = None) -> 'Rate':
        """
        Create a new rate record (MULTI-TENANT).

        Args:
            organization_id: Organization ID (REQUIRED for multi-tenancy)
            facility_id: ID of the facility
            payer_id: ID of the payer
            payer_type: Type of rate (use Rate constants)
            rate_data: Dictionary containing rate structure (varies by payer type)
            effective_date: When this rate becomes effective
            end_date: When this rate expires (None if current)

        Returns:
            Rate instance with assigned ID
        """
        if payer_type not in cls.RATE_TYPES:
            raise ValueError(f"Invalid payer type. Must be one of: {cls.RATE_TYPES}")

        rate_data_json = json.dumps(rate_data)

        query = """
            INSERT INTO rates (organization_id, facility_id, payer_id, payer_type, rate_data, effective_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        rate_id = db.execute_query(
            query,
            (organization_id, facility_id, payer_id, payer_type, rate_data_json, effective_date, end_date),
            fetch='none'
        )

        return cls(
            id=rate_id,
            organization_id=organization_id,
            facility_id=facility_id,
            payer_id=payer_id,
            payer_type=payer_type,
            rate_data=rate_data,
            effective_date=effective_date,
            end_date=end_date
        )

    @classmethod
    def get_by_id(cls, rate_id: int) -> Optional['Rate']:
        """Get rate by ID."""
        query = "SELECT * FROM rates WHERE id = ?"
        result = db.execute_query(query, (rate_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_current_rate(cls, facility_id: int, payer_id: int, payer_type: str,
                        as_of_date: Optional[date] = None) -> Optional['Rate']:
        """
        Get the current rate for a facility/payer combination.

        Args:
            facility_id: Facility ID
            payer_id: Payer ID
            payer_type: Rate type
            as_of_date: Date to check (defaults to today)

        Returns:
            Current Rate instance or None if no rate found
        """
        as_of_date = as_of_date or date.today()

        query = """
            SELECT * FROM rates
            WHERE facility_id = ? AND payer_id = ? AND payer_type = ?
              AND effective_date <= ?
              AND (end_date IS NULL OR end_date >= ?)
            ORDER BY effective_date DESC
            LIMIT 1
        """

        result = db.execute_query(
            query,
            (facility_id, payer_id, payer_type, as_of_date, as_of_date),
            fetch='one'
        )

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_all_for_facility(cls, facility_id: int, payer_type: Optional[str] = None) -> List['Rate']:
        """
        Get all rates for a facility, optionally filtered by payer type.

        Args:
            facility_id: Facility ID
            payer_type: Optional rate type to filter by

        Returns:
            List of Rate instances
        """
        if payer_type:
            query = """
                SELECT * FROM rates
                WHERE facility_id = ? AND payer_type = ?
                ORDER BY effective_date DESC
            """
            results = db.execute_query(query, (facility_id, payer_type))
        else:
            query = """
                SELECT * FROM rates
                WHERE facility_id = ?
                ORDER BY payer_type, effective_date DESC
            """
            results = db.execute_query(query, (facility_id,))

        return [cls._from_db_row(row) for row in results]

    @classmethod
    def _from_db_row(cls, row) -> 'Rate':
        """Create Rate instance from database row."""
        rate_data = json.loads(row['rate_data']) if row['rate_data'] else {}
        return cls(
            id=row['id'],
            organization_id=row['organization_id'],  # MULTI-TENANT
            facility_id=row['facility_id'],
            payer_id=row['payer_id'],
            payer_type=row['payer_type'],
            rate_data=rate_data,
            effective_date=row['effective_date'],
            end_date=row['end_date']
        )

    def update(self, rate_data: Optional[Dict] = None, effective_date: Optional[date] = None,
               end_date: Optional[date] = None):
        """Update rate information."""
        if rate_data is not None:
            self.rate_data = rate_data
        if effective_date is not None:
            self.effective_date = effective_date
        if end_date is not None:
            self.end_date = end_date

        rate_data_json = json.dumps(self.rate_data)

        query = """
            UPDATE rates
            SET rate_data = ?, effective_date = ?, end_date = ?
            WHERE id = ?
        """

        db.execute_query(
            query,
            (rate_data_json, self.effective_date, self.end_date, self.id),
            fetch='none'
        )

    def delete(self):
        """Delete rate."""
        query = "DELETE FROM rates WHERE id = ?"
        db.execute_query(query, (self.id,), fetch='none')

    def to_dict(self) -> Dict:
        """Convert rate to dictionary."""
        return {
            'id': self.id,
            'facility_id': self.facility_id,
            'payer_id': self.payer_id,
            'payer_type': self.payer_type,
            'rate_data': self.rate_data,
            'effective_date': str(self.effective_date) if self.effective_date else None,
            'end_date': str(self.end_date) if self.end_date else None
        }

    def __repr__(self):
        return f"<Rate {self.id}: Facility {self.facility_id}, Payer {self.payer_id}, Type {self.payer_type}>"
