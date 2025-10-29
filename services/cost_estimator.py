"""
Cost estimator service for projecting SNF costs.
Estimates nursing, supplies, pharmacy, and other costs based on patient acuity and services.
"""

from typing import Dict, Optional


class CostEstimator:
    """Estimator for projected costs per admission."""

    # Denial risk probabilities by payer type and auth status
    DENIAL_RISK = {
        'medicare_ffs': {
            'granted': 0.02,  # 2% denial risk with pre-auth
            'pending': 0.15,  # 15% denial risk pending auth
            'unknown': 0.25   # 25% denial risk no auth
        },
        'ma_commercial': {
            'granted': 0.05,
            'pending': 0.20,
            'unknown': 0.35
        },
        'medicaid_wi': {
            'granted': 0.03,
            'pending': 0.10,
            'unknown': 0.15
        },
        'family_care_wi': {
            'granted': 0.03,
            'pending': 0.12,
            'unknown': 0.18
        }
    }

    def estimate_nursing_cost(self, acuity_band: str, nursing_hours: float,
                             hourly_rate: float, los: int) -> Dict[str, float]:
        """
        Estimate nursing cost based on acuity and staffing hours.

        Args:
            acuity_band: Patient acuity level ('low', 'medium', 'high', 'complex')
            nursing_hours: Average nursing hours per day for this acuity
            hourly_rate: Loaded hourly wage rate (includes benefits)
            los: Length of stay

        Returns:
            Dict with nursing cost breakdown
        """
        daily_nursing_cost = nursing_hours * hourly_rate
        total_nursing_cost = daily_nursing_cost * los

        return {
            'nursing_hours_per_day': nursing_hours,
            'hourly_rate': hourly_rate,
            'daily_nursing_cost': daily_nursing_cost,
            'total_nursing_cost': total_nursing_cost,
            'acuity_band': acuity_band
        }

    def estimate_supply_cost(self, acuity_band: str, base_supply_cost: float,
                            los: int, special_services: Optional[Dict] = None) -> Dict[str, float]:
        """
        Estimate supply costs including special equipment/services.

        Args:
            acuity_band: Patient acuity level
            base_supply_cost: Base supply cost per day
            los: Length of stay
            special_services: Dict of special services needed

        Returns:
            Dict with supply cost breakdown
        """
        special_services = special_services or {}

        daily_supply_cost = base_supply_cost
        supply_breakdown = {'base_supplies': base_supply_cost}

        # Add special service supply costs
        if special_services.get('wound_vac'):
            wound_vac_cost = 75.00  # Per day
            daily_supply_cost += wound_vac_cost
            supply_breakdown['wound_vac'] = wound_vac_cost

        if special_services.get('oxygen'):
            oxygen_cost = 25.00  # Per day
            daily_supply_cost += oxygen_cost
            supply_breakdown['oxygen'] = oxygen_cost

        if special_services.get('feeding_tube'):
            feeding_tube_cost = 40.00  # Per day
            daily_supply_cost += feeding_tube_cost
            supply_breakdown['feeding_tube'] = feeding_tube_cost

        total_supply_cost = daily_supply_cost * los

        return {
            'daily_supply_cost': daily_supply_cost,
            'total_supply_cost': total_supply_cost,
            'breakdown': supply_breakdown
        }

    def estimate_pharmacy_cost(self, special_services: Optional[Dict] = None,
                              los: int = 15) -> Dict[str, float]:
        """
        Estimate pharmacy costs for IV antibiotics, wound care, etc.

        Args:
            special_services: Dict of special services needed
            los: Length of stay

        Returns:
            Dict with pharmacy cost breakdown
        """
        special_services = special_services or {}

        daily_pharmacy_cost = 0
        pharmacy_breakdown = {}

        if special_services.get('iv_abx'):
            iv_abx_cost = 150.00  # Per day for IV antibiotics
            daily_pharmacy_cost += iv_abx_cost
            pharmacy_breakdown['iv_antibiotics'] = iv_abx_cost

        if special_services.get('wound_vac'):
            # Additional wound care medications
            wound_meds_cost = 50.00  # Per day
            daily_pharmacy_cost += wound_meds_cost
            pharmacy_breakdown['wound_medications'] = wound_meds_cost

        # Base medication cost for all patients
        base_meds_cost = 30.00  # Per day
        daily_pharmacy_cost += base_meds_cost
        pharmacy_breakdown['base_medications'] = base_meds_cost

        total_pharmacy_cost = daily_pharmacy_cost * los

        return {
            'daily_pharmacy_cost': daily_pharmacy_cost,
            'total_pharmacy_cost': total_pharmacy_cost,
            'breakdown': pharmacy_breakdown
        }

    def estimate_transport_cost(self, needs_transport: bool = False,
                               transport_type: str = 'wheelchair_van') -> float:
        """
        Estimate one-time transport cost (ambulance or wheelchair van).

        Args:
            needs_transport: Whether transport is needed
            transport_type: 'ambulance' or 'wheelchair_van'

        Returns:
            Transport cost (one-time)
        """
        if not needs_transport:
            return 0.0

        transport_costs = {
            'ambulance': 500.00,
            'wheelchair_van': 150.00
        }

        return transport_costs.get(transport_type, 150.00)

    def estimate_denial_loss(self, projected_revenue: float, payer_type: str,
                            auth_status: str = 'unknown') -> Dict[str, float]:
        """
        Estimate expected loss from potential denials.

        Args:
            projected_revenue: Total projected revenue
            payer_type: Type of payer
            auth_status: 'granted', 'pending', or 'unknown'

        Returns:
            Dict with denial risk analysis
        """
        denial_probability = self.DENIAL_RISK.get(payer_type, {}).get(auth_status, 0.25)

        # Assume average denial results in 30% revenue loss (partial denials common)
        avg_denial_loss_pct = 0.30
        expected_loss = projected_revenue * denial_probability * avg_denial_loss_pct

        return {
            'denial_probability': denial_probability,
            'avg_denial_loss_percentage': avg_denial_loss_pct,
            'expected_denial_loss': expected_loss,
            'revenue_at_risk': projected_revenue * avg_denial_loss_pct
        }

    def estimate_total_cost(self, cost_model_data: Dict, los: int,
                           special_services: Optional[Dict] = None,
                           needs_transport: bool = False,
                           projected_revenue: float = 0,
                           payer_type: str = 'medicare_ffs',
                           auth_status: str = 'unknown') -> Dict:
        """
        Estimate total cost for an admission.

        Args:
            cost_model_data: Cost model data from database (nursing hours, rates, etc.)
            los: Length of stay
            special_services: Dict of special services needed
            needs_transport: Whether transport is needed
            projected_revenue: Projected revenue (for denial risk calculation)
            payer_type: Type of payer
            auth_status: Authorization status

        Returns:
            Dict with comprehensive cost breakdown
        """
        special_services = special_services or {}

        # Get cost model parameters
        acuity_band = cost_model_data.get('acuity_band', 'medium')
        nursing_hours = cost_model_data.get('nursing_hours', 4.0)
        hourly_rate = cost_model_data.get('hourly_rate', 35.00)
        supply_cost = cost_model_data.get('supply_cost', 50.00)

        # Calculate component costs
        nursing = self.estimate_nursing_cost(acuity_band, nursing_hours, hourly_rate, los)
        supplies = self.estimate_supply_cost(acuity_band, supply_cost, los, special_services)
        pharmacy = self.estimate_pharmacy_cost(special_services, los)
        transport = self.estimate_transport_cost(needs_transport)

        # Calculate denial risk
        denial = self.estimate_denial_loss(projected_revenue, payer_type, auth_status)

        # Total direct costs
        total_direct_cost = (
            nursing['total_nursing_cost'] +
            supplies['total_supply_cost'] +
            pharmacy['total_pharmacy_cost'] +
            transport
        )

        # Add overhead (typically 20-25% of direct costs)
        overhead_rate = 0.22
        overhead_cost = total_direct_cost * overhead_rate

        # Total cost including overhead and expected denial loss
        total_cost_with_risk = total_direct_cost + overhead_cost + denial['expected_denial_loss']

        return {
            'nursing': nursing,
            'supplies': supplies,
            'pharmacy': pharmacy,
            'transport_cost': transport,
            'total_direct_cost': total_direct_cost,
            'overhead_rate': overhead_rate,
            'overhead_cost': overhead_cost,
            'denial_risk': denial,
            'total_cost': total_cost_with_risk,
            'total_cost_no_risk': total_direct_cost + overhead_cost,
            'per_diem_cost': total_cost_with_risk / los,
            'los': los
        }


# Example usage
if __name__ == '__main__':
    estimator = CostEstimator()

    # Test cost estimation
    cost_model = {
        'acuity_band': 'high',
        'nursing_hours': 5.5,
        'hourly_rate': 38.00,
        'supply_cost': 60.00
    }

    special_services = {
        'iv_abx': True,
        'wound_vac': False,
        'oxygen': True
    }

    result = estimator.estimate_total_cost(
        cost_model_data=cost_model,
        los=15,
        special_services=special_services,
        needs_transport=True,
        projected_revenue=8500.00,
        payer_type='medicare_ffs',
        auth_status='granted'
    )

    print("Cost Estimation Results:")
    print(f"Total Cost: ${result['total_cost']:,.2f}")
    print(f"Per Diem Cost: ${result['per_diem_cost']:,.2f}")
    print(f"Nursing Cost: ${result['nursing']['total_nursing_cost']:,.2f}")
    print(f"Supply Cost: ${result['supplies']['total_supply_cost']:,.2f}")
    print(f"Pharmacy Cost: ${result['pharmacy']['total_pharmacy_cost']:,.2f}")
    print(f"Denial Risk Loss: ${result['denial_risk']['expected_denial_loss']:,.2f}")
