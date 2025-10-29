"""
Scoring engine for calculating margin scores and generating recommendations.
Transparent, auditable scoring with adjustable business weights.
"""

from typing import Dict, Optional
from config.settings import Config


class ScoringEngine:
    """Engine for calculating admission margin scores (0-100) and recommendations."""

    def __init__(self, business_weights: Optional[Dict] = None):
        """
        Initialize scoring engine.

        Args:
            business_weights: Optional custom weights (defaults to Config.DEFAULT_BUSINESS_WEIGHTS)
        """
        self.weights = business_weights or Config.DEFAULT_BUSINESS_WEIGHTS.copy()
        self.thresholds = Config.SCORE_THRESHOLDS

    def calculate_base_margin(self, projected_revenue: float, projected_cost: float,
                             los: int) -> Dict[str, float]:
        """
        Calculate base financial margin metrics.

        Args:
            projected_revenue: Total projected revenue
            projected_cost: Total projected cost
            los: Length of stay

        Returns:
            Dict with margin calculations
        """
        total_margin = projected_revenue - projected_cost
        margin_percentage = (total_margin / projected_revenue * 100) if projected_revenue > 0 else 0
        per_diem_margin = total_margin / los if los > 0 else 0

        return {
            'total_margin': total_margin,
            'margin_percentage': margin_percentage,
            'per_diem_margin': per_diem_margin,
            'projected_revenue': projected_revenue,
            'projected_cost': projected_cost,
            'los': los
        }

    def normalize_margin_score(self, per_diem_margin: float) -> float:
        """
        Normalize per-diem margin to 0-100 scale.

        Uses a sigmoid-like curve:
        - $0/day margin = 50 points
        - $100/day margin = ~75 points
        - $200/day margin = ~85 points
        - $300/day margin = ~90 points
        - Negative margins scale down proportionally

        Args:
            per_diem_margin: Margin per day

        Returns:
            Normalized score (0-100)
        """
        # Normalization formula: 50 + (margin / (margin + 200)) * 50
        # This creates a curve where:
        # - Negative margins → 0-50
        # - Zero margin → 50
        # - Positive margins → 50-100 (asymptotically)

        if per_diem_margin >= 0:
            # Positive margin: 50-100 scale
            normalized = 50 + (per_diem_margin / (per_diem_margin + 200)) * 50
        else:
            # Negative margin: 0-50 scale (linear penalty)
            normalized = max(0, 50 + (per_diem_margin / 100) * 50)

        return min(100, max(0, normalized))

    def calculate_census_factor(self, current_census_pct: float = 85.0,
                                target_census_pct: float = 90.0) -> float:
        """
        Calculate census priority factor.

        If census is below target, admissions are more valuable.

        Args:
            current_census_pct: Current facility census percentage
            target_census_pct: Target census percentage

        Returns:
            Census factor (+10 to -10 points)
        """
        census_gap = target_census_pct - current_census_pct

        # Scale: -10 to +10 points
        # If 10% below target → +10 points
        # If at target → 0 points
        # If 10% above target → -10 points
        census_factor = min(10, max(-10, census_gap))

        return census_factor

    def calculate_complexity_penalty(self, pdpm_groups: Dict,
                                    special_services: Optional[Dict] = None) -> float:
        """
        Calculate penalty for care complexity.

        More complex patients require more resources and carry more risk.

        Args:
            pdpm_groups: PDPM classification results
            special_services: Dict of special services needed

        Returns:
            Complexity penalty (0-20 points)
        """
        special_services = special_services or {}
        penalty = 0

        # Complex PDPM groups
        if pdpm_groups.get('nursing_group') in ['ES1', 'ES2']:
            penalty += 5  # Extensive services add complexity

        # Special services penalties
        if special_services.get('dialysis'):
            penalty += 8  # Dialysis is very complex
        if special_services.get('trach'):
            penalty += 6  # Trach care is complex
        if special_services.get('wound_vac'):
            penalty += 4  # Wound vac adds complexity
        if special_services.get('iv_abx'):
            penalty += 3  # IV antibiotics add some complexity

        return min(20, penalty)

    def calculate_readmit_risk_penalty(self, clinical_notes: str = '',
                                      has_history: bool = False) -> float:
        """
        Calculate penalty for readmission risk.

        Args:
            clinical_notes: Clinical notes text
            has_history: Whether patient has prior readmission history

        Returns:
            Readmit risk penalty (0-10 points)
        """
        penalty = 0

        # Check for high-risk conditions in clinical notes
        high_risk_terms = ['falls risk', 'multiple readmissions', 'poor compliance',
                          'unstable', 'acute exacerbation']

        clinical_notes_lower = clinical_notes.lower()
        for term in high_risk_terms:
            if term in clinical_notes_lower:
                penalty += 2

        # Prior readmission history
        if has_history:
            penalty += 5

        return min(10, penalty)

    def calculate_margin_score(self, projected_revenue: float, projected_cost: float,
                              los: int, pdpm_groups: Dict,
                              special_services: Optional[Dict] = None,
                              denial_risk: float = 0.0,
                              current_census_pct: float = 85.0,
                              target_census_pct: float = 90.0,
                              clinical_notes: str = '') -> Dict:
        """
        Calculate comprehensive margin score (0-100) with all factors.

        Args:
            projected_revenue: Total projected revenue
            projected_cost: Total projected cost
            los: Length of stay
            pdpm_groups: PDPM classification
            special_services: Dict of special services
            denial_risk: Denial probability (0-1)
            current_census_pct: Current census percentage
            target_census_pct: Target census percentage
            clinical_notes: Clinical observation notes

        Returns:
            Dict with score and detailed explanation
        """
        # 1. Calculate base margin
        base_margin = self.calculate_base_margin(projected_revenue, projected_cost, los)
        per_diem_margin = base_margin['per_diem_margin']

        # 2. Normalize to base score (0-100)
        base_score = self.normalize_margin_score(per_diem_margin)

        # 3. Calculate adjustment factors
        census_factor = self.calculate_census_factor(current_census_pct, target_census_pct)
        complexity_penalty = self.calculate_complexity_penalty(pdpm_groups, special_services)
        readmit_penalty = self.calculate_readmit_risk_penalty(clinical_notes)

        # Denial risk penalty (scaled to max 15 points)
        denial_penalty = denial_risk * 100 * 0.15

        # 4. Apply business weights
        weighted_census = census_factor * self.weights['census']
        weighted_denial = denial_penalty * self.weights['denial_risk']
        weighted_complexity = complexity_penalty * self.weights['complexity']
        weighted_readmit = readmit_penalty * self.weights['readmit_risk']

        # 5. Calculate final score
        final_score = base_score + weighted_census - weighted_denial - weighted_complexity - weighted_readmit

        # Clamp to 0-100
        final_score = min(100, max(0, final_score))

        # 6. Generate explanation
        explanation = {
            'base_margin': base_margin,
            'base_score': base_score,
            'adjustments': {
                'census_factor': {
                    'raw_value': census_factor,
                    'weighted_value': weighted_census,
                    'weight': self.weights['census'],
                    'description': f'Census {current_census_pct:.0f}% vs target {target_census_pct:.0f}%'
                },
                'denial_risk': {
                    'raw_value': denial_penalty,
                    'weighted_value': -weighted_denial,
                    'weight': self.weights['denial_risk'],
                    'description': f'Denial risk {denial_risk*100:.1f}%'
                },
                'complexity': {
                    'raw_value': complexity_penalty,
                    'weighted_value': -weighted_complexity,
                    'weight': self.weights['complexity'],
                    'description': f'Care complexity penalty {complexity_penalty:.1f} points'
                },
                'readmit_risk': {
                    'raw_value': readmit_penalty,
                    'weighted_value': -weighted_readmit,
                    'weight': self.weights['readmit_risk'],
                    'description': f'Readmit risk penalty {readmit_penalty:.1f} points'
                }
            },
            'final_score': final_score
        }

        return explanation

    def get_recommendation(self, score: float) -> str:
        """
        Get recommendation based on score.

        Args:
            score: Margin score (0-100)

        Returns:
            Recommendation: 'Accept', 'Defer', or 'Decline'
        """
        if score >= self.thresholds['accept']:
            return 'Accept'
        elif score >= self.thresholds['defer']:
            return 'Defer'
        else:
            return 'Decline'

    def get_recommendation_rationale(self, score: float, explanation: Dict) -> str:
        """
        Get human-readable rationale for the recommendation.

        Args:
            score: Margin score
            explanation: Score explanation dict

        Returns:
            Rationale text
        """
        recommendation = self.get_recommendation(score)
        margin = explanation['base_margin']

        if recommendation == 'Accept':
            return (f"Strong financial margin of ${margin['per_diem_margin']:.2f}/day "
                   f"({margin['margin_percentage']:.1f}% margin rate). "
                   f"Projected net profit of ${margin['total_margin']:,.2f} over {margin['los']} days.")

        elif recommendation == 'Defer':
            return (f"Moderate margin of ${margin['per_diem_margin']:.2f}/day "
                   f"({margin['margin_percentage']:.1f}% margin rate). "
                   f"Consider negotiating rates or confirming authorization before accepting. "
                   f"Projected net profit of ${margin['total_margin']:,.2f} over {margin['los']} days.")

        else:  # Decline
            if margin['total_margin'] < 0:
                return (f"Negative margin of ${margin['per_diem_margin']:.2f}/day "
                       f"({margin['margin_percentage']:.1f}% margin rate). "
                       f"Projected loss of ${abs(margin['total_margin']):,.2f} over {margin['los']} days. "
                       f"Not financially viable without rate renegotiation.")
            else:
                return (f"Low margin of ${margin['per_diem_margin']:.2f}/day "
                       f"({margin['margin_percentage']:.1f}% margin rate). "
                       f"High complexity or denial risk reduces overall score. "
                       f"Consider only if census priority is critical.")


# Example usage
if __name__ == '__main__':
    engine = ScoringEngine()

    # Test scoring
    result = engine.calculate_margin_score(
        projected_revenue=8500.00,
        projected_cost=6200.00,
        los=15,
        pdpm_groups={'nursing_group': 'HBS1', 'pt_group': 'TB'},
        special_services={'iv_abx': True, 'oxygen': True},
        denial_risk=0.05,
        current_census_pct=82.0,
        target_census_pct=90.0,
        clinical_notes='Patient stable, low falls risk'
    )

    print("Margin Score Calculation:")
    print(f"Final Score: {result['final_score']:.1f}/100")
    print(f"Recommendation: {engine.get_recommendation(result['final_score'])}")
    print(f"Rationale: {engine.get_recommendation_rationale(result['final_score'], result)}")
    print(f"\nBase Margin: ${result['base_margin']['per_diem_margin']:.2f}/day")
    print(f"Adjustments:")
    for key, adj in result['adjustments'].items():
        print(f"  {key}: {adj['weighted_value']:+.1f} points ({adj['description']})")
