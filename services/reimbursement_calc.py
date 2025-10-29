"""
Reimbursement calculator for all payer types.
Calculates projected revenue based on PDPM groups, rates, and LOS.
"""

from typing import Dict, Optional


class ReimbursementCalculator:
    """Calculator for projected reimbursement across all payer types."""

    # Variable Per Diem (VPD) adjustment schedule for Medicare FFS
    # Days 1-3 get 100% of therapy rates, then declining percentages
    VPD_SCHEDULE = {
        1: 1.00, 2: 1.00, 3: 1.00,
        4: 0.98, 5: 0.98, 6: 0.98,
        7: 0.95, 8: 0.95, 9: 0.95, 10: 0.95,
        11: 0.92, 12: 0.92, 13: 0.92, 14: 0.92,
        15: 0.88, 16: 0.88, 17: 0.88, 18: 0.88,
        19: 0.85, 20: 0.85,
        # After day 20, stays at 0.85
    }

    def calculate_medicare_ffs(self, pdpm_groups: Dict, rate_data: Dict,
                               los: int, wage_index: float = 1.0,
                               vbp_multiplier: float = 1.0) -> Dict[str, float]:
        """
        Calculate Medicare Fee-for-Service revenue using PDPM.

        Args:
            pdpm_groups: Dict with PT, OT, SLP, Nursing, NTA groups
            rate_data: Dict with component rates from database
            los: Length of stay in days
            wage_index: Facility wage index
            vbp_multiplier: SNF VBP performance multiplier

        Returns:
            Dict with component revenues and total
        """
        # Get base rates (per day, before wage index and VPD)
        pt_rate = rate_data.get('pt_component', 64.89)
        ot_rate = rate_data.get('ot_component', 64.38)
        slp_rate = rate_data.get('slp_component', 26.43)
        nursing_rate = rate_data.get('nursing_component', 105.81)
        nta_rate = rate_data.get('nta_component', 86.72)
        non_case_mix = rate_data.get('non_case_mix', 98.13)

        # Calculate PT revenue (with VPD schedule)
        pt_revenue = 0
        ot_revenue = 0
        slp_revenue = 0

        for day in range(1, los + 1):
            vpd_factor = self.VPD_SCHEDULE.get(day, 0.85)  # Default to 0.85 after day 20

            # PT, OT use VPD schedule
            pt_revenue += pt_rate * vpd_factor
            ot_revenue += ot_rate * vpd_factor

            # SLP uses VPD only if there's an SLP comorbidity
            if pdpm_groups.get('slp_group') != 'None':
                slp_revenue += slp_rate * vpd_factor

        # Nursing and NTA are per-diem (no VPD)
        nursing_revenue = nursing_rate * los
        nta_revenue = nta_rate * los
        non_case_mix_revenue = non_case_mix * los

        # Apply wage index to labor-related components (PT, OT, SLP, Nursing - 71.3% labor)
        labor_portion = 0.713
        therapy_total = pt_revenue + ot_revenue + slp_revenue + nursing_revenue
        wage_adjusted_therapy = (therapy_total * labor_portion * wage_index +
                                therapy_total * (1 - labor_portion))

        # Non-labor components (NTA, non-case-mix) don't get wage index
        total_revenue = wage_adjusted_therapy + nta_revenue + non_case_mix_revenue

        # Apply VBP multiplier (typically 0.98-1.02)
        total_revenue *= vbp_multiplier

        return {
            'pt_revenue': pt_revenue * labor_portion * wage_index + pt_revenue * (1 - labor_portion),
            'ot_revenue': ot_revenue * labor_portion * wage_index + ot_revenue * (1 - labor_portion),
            'slp_revenue': slp_revenue * labor_portion * wage_index + slp_revenue * (1 - labor_portion),
            'nursing_revenue': nursing_revenue * labor_portion * wage_index + nursing_revenue * (1 - labor_portion),
            'nta_revenue': nta_revenue,
            'non_case_mix_revenue': non_case_mix_revenue,
            'total_before_vbp': total_revenue / vbp_multiplier,
            'vbp_adjustment': total_revenue - (total_revenue / vbp_multiplier),
            'total_revenue': total_revenue,
            'per_diem_rate': total_revenue / los
        }

    def calculate_ma_commercial(self, contract_rates: Dict, los: int,
                                pdpm_groups: Optional[Dict] = None) -> Dict[str, float]:
        """
        Calculate Medicare Advantage / Commercial revenue.

        Args:
            contract_rates: Dict with contract rate structure
            los: Length of stay
            pdpm_groups: Optional PDPM groups (if contract uses PDPM mapping)

        Returns:
            Dict with revenue breakdown and total
        """
        contract_type = contract_rates.get('contract_type', 'per_diem')

        if contract_type == 'per_diem':
            # Simple per-diem with day tiers
            # Example: Days 1-30 = $450, 31-60 = $400, 61+ = $375
            day_tiers = contract_rates.get('day_tiers', {
                '1-30': 450.00,
                '31-60': 400.00,
                '61-100': 375.00
            })

            total_revenue = 0
            for day in range(1, los + 1):
                if day <= 30:
                    total_revenue += day_tiers.get('1-30', 450.00)
                elif day <= 60:
                    total_revenue += day_tiers.get('31-60', 400.00)
                else:
                    total_revenue += day_tiers.get('61-100', 375.00)

            return {
                'total_revenue': total_revenue,
                'per_diem_rate': total_revenue / los,
                'contract_type': 'per_diem'
            }

        elif contract_type == 'pdpm_mapped':
            # PDPM-based rates (usually a percentage of Medicare FFS)
            # Example: 95% of Medicare FFS rates
            multiplier = contract_rates.get('pdpm_multiplier', 0.95)

            # Calculate as Medicare FFS, then apply multiplier
            medicare_revenue = self.calculate_medicare_ffs(
                pdpm_groups,
                contract_rates,
                los,
                wage_index=1.0,  # MA plans often don't use wage index
                vbp_multiplier=1.0
            )

            total_revenue = medicare_revenue['total_revenue'] * multiplier

            return {
                'total_revenue': total_revenue,
                'per_diem_rate': total_revenue / los,
                'contract_type': 'pdpm_mapped',
                'base_medicare_revenue': medicare_revenue['total_revenue'],
                'multiplier': multiplier
            }

        else:
            raise ValueError(f"Unknown contract type: {contract_type}")

    def calculate_medicaid_wi(self, medicaid_rates: Dict, los: int) -> Dict[str, float]:
        """
        Calculate Wisconsin Medicaid revenue.

        Args:
            medicaid_rates: Dict with WI Medicaid rate structure
            los: Length of stay

        Returns:
            Dict with revenue breakdown and total
        """
        # Wisconsin Medicaid uses facility-specific per-diem or component rates
        # Check if it's per-diem or component-based
        if 'per_diem_rate' in medicaid_rates:
            # Simple per-diem
            per_diem = medicaid_rates['per_diem_rate']
            total_revenue = per_diem * los

            return {
                'total_revenue': total_revenue,
                'per_diem_rate': per_diem,
                'rate_type': 'per_diem'
            }
        else:
            # Component-based (Methods implementation)
            nursing_rate = medicaid_rates.get('component_nursing', 185.00)
            therapy_rate = medicaid_rates.get('component_therapy', 95.00)
            room_rate = medicaid_rates.get('component_room', 45.00)

            total_revenue = (nursing_rate + therapy_rate + room_rate) * los

            return {
                'nursing_revenue': nursing_rate * los,
                'therapy_revenue': therapy_rate * los,
                'room_revenue': room_rate * los,
                'total_revenue': total_revenue,
                'per_diem_rate': total_revenue / los,
                'rate_type': 'component'
            }

    def calculate_family_care_wi(self, mco_rates: Dict, pdpm_groups: Dict, los: int) -> Dict[str, float]:
        """
        Calculate Wisconsin Family Care MCO revenue.

        Args:
            mco_rates: Dict with MCO PDPM rate matrices
            pdpm_groups: Dict with PDPM groups
            los: Length of stay

        Returns:
            Dict with revenue breakdown and total
        """
        # Family Care uses PDPM matrices for Nursing and NTA
        nursing_group = pdpm_groups.get('nursing_group', 'LBS2')
        nta_score = pdpm_groups.get('nta_score', 0)

        # Get rate matrices
        nursing_matrix = mco_rates.get('nursing_matrix', {})
        nta_matrix = mco_rates.get('nta_matrix', {})

        # Default rates if not in matrix
        nursing_rate = nursing_matrix.get(nursing_group, 275.00)

        # NTA rates by score range
        if nta_score >= 12:
            nta_rate = nta_matrix.get('12+', 100.00)
        elif nta_score >= 6:
            nta_rate = nta_matrix.get('6-11', 85.00)
        else:
            nta_rate = nta_matrix.get('0-5', 70.00)

        total_revenue = (nursing_rate + nta_rate) * los

        return {
            'nursing_revenue': nursing_rate * los,
            'nta_revenue': nta_rate * los,
            'total_revenue': total_revenue,
            'per_diem_rate': total_revenue / los,
            'nursing_group': nursing_group,
            'nta_score': nta_score
        }

    def calculate_revenue(self, payer_type: str, rate_data: Dict,
                         pdpm_groups: Dict, los: int,
                         facility_data: Optional[Dict] = None) -> Dict[str, float]:
        """
        Unified method to calculate revenue for any payer type.

        Args:
            payer_type: Type of payer ('medicare_ffs', 'ma_commercial', 'medicaid_wi', 'family_care_wi')
            rate_data: Rate data from database
            pdpm_groups: PDPM classification results
            los: Length of stay
            facility_data: Optional facility data (wage index, VBP multiplier)

        Returns:
            Dict with revenue breakdown
        """
        facility_data = facility_data or {}

        if payer_type == 'medicare_ffs':
            return self.calculate_medicare_ffs(
                pdpm_groups,
                rate_data,
                los,
                wage_index=facility_data.get('wage_index', 1.0),
                vbp_multiplier=facility_data.get('vbp_multiplier', 1.0)
            )
        elif payer_type == 'ma_commercial':
            return self.calculate_ma_commercial(rate_data, los, pdpm_groups)
        elif payer_type == 'medicaid_wi':
            return self.calculate_medicaid_wi(rate_data, los)
        elif payer_type == 'family_care_wi':
            return self.calculate_family_care_wi(rate_data, pdpm_groups, los)
        else:
            raise ValueError(f"Unknown payer type: {payer_type}")


# Example usage
if __name__ == '__main__':
    calc = ReimbursementCalculator()

    # Test Medicare FFS calculation
    pdpm_groups = {
        'pt_group': 'TB',
        'ot_group': 'TB',
        'slp_group': 'None',
        'nursing_group': 'HBS1',
        'nta_score': 8
    }

    rate_data = {
        'pt_component': 64.89,
        'ot_component': 64.38,
        'slp_component': 26.43,
        'nursing_component': 105.81,
        'nta_component': 86.72,
        'non_case_mix': 98.13
    }

    result = calc.calculate_medicare_ffs(
        pdpm_groups,
        rate_data,
        los=15,
        wage_index=1.0234,
        vbp_multiplier=0.98
    )

    print("Medicare FFS Revenue Breakdown:")
    for key, value in result.items():
        print(f"  {key}: ${value:,.2f}")
