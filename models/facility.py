"""
Facility model for managing SNF facility data.
"""

import json
from typing import Optional, Dict, List
from config.database import db


class Facility:
    """Represents a Skilled Nursing Facility (SNF)."""

    def __init__(self, id: Optional[int] = None, name: str = '', wage_index: Optional[float] = None,
                 vbp_multiplier: Optional[float] = None, capabilities: Optional[Dict] = None):
        self.id = id
        self.name = name
        self.wage_index = wage_index or 1.0
        self.vbp_multiplier = vbp_multiplier or 1.0
        self.capabilities = capabilities or {}

    @classmethod
    def create(cls, name: str, wage_index: float = 1.0, vbp_multiplier: float = 1.0,
               capabilities: Optional[Dict] = None) -> 'Facility':
        """
        Create a new facility.

        Args:
            name: Facility name
            wage_index: Medicare wage index for the facility location
            vbp_multiplier: SNF VBP performance multiplier (default 1.0)
            capabilities: Dict of facility capabilities (e.g., {'dialysis': True, 'iv_abx': True})

        Returns:
            Facility instance with assigned ID
        """
        capabilities_json = json.dumps(capabilities or {})

        query = """
            INSERT INTO facilities (name, wage_index, vbp_multiplier, capabilities)
            VALUES (?, ?, ?, ?)
        """

        facility_id = db.execute_query(
            query,
            (name, wage_index, vbp_multiplier, capabilities_json),
            fetch='none'
        )

        return cls(id=facility_id, name=name, wage_index=wage_index,
                   vbp_multiplier=vbp_multiplier, capabilities=capabilities)

    @classmethod
    def get_by_id(cls, facility_id: int) -> Optional['Facility']:
        """Get facility by ID."""
        query = "SELECT * FROM facilities WHERE id = ?"
        result = db.execute_query(query, (facility_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_all(cls) -> List['Facility']:
        """Get all facilities."""
        query = "SELECT * FROM facilities ORDER BY name"
        results = db.execute_query(query)
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def _from_db_row(cls, row) -> 'Facility':
        """Create Facility instance from database row."""
        capabilities = json.loads(row['capabilities']) if row['capabilities'] else {}
        return cls(
            id=row['id'],
            name=row['name'],
            wage_index=row['wage_index'],
            vbp_multiplier=row['vbp_multiplier'],
            capabilities=capabilities
        )

    def update(self, name: Optional[str] = None, wage_index: Optional[float] = None,
               vbp_multiplier: Optional[float] = None, capabilities: Optional[Dict] = None):
        """Update facility information."""
        if name is not None:
            self.name = name
        if wage_index is not None:
            self.wage_index = wage_index
        if vbp_multiplier is not None:
            self.vbp_multiplier = vbp_multiplier
        if capabilities is not None:
            self.capabilities = capabilities

        capabilities_json = json.dumps(self.capabilities)

        query = """
            UPDATE facilities
            SET name = ?, wage_index = ?, vbp_multiplier = ?, capabilities = ?
            WHERE id = ?
        """

        db.execute_query(
            query,
            (self.name, self.wage_index, self.vbp_multiplier, capabilities_json, self.id),
            fetch='none'
        )

    def delete(self):
        """Delete facility (soft delete by preventing new admissions)."""
        # In production, you might want to soft-delete or archive instead
        query = "DELETE FROM facilities WHERE id = ?"
        db.execute_query(query, (self.id,), fetch='none')

    def has_capability(self, capability: str) -> bool:
        """Check if facility has a specific capability."""
        return self.capabilities.get(capability, False)

    def to_dict(self) -> Dict:
        """Convert facility to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'wage_index': self.wage_index,
            'vbp_multiplier': self.vbp_multiplier,
            'capabilities': self.capabilities
        }

    def __repr__(self):
        return f"<Facility {self.id}: {self.name}>"
