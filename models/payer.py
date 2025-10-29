"""
Payer model for managing insurance payer data.
"""

from typing import Optional, List, Dict
from config.database import db


class Payer:
    """Represents an insurance payer (Medicare, Medicaid, MA, etc.)."""

    # Payer type constants
    MEDICARE_FFS = 'Medicare FFS'
    MEDICARE_ADVANTAGE = 'Medicare Advantage'
    MEDICAID_FFS = 'Medicaid FFS'
    FAMILY_CARE = 'Family Care'
    COMMERCIAL = 'Commercial'

    PAYER_TYPES = [MEDICARE_FFS, MEDICARE_ADVANTAGE, MEDICAID_FFS, FAMILY_CARE, COMMERCIAL]

    def __init__(self, id: Optional[int] = None, type: str = '', plan_name: Optional[str] = None,
                 network_status: str = 'in_network'):
        self.id = id
        self.type = type
        self.plan_name = plan_name
        self.network_status = network_status

    @classmethod
    def create(cls, type: str, plan_name: Optional[str] = None,
               network_status: str = 'in_network') -> 'Payer':
        """
        Create a new payer.

        Args:
            type: Payer type (use constants like Payer.MEDICARE_FFS)
            plan_name: Name of specific plan (for MA, Commercial)
            network_status: 'in_network', 'out_of_network', 'single_case'

        Returns:
            Payer instance with assigned ID
        """
        if type not in cls.PAYER_TYPES:
            raise ValueError(f"Invalid payer type. Must be one of: {cls.PAYER_TYPES}")

        query = """
            INSERT INTO payers (type, plan_name, network_status)
            VALUES (?, ?, ?)
        """

        payer_id = db.execute_query(
            query,
            (type, plan_name, network_status),
            fetch='none'
        )

        return cls(id=payer_id, type=type, plan_name=plan_name, network_status=network_status)

    @classmethod
    def get_by_id(cls, payer_id: int) -> Optional['Payer']:
        """Get payer by ID."""
        query = "SELECT * FROM payers WHERE id = ?"
        result = db.execute_query(query, (payer_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_all(cls, type: Optional[str] = None) -> List['Payer']:
        """
        Get all payers, optionally filtered by type.

        Args:
            type: Optional payer type to filter by

        Returns:
            List of Payer instances
        """
        if type:
            query = "SELECT * FROM payers WHERE type = ? ORDER BY plan_name"
            results = db.execute_query(query, (type,))
        else:
            query = "SELECT * FROM payers ORDER BY type, plan_name"
            results = db.execute_query(query)

        return [cls._from_db_row(row) for row in results]

    @classmethod
    def get_by_type_and_plan(cls, type: str, plan_name: Optional[str] = None) -> Optional['Payer']:
        """Get payer by type and optional plan name."""
        if plan_name:
            query = "SELECT * FROM payers WHERE type = ? AND plan_name = ?"
            result = db.execute_query(query, (type, plan_name), fetch='one')
        else:
            query = "SELECT * FROM payers WHERE type = ? AND plan_name IS NULL"
            result = db.execute_query(query, (type,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def _from_db_row(cls, row) -> 'Payer':
        """Create Payer instance from database row."""
        return cls(
            id=row['id'],
            type=row['type'],
            plan_name=row['plan_name'],
            network_status=row['network_status']
        )

    def update(self, type: Optional[str] = None, plan_name: Optional[str] = None,
               network_status: Optional[str] = None):
        """Update payer information."""
        if type is not None:
            if type not in self.PAYER_TYPES:
                raise ValueError(f"Invalid payer type. Must be one of: {self.PAYER_TYPES}")
            self.type = type
        if plan_name is not None:
            self.plan_name = plan_name
        if network_status is not None:
            self.network_status = network_status

        query = """
            UPDATE payers
            SET type = ?, plan_name = ?, network_status = ?
            WHERE id = ?
        """

        db.execute_query(
            query,
            (self.type, self.plan_name, self.network_status, self.id),
            fetch='none'
        )

    def delete(self):
        """Delete payer."""
        query = "DELETE FROM payers WHERE id = ?"
        db.execute_query(query, (self.id,), fetch='none')

    def to_dict(self) -> Dict:
        """Convert payer to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'plan_name': self.plan_name,
            'network_status': self.network_status
        }

    def get_display_name(self) -> str:
        """Get human-readable payer name."""
        if self.plan_name:
            return f"{self.type} - {self.plan_name}"
        return self.type

    def __repr__(self):
        return f"<Payer {self.id}: {self.get_display_name()}>"
