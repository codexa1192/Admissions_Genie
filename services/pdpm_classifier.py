"""
PDPM classifier service for mapping clinical data to PDPM payment groups.
Based on CMS PDPM guidelines and ICD-10 mappings.
"""

from typing import Dict, List, Optional


class PDPMClassifier:
    """Classifier for PDPM (Patient-Driven Payment Model) groups."""

    # PDPM Clinical Categories (simplified mapping for MVP)
    # In production, load this from CMS CSV files
    CLINICAL_CATEGORIES = {
        # Major Joint Replacement or Spinal Surgery
        'major_joint': ['Z96.6', 'M96.6', 'Z47.1', 'T84'],
        # Non-surgical orthopedic/musculoskeletal
        'non_surgical_ortho': ['M16', 'M17', 'M19', 'M25', 'M54', 'S72', 'S82'],
        # Acute infections
        'acute_infections': ['A40', 'A41', 'J15', 'J18', 'L03', 'N39.0'],
        # Cardiovascular/coagulations
        'cardiovascular': ['I50', 'I48', 'I21', 'I63', 'I25', 'I10'],
        # Pulmonary
        'pulmonary': ['J44', 'J96', 'J45', 'J81'],
        # Non-orthopedic surgery/acute neurologic
        'surgery_neuro': ['I60', 'I61', 'I62', 'G81', 'G83'],
    }

    # PT/OT Clinical Categories
    PT_OT_CATEGORIES = {
        'TA': ['major_joint'],  # Major Joint Replacement or Spinal Surgery
        'TB': ['non_surgical_ortho'],  # Non-surgical orthopedic
        'TC': ['acute_infections', 'surgery_neuro'],  # Acute infections, surgery
        'TD': ['cardiovascular', 'pulmonary'],  # Med management
        'TE': [],  # Other
    }

    # Nursing Clinical Categories (simplified)
    NURSING_CATEGORIES = {
        'ES1': [],  # Extensive Services Level 1 (very complex)
        'ES2': [],  # Extensive Services Level 2
        'HBS1': ['surgery_neuro', 'major_joint'],  # High Base Score 1
        'HBS2': ['cardiovascular', 'pulmonary'],  # High Base Score 2
        'LBS1': ['non_surgical_ortho'],  # Low Base Score 1
        'LBS2': ['acute_infections'],  # Low Base Score 2
    }

    # SLP Comorbidities (conditions requiring SLP)
    SLP_CONDITIONS = [
        'R13',  # Dysphagia
        'R47',  # Speech disturbances
        'R48',  # Symbolic dysfunctions
        'F80',  # Language disorders
        'I69',  # Sequelae of cerebrovascular disease
    ]

    # NTA (Non-Therapy Ancillary) Comorbidity Scores
    NTA_SCORES = {
        'pneumonia': 5,
        'septicemia': 6,
        'diabetes': 3,
        'copd': 4,
        'uti': 4,
        'chf': 5,
        'dialysis': 8,
        'hiv': 6,
        'multiple_sclerosis': 6,
        'parkinsons': 5,
        'hemiplegia': 6,
        'aphasia': 5,
        'malnutrition': 4,
        'depression': 3,
        'bipolar': 4,
        'schizophrenia': 4,
    }

    def classify_pt_ot_group(self, primary_diagnosis: str, comorbidities: List[str],
                             functional_score: Optional[int] = None) -> Dict[str, str]:
        """
        Classify PT and OT clinical groups.

        Args:
            primary_diagnosis: Primary ICD-10 code
            comorbidities: List of comorbidity ICD-10 codes
            functional_score: Optional functional assessment score

        Returns:
            Dict with 'pt_group' and 'ot_group' (usually the same)
        """
        all_codes = [primary_diagnosis] + comorbidities

        # Find matching clinical category
        clinical_category = self._get_clinical_category(all_codes)

        # Map to PT/OT group
        pt_group = 'TE'  # Default to TE (Other)
        for group, categories in self.PT_OT_CATEGORIES.items():
            if clinical_category in categories:
                pt_group = group
                break

        # PT and OT groups are typically the same
        return {
            'pt_group': pt_group,
            'ot_group': pt_group,
            'clinical_category': clinical_category or 'other'
        }

    def classify_nursing_group(self, primary_diagnosis: str, comorbidities: List[str],
                               adl_score: Optional[int] = None,
                               has_extensive_services: bool = False) -> str:
        """
        Classify Nursing clinical group.

        Args:
            primary_diagnosis: Primary ICD-10 code
            comorbidities: List of comorbidity ICD-10 codes
            adl_score: Optional ADL score (higher = more dependent)
            has_extensive_services: Whether patient needs extensive services

        Returns:
            Nursing group (ES1, ES2, HBS1, HBS2, LBS1, LBS2)
        """
        all_codes = [primary_diagnosis] + comorbidities
        clinical_category = self._get_clinical_category(all_codes)

        # Check for extensive services (trach, vent, IV meds, etc.)
        if has_extensive_services:
            return 'ES1' if adl_score and adl_score >= 15 else 'ES2'

        # Map to nursing group based on clinical category
        for group, categories in self.NURSING_CATEGORIES.items():
            if clinical_category in categories:
                return group

        # Default to LBS2
        return 'LBS2'

    def check_slp_comorbidity(self, comorbidities: List[str]) -> bool:
        """
        Check if patient has SLP comorbidities.

        Args:
            comorbidities: List of ICD-10 codes

        Returns:
            True if SLP services are needed
        """
        for code in comorbidities:
            for slp_code in self.SLP_CONDITIONS:
                if code.startswith(slp_code):
                    return True
        return False

    def calculate_nta_score(self, comorbidities: List[str],
                           special_services: Optional[Dict] = None) -> int:
        """
        Calculate NTA (Non-Therapy Ancillary) score from comorbidities.

        Args:
            comorbidities: List of ICD-10 codes
            special_services: Dict of special services (dialysis, etc.)

        Returns:
            NTA score (0-12)
        """
        score = 0

        # Map ICD-10 codes to NTA comorbidities
        comorbidity_mapping = {
            'J15': 'pneumonia', 'J18': 'pneumonia',
            'A40': 'septicemia', 'A41': 'septicemia',
            'E11': 'diabetes', 'E10': 'diabetes',
            'J44': 'copd',
            'N39.0': 'uti',
            'I50': 'chf',
            'B20': 'hiv',
            'G35': 'multiple_sclerosis',
            'G20': 'parkinsons',
            'G81': 'hemiplegia',
            'R47.01': 'aphasia',
            'E46': 'malnutrition',
            'F32': 'depression',
            'F31': 'bipolar',
            'F20': 'schizophrenia',
        }

        # Score comorbidities
        for code in comorbidities:
            for icd_prefix, condition in comorbidity_mapping.items():
                if code.startswith(icd_prefix):
                    score += self.NTA_SCORES.get(condition, 0)

        # Add special service scores
        if special_services:
            if special_services.get('dialysis'):
                score += 8

        # Cap at 12
        return min(score, 12)

    def classify_patient(self, extracted_data: Dict) -> Dict:
        """
        Classify patient into all PDPM groups.

        Args:
            extracted_data: Dictionary from document parser with clinical data

        Returns:
            Dictionary with all PDPM classifications
        """
        primary_diagnosis = extracted_data.get('primary_diagnosis', '')
        comorbidities = extracted_data.get('comorbidities', [])
        functional_status = extracted_data.get('functional_status', {})
        therapy_needs = extracted_data.get('therapy_needs', {})
        special_services = extracted_data.get('special_services', {})

        # Classify PT/OT groups
        pt_ot = self.classify_pt_ot_group(
            primary_diagnosis,
            comorbidities,
            functional_status.get('adl_score')
        )

        # Classify Nursing group
        has_extensive_services = any([
            special_services.get('trach'),
            special_services.get('dialysis'),
            special_services.get('iv_abx')
        ])
        nursing_group = self.classify_nursing_group(
            primary_diagnosis,
            comorbidities,
            functional_status.get('adl_score'),
            has_extensive_services
        )

        # Check SLP comorbidity
        has_slp_comorbidity = self.check_slp_comorbidity(comorbidities)

        # Calculate NTA score
        nta_score = self.calculate_nta_score(comorbidities, special_services)

        return {
            'pt_group': pt_ot['pt_group'],
            'ot_group': pt_ot['ot_group'],
            'slp_group': 'SLP' if has_slp_comorbidity or therapy_needs.get('slp') else 'None',
            'nursing_group': nursing_group,
            'nta_score': nta_score,
            'clinical_category': pt_ot['clinical_category']
        }

    def _get_clinical_category(self, icd_codes: List[str]) -> Optional[str]:
        """
        Get clinical category from ICD-10 codes.

        Args:
            icd_codes: List of ICD-10 codes

        Returns:
            Clinical category name or None
        """
        for category, code_prefixes in self.CLINICAL_CATEGORIES.items():
            for code in icd_codes:
                for prefix in code_prefixes:
                    if code.startswith(prefix):
                        return category
        return None

    def estimate_los(self, pdpm_groups: Dict, special_services: Optional[Dict] = None) -> int:
        """
        Estimate length of stay based on PDPM groups and services.

        Args:
            pdpm_groups: Dictionary with PDPM classifications
            special_services: Optional dict of special services

        Returns:
            Estimated LOS in days
        """
        base_los = 15  # Default

        # Adjust based on PT/OT group
        pt_group = pdpm_groups.get('pt_group', 'TE')
        los_adjustments = {
            'TA': 12,  # Major joint - shorter stay
            'TB': 14,
            'TC': 18,  # More complex
            'TD': 16,
            'TE': 15
        }
        base_los = los_adjustments.get(pt_group, 15)

        # Adjust for special services
        if special_services:
            if special_services.get('dialysis'):
                base_los += 5
            if special_services.get('wound_vac'):
                base_los += 3
            if special_services.get('trach'):
                base_los += 7

        return base_los


# Example usage
if __name__ == '__main__':
    classifier = PDPMClassifier()

    # Test with sample data
    sample_data = {
        'primary_diagnosis': 'M16.11',  # Unilateral primary osteoarthritis, right hip
        'comorbidities': ['I50.9', 'E11.9', 'J44.0'],  # CHF, Diabetes, COPD
        'functional_status': {'adl_score': 12},
        'therapy_needs': {'pt': True, 'ot': True, 'slp': False},
        'special_services': {'dialysis': False, 'iv_abx': False}
    }

    result = classifier.classify_patient(sample_data)
    print("PDPM Classification:", result)

    los = classifier.estimate_los(result, sample_data['special_services'])
    print(f"Estimated LOS: {los} days")
