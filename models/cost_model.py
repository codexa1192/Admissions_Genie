"""
Cost model for managing facility-specific cost estimates.
"""

from typing import Optional, List, Dict
from config.database import db


class CostModel:
    """Represents cost estimates for a facility by acuity band."""

    # Acuity band constants
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    COMPLEX = 'complex'

    ACUITY_BANDS = [LOW, MEDIUM, HIGH, COMPLEX]

    def __init__(self, id: Optional[int] = None, facility_id: Optional[int] = None,
                 acuity_band: str = '', nursing_hours: float = 0.0, hourly_rate: float = 0.0,
                 supply_cost: float = 0.0, pharmacy_addon: float = 0.0, transport_cost: float = 0.0):
        self.id = id
        self.facility_id = facility_id
        self.acuity_band = acuity_band
        self.nursing_hours = nursing_hours
        self.hourly_rate = hourly_rate
        self.supply_cost = supply_cost
        self.pharmacy_addon = pharmacy_addon
        self.transport_cost = transport_cost

    @classmethod
    def create(cls, facility_id: int, acuity_band: str, nursing_hours: float,
               hourly_rate: float, supply_cost: float = 0.0, pharmacy_addon: float = 0.0,
               transport_cost: float = 0.0) -> 'CostModel':
        """
        Create a new cost model.

        Args:
            facility_id: ID of the facility
            acuity_band: Acuity level (use CostModel constants)
            nursing_hours: Average nursing hours per day
            hourly_rate: Loaded hourly wage rate (includes benefits)
            supply_cost: Average supply cost per day
            pharmacy_addon: Additional pharmacy costs (IV ABX, wound vac, etc.)
            transport_cost: Transport cost (ambulance, wheelchair van)

        Returns:
            CostModel instance with assigned ID
        """
        if acuity_band not in cls.ACUITY_BANDS:
            raise ValueError(f"Invalid acuity band. Must be one of: {cls.ACUITY_BANDS}")

        query = """
            INSERT INTO cost_models (facility_id, acuity_band, nursing_hours, hourly_rate,
                                    supply_cost, pharmacy_addon, transport_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        cost_model_id = db.execute_query(
            query,
            (facility_id, acuity_band, nursing_hours, hourly_rate, supply_cost,
             pharmacy_addon, transport_cost),
            fetch='none'
        )

        return cls(
            id=cost_model_id,
            facility_id=facility_id,
            acuity_band=acuity_band,
            nursing_hours=nursing_hours,
            hourly_rate=hourly_rate,
            supply_cost=supply_cost,
            pharmacy_addon=pharmacy_addon,
            transport_cost=transport_cost
        )

    @classmethod
    def get_by_id(cls, cost_model_id: int) -> Optional['CostModel']:
        """Get cost model by ID."""
        query = "SELECT * FROM cost_models WHERE id = ?"
        result = db.execute_query(query, (cost_model_id,), fetch='one')

        if result:
            return cls._from_db_row(result)
        return None

    @classmethod
    def get_for_facility(cls, facility_id: int, acuity_band: Optional[str] = None) -> Optional['CostModel']:
        """
        Get cost model for a facility and optional acuity band.

        Args:
            facility_id: Facility ID
            acuity_band: Optional acuity band to filter by

        Returns:
            CostModel instance or None if not found
        """
        if acuity_band:
            query = "SELECT * FROM cost_models WHERE facility_id = ? AND acuity_band = ?"
            result = db.execute_query(query, (facility_id, acuity_band), fetch='one')
            if result:
                return cls._from_db_row(result)
        else:
            # Return all cost models for the facility
            query = "SELECT * FROM cost_models WHERE facility_id = ? ORDER BY acuity_band"
            results = db.execute_query(query, (facility_id,))
            return [cls._from_db_row(row) for row in results]

        return None

    @classmethod
    def get_all_for_facility(cls, facility_id: int) -> List['CostModel']:
        """Get all cost models for a facility."""
        query = "SELECT * FROM cost_models WHERE facility_id = ? ORDER BY acuity_band"
        results = db.execute_query(query, (facility_id,))
        return [cls._from_db_row(row) for row in results]

    @classmethod
    def _from_db_row(cls, row) -> 'CostModel':
        """Create CostModel instance from database row."""
        return cls(
            id=row['id'],
            facility_id=row['facility_id'],
            acuity_band=row['acuity_band'],
            nursing_hours=row['nursing_hours'],
            hourly_rate=row['hourly_rate'],
            supply_cost=row['supply_cost'],
            pharmacy_addon=row['pharmacy_addon'],
            transport_cost=row['transport_cost']
        )

    def update(self, nursing_hours: Optional[float] = None, hourly_rate: Optional[float] = None,
               supply_cost: Optional[float] = None, pharmacy_addon: Optional[float] = None,
               transport_cost: Optional[float] = None):
        """Update cost model information."""
        if nursing_hours is not None:
            self.nursing_hours = nursing_hours
        if hourly_rate is not None:
            self.hourly_rate = hourly_rate
        if supply_cost is not None:
            self.supply_cost = supply_cost
        if pharmacy_addon is not None:
            self.pharmacy_addon = pharmacy_addon
        if transport_cost is not None:
            self.transport_cost = transport_cost

        query = """
            UPDATE cost_models
            SET nursing_hours = ?, hourly_rate = ?, supply_cost = ?,
                pharmacy_addon = ?, transport_cost = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        db.execute_query(
            query,
            (self.nursing_hours, self.hourly_rate, self.supply_cost,
             self.pharmacy_addon, self.transport_cost, self.id),
            fetch='none'
        )

    def delete(self):
        """Delete cost model."""
        query = "DELETE FROM cost_models WHERE id = ?"
        db.execute_query(query, (self.id,), fetch='none')

    def calculate_daily_cost(self, has_iv_abx: bool = False, has_wound_vac: bool = False,
                            needs_transport: bool = False) -> float:
        """
        Calculate total daily cost based on this cost model and special services.

        Args:
            has_iv_abx: Whether patient needs IV antibiotics
            has_wound_vac: Whether patient needs wound vac
            needs_transport: Whether patient needs transport

        Returns:
            Total daily cost
        """
        base_nursing = self.nursing_hours * self.hourly_rate
        total_cost = base_nursing + self.supply_cost

        # Add pharmacy addons if needed
        if has_iv_abx or has_wound_vac:
            total_cost += self.pharmacy_addon

        # Add transport cost if needed (one-time cost)
        if needs_transport:
            total_cost += self.transport_cost

        return total_cost

    def to_dict(self) -> Dict:
        """Convert cost model to dictionary."""
        return {
            'id': self.id,
            'facility_id': self.facility_id,
            'acuity_band': self.acuity_band,
            'nursing_hours': self.nursing_hours,
            'hourly_rate': self.hourly_rate,
            'supply_cost': self.supply_cost,
            'pharmacy_addon': self.pharmacy_addon,
            'transport_cost': self.transport_cost
        }

    def __repr__(self):
        return f"<CostModel {self.id}: Facility {self.facility_id}, {self.acuity_band} acuity>"
