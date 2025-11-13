"""
REAL-WORLD WISCONSIN SNF ADMISSION SCENARIOS
==============================================

This seed script creates realistic admission scenarios that Wisconsin SNF
administrators encounter daily. Use this to demo the system effectively.

Categories:
- High-margin Medicare winners (orthopedic, stroke)
- Medium-margin cases (cardiac, pulmonary, wound care)
- Low-margin/loss cases (dementia, hospice, behavioral)
- Edge cases (bariatric, trach/vent, dialysis)
- Complex medical (sepsis, multi-comorbid)
"""

from datetime import date
from config.database import init_db
from models.organization import Organization
from models.facility import Facility
from models.payer import Payer
from models.rates import Rate
from models.cost_model import CostModel
from models.admission import Admission


def seed_realistic_data():
    """Seed database with real-world Wisconsin SNF scenarios."""
    print("=" * 70)
    print("🏥 LOADING REALISTIC WISCONSIN SNF ADMISSION SCENARIOS")
    print("=" * 70)
    print()

    init_db()

    # Get existing organization
    org = Organization.get_by_subdomain("demo")
    if not org:
        print("❌ Error: Demo organization not found. Run seed_database.py first.")
        return

    print(f"✅ Using organization: {org.name}")

    # Get existing facilities
    facilities = Facility.get_by_organization(org.id)
    if not facilities or len(facilities) < 2:
        print("❌ Error: Need at least 2 facilities. Run seed_database.py first.")
        return

    facility1 = facilities[0]
    facility2 = facilities[1]
    print(f"✅ Using facilities: {facility1.name}, {facility2.name}")

    # Get or create realistic Wisconsin payers
    print("\n📋 Setting up realistic Wisconsin payers...")

    # Medicare FFS
    payer_medicare = Payer.get_by_type(org.id, Payer.MEDICARE_FFS)
    if not payer_medicare:
        payer_medicare = Payer.create(org.id, Payer.MEDICARE_FFS)
    print(f"  ✅ {payer_medicare.get_display_name()}")

    # Real Wisconsin MA plans
    payer_humana = Payer.create(org.id, Payer.MEDICARE_ADVANTAGE, "Humana Gold Plus")
    print(f"  ✅ Humana Gold Plus (MA)")

    payer_uhc = Payer.create(org.id, Payer.MEDICARE_ADVANTAGE, "UnitedHealthcare Dual Complete")
    print(f"  ✅ UnitedHealthcare Dual Complete (MA)")

    payer_anthem = Payer.create(org.id, Payer.MEDICARE_ADVANTAGE, "Anthem Blue Cross Medicare")
    print(f"  ✅ Anthem Blue Cross Medicare (MA)")

    # Wisconsin Medicaid
    payer_medicaid = Payer.create(org.id, Payer.MEDICAID_FFS, "Wisconsin Medicaid")
    print(f"  ✅ Wisconsin Medicaid")

    # Real Wisconsin Family Care MCOs
    payer_icare = Payer.create(org.id, Payer.FAMILY_CARE, "iCare Family Care")
    print(f"  ✅ iCare Family Care MCO")

    payer_lakeland = Payer.create(org.id, Payer.FAMILY_CARE, "Lakeland Care")
    print(f"  ✅ Lakeland Care MCO")

    payer_care_wi = Payer.create(org.id, Payer.FAMILY_CARE, "Care Wisconsin")
    print(f"  ✅ Care Wisconsin MCO")

    print("\n" + "=" * 70)
    print("💰 CREATING REALISTIC ADMISSION SCENARIOS")
    print("=" * 70)

    # ===========================================================================
    # CATEGORY 1: HIGH-MARGIN WINNERS (Score 80-95)
    # ===========================================================================
    print("\n✅ HIGH-MARGIN WINNERS (Accept immediately)")
    print("-" * 70)

    # Scenario 1: Total Hip Replacement - Classic SNF winner
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-001',
        extracted_data={
            'diagnoses': ['Z96.641', 'M16.11', 'I10', 'E11.9'],  # Status post THA, osteoarthritis, HTN, diabetes
            'medications': ['Enoxaparin', 'Warfarin', 'Metformin', 'Lisinopril', 'Oxycodone'],
            'function_score': 7,
            'cognitive_score': 14,
            'therapy_needs': ['PT', 'OT'],
            'special_treatments': ['DVT prophylaxis']
        },
        pdpm_groups={
            'pt_group': 'TA',   # Highest therapy
            'ot_group': 'TA',
            'slp_group': 'SA',
            'nursing_group': 'ES1',  # High nursing
            'nta_group': '6-11'
        },
        projected_revenue=218450.00,
        projected_cost=132600.00,
        projected_los=22,
        margin_score=92,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Classic high-revenue Medicare case',
                '✅ Excellent therapy potential - full PT/OT billable',
                '✅ Low denial risk for primary THA with standard complications',
                '✅ Strong projected margin: $85,850 (39.3%)',
                '✅ Facility has required capabilities',
                '✅ Typical 21-day LOS with good discharge planning'
            ],
            'risks': ['⚠️ Monitor INR for warfarin management', '⚠️ DVT prophylaxis compliance'],
            'conclusion': 'ACCEPT - Ideal SNF admission. High margin, low risk, excellent outcome potential.'
        }
    )
    print(f"  {admission.case_number}: Total Hip Replacement (Medicare) - Score {admission.margin_score}")

    # Scenario 2: CVA/Stroke with good rehab potential
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_uhc.id,
        case_number='WI-2025-002',
        extracted_data={
            'diagnoses': ['I63.9', 'I69.351', 'G81.91', 'I48.91', 'I10'],  # CVA, hemiplegia, a-fib
            'medications': ['Apixaban', 'Atorvastatin', 'Metoprolol', 'ASA'],
            'function_score': 9,
            'cognitive_score': 11,
            'therapy_needs': ['PT', 'OT', 'SLP'],
            'special_treatments': []
        },
        pdpm_groups={
            'pt_group': 'TA',
            'ot_group': 'TB',
            'slp_group': 'SC',  # Speech therapy for dysphagia
            'nursing_group': 'HBS1',
            'nta_group': '6-11'
        },
        projected_revenue=195600.00,
        projected_cost=118400.00,
        projected_los=28,
        margin_score=88,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ UHC MA contract - stable per diem reimbursement',
                '✅ Stroke rehab = high therapy utilization (PT/OT/SLP)',
                '✅ Good functional recovery potential',
                '✅ Projected margin: $77,200 (39.5%)',
                '✅ 28-day LOS allows full therapy progression'
            ],
            'risks': ['⚠️ Monitor swallowing/aspiration risk', '⚠️ Fall risk with hemiplegia'],
            'conclusion': 'ACCEPT - Excellent stroke rehab case with strong MA reimbursement.'
        }
    )
    print(f"  {admission.case_number}: CVA/Stroke Rehab (UHC MA) - Score {admission.margin_score}")

    # Scenario 3: Total Knee Replacement
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-003',
        extracted_data={
            'diagnoses': ['Z96.651', 'M17.11', 'E66.9', 'I10'],  # Status post TKA, obesity
            'medications': ['Enoxaparin', 'Acetaminophen', 'Gabapentin', 'Losartan'],
            'function_score': 8,
            'cognitive_score': 15,
            'therapy_needs': ['PT', 'OT'],
            'special_treatments': ['DVT prophylaxis', 'Bariatric equipment']
        },
        pdpm_groups={
            'pt_group': 'TA',
            'ot_group': 'TA',
            'slp_group': 'SA',
            'nursing_group': 'ES1',
            'nta_group': '0-5'
        },
        projected_revenue=212300.00,
        projected_cost=135800.00,
        projected_los=20,
        margin_score=85,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ High Medicare reimbursement for TKA',
                '✅ Full therapy potential with good outcomes expected',
                '✅ Facility has bariatric capabilities',
                '✅ Projected margin: $76,500 (36.0%)',
                '✅ Standard 3-week rehabilitation course'
            ],
            'risks': ['⚠️ Obesity increases care complexity', '⚠️ DVT risk management required'],
            'conclusion': 'ACCEPT - Strong orthopedic case with adequate bariatric support.'
        }
    )
    print(f"  {admission.case_number}: Total Knee Replacement (Medicare) - Score {admission.margin_score}")

    # ===========================================================================
    # CATEGORY 2: SOLID PERFORMERS (Score 65-79)
    # ===========================================================================
    print("\n💼 SOLID PERFORMERS (Accept with monitoring)")
    print("-" * 70)

    # Scenario 4: CHF Exacerbation
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_humana.id,
        case_number='WI-2025-004',
        extracted_data={
            'diagnoses': ['I50.23', 'J44.1', 'N18.3', 'E11.65'],  # CHF, COPD, CKD, diabetes
            'medications': ['Furosemide', 'Carvedilol', 'Lisinopril', 'Albuterol', 'Insulin', 'Spironolactone'],
            'function_score': 12,
            'cognitive_score': 10,
            'therapy_needs': ['PT'],
            'special_treatments': ['Daily weights', 'O2 therapy']
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'OB',
            'slp_group': 'SB',
            'nursing_group': 'HBS1',
            'nta_group': '12+'
        },
        projected_revenue=162400.00,
        projected_cost=118600.00,
        projected_los=25,
        margin_score=72,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Humana MA - reliable per diem reimbursement',
                '✅ Multiple comorbidities justify high nursing acuity',
                '✅ Moderate therapy potential as CHF stabilizes',
                '✅ Projected margin: $43,800 (27.0%)',
                '✅ Good discharge plan to home with HH'
            ],
            'risks': [
                '⚠️ Re-hospitalization risk if CHF not managed well',
                '⚠️ Requires close monitoring (daily weights, I&Os)',
                '⚠️ Medication management complexity'
            ],
            'conclusion': 'ACCEPT - Solid medical case requiring skilled nursing expertise.'
        }
    )
    print(f"  {admission.case_number}: CHF Exacerbation (Humana MA) - Score {admission.margin_score}")

    # Scenario 5: Pneumonia with deconditioning
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-005',
        extracted_data={
            'diagnoses': ['J18.9', 'E87.1', 'R53.1', 'I10'],  # Pneumonia, dehydration, weakness
            'medications': ['Levofloxacin', 'Acetaminophen', 'Lisinopril'],
            'function_score': 13,
            'cognitive_score': 12,
            'therapy_needs': ['PT', 'OT'],
            'special_treatments': ['IV antibiotics']
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'TB',
            'slp_group': 'SB',
            'nursing_group': 'HBS1',
            'nta_group': '6-11'
        },
        projected_revenue=142800.00,
        projected_cost=98200.00,
        projected_los=18,
        margin_score=74,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Medicare FFS with IV antibiotic justification',
                '✅ Good therapy potential post-infection resolution',
                '✅ Facility has IV capabilities',
                '✅ Projected margin: $44,600 (31.2%)',
                '✅ Short-term stay (14-21 days typical)'
            ],
            'risks': ['⚠️ C.diff risk with antibiotic use', '⚠️ Monitor for aspiration'],
            'conclusion': 'ACCEPT - Standard post-hospital pneumonia recovery case.'
        }
    )
    print(f"  {admission.case_number}: Pneumonia/Deconditioning (Medicare) - Score {admission.margin_score}")

    # Scenario 6: Wound care with MRSA
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_anthem.id,
        case_number='WI-2025-006',
        extracted_data={
            'diagnoses': ['L89.323', 'B95.62', 'E11.9', 'I70.25'],  # Pressure ulcer Stage 3, MRSA, diabetes, PVD
            'medications': ['Vancomycin', 'Metformin', 'Insulin', 'Pentoxifylline'],
            'function_score': 14,
            'cognitive_score': 11,
            'therapy_needs': ['PT'],
            'special_treatments': ['Wound VAC', 'IV antibiotics', 'Contact precautions']
        },
        pdpm_groups={
            'pt_group': 'TC',
            'ot_group': 'OC',
            'slp_group': 'SA',
            'nursing_group': 'ES2',
            'nta_group': '12+'
        },
        projected_revenue=185600.00,
        projected_cost=142300.00,
        projected_los=35,
        margin_score=68,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Anthem MA - competitive per diem rates',
                '✅ Wound VAC + IV antibiotics = high acuity reimbursement',
                '✅ Facility has wound care capabilities',
                '✅ Projected margin: $43,300 (23.3%)',
                '✅ Longer LOS allows wound healing progression'
            ],
            'risks': [
                '⚠️ MRSA isolation requirements increase staff time',
                '⚠️ Wound VAC supplies are expensive',
                '⚠️ May need longer than 35 days',
                '⚠️ Diabetes complicates wound healing'
            ],
            'conclusion': 'ACCEPT - Skilled wound care case with adequate reimbursement.'
        }
    )
    print(f"  {admission.case_number}: Wound Care/MRSA (Anthem MA) - Score {admission.margin_score}")

    # ===========================================================================
    # CATEGORY 3: MARGINAL CASES (Score 50-64)
    # ===========================================================================
    print("\n⚠️  MARGINAL CASES (Consider carefully)")
    print("-" * 70)

    # Scenario 7: COPD exacerbation with limited therapy
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_medicaid.id,
        case_number='WI-2025-007',
        extracted_data={
            'diagnoses': ['J44.1', 'J96.11', 'F17.210', 'I50.9'],  # COPD, resp failure, tobacco use, CHF
            'medications': ['Albuterol', 'Ipratropium', 'Prednisone', 'Furosemide'],
            'function_score': 15,
            'cognitive_score': 9,
            'therapy_needs': [],
            'special_treatments': ['O2 therapy', 'Nebulizer treatments']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'HBS2',
            'nta_group': '12+'
        },
        projected_revenue=118400.00,
        projected_cost=108200.00,
        projected_los=30,
        margin_score=58,
        recommendation='Defer',
        explanation={
            'factors': [
                '⚠️ Medicaid reimbursement is lower',
                '⚠️ Limited therapy potential = less revenue',
                '⚠️ High nursing needs without offsetting therapy revenue',
                '⚠️ Projected margin: $10,200 (8.6%)',
                '⚠️ Long LOS (30+ days) ties up bed'
            ],
            'risks': [
                '⚠️ Re-hospitalization risk high with COPD',
                '⚠️ Behavioral issues with smoking withdrawal',
                '⚠️ Minimal margin leaves no room for complications'
            ],
            'conclusion': 'DEFER - Consider only if you need Medicaid census for payer mix. Low financial margin.'
        }
    )
    print(f"  {admission.case_number}: COPD Exacerbation (Medicaid) - Score {admission.margin_score}")

    # Scenario 8: Family Care long-stay
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_icare.id,
        case_number='WI-2025-008',
        extracted_data={
            'diagnoses': ['F03.90', 'G20', 'I10', 'R26.81'],  # Dementia, Parkinson's, HTN, gait abnormality
            'medications': ['Carbidopa-Levodopa', 'Donepezil', 'Amlodipine', 'Quetiapine'],
            'function_score': 16,
            'cognitive_score': 4,
            'therapy_needs': [],
            'special_treatments': ['Behavioral management', 'Fall prevention']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'LBS1',
            'nta_group': '12+'
        },
        projected_revenue=156800.00,
        projected_cost=148600.00,
        projected_los=60,
        margin_score=54,
        recommendation='Defer',
        explanation={
            'factors': [
                '⚠️ iCare Family Care - moderate MCO rates',
                '⚠️ Very long LOS (60+ days) typical for dementia/Parkinson\'s',
                '⚠️ No therapy revenue',
                '⚠️ Projected margin: $8,200 (5.2%)',
                '⚠️ High staff time for behavioral management'
            ],
            'risks': [
                '⚠️ Dementia + Parkinson\'s = falls, behavioral issues',
                '⚠️ Minimal financial margin',
                '⚠️ Long-term bed commitment with low return'
            ],
            'conclusion': 'DEFER - Accept only if strategic need for Family Care relationship or low census.'
        }
    )
    print(f"  {admission.case_number}: Dementia/Parkinson's (iCare FC) - Score {admission.margin_score}")

    # Scenario 9: Diabetes with complications
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_medicaid.id,
        case_number='WI-2025-009',
        extracted_data={
            'diagnoses': ['E11.65', 'E11.621', 'N18.4', 'I70.25', 'L97.421'],  # DM with complications, CKD, PVD, foot ulcer
            'medications': ['Insulin', 'Gabapentin', 'Lisinopril', 'Atorvastatin'],
            'function_score': 14,
            'cognitive_score': 10,
            'therapy_needs': ['PT'],
            'special_treatments': ['Wound care', 'Glucose monitoring']
        },
        pdpm_groups={
            'pt_group': 'TC',
            'ot_group': 'OC',
            'slp_group': 'SA',
            'nursing_group': 'HBS2',
            'nta_group': '12+'
        },
        projected_revenue=132600.00,
        projected_cost=124800.00,
        projected_los=42,
        margin_score=61,
        recommendation='Defer',
        explanation={
            'factors': [
                '⚠️ Wisconsin Medicaid - limited reimbursement',
                '⚠️ Complex diabetic foot ulcer care',
                '⚠️ CKD complicates medication management',
                '⚠️ Projected margin: $7,800 (5.9%)',
                '⚠️ Long healing timeline (6+ weeks)'
            ],
            'risks': [
                '⚠️ High amputation risk if ulcer doesn\'t heal',
                '⚠️ Wound supplies expensive',
                '⚠️ Re-hospitalization risk with diabetes complications'
            ],
            'conclusion': 'DEFER - Tight margin with high clinical risk. Consider if you have strong diabetes/wound program.'
        }
    )
    print(f"  {admission.case_number}: Diabetic Foot Ulcer (Medicaid) - Score {admission.margin_score}")

    # ===========================================================================
    # CATEGORY 4: HIGH-RISK / LOW-MARGIN (Score 30-49)
    # ===========================================================================
    print("\n❌ HIGH-RISK / LOW-MARGIN (Decline unless strategic need)")
    print("-" * 70)

    # Scenario 10: Advanced dementia with feeding issues
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_lakeland.id,
        case_number='WI-2025-010',
        extracted_data={
            'diagnoses': ['G30.9', 'F02.81', 'R13.10', 'E43', 'L89.154'],  # Alzheimer's, behavioral, dysphagia, malnutrition, pressure ulcer
            'medications': ['Donepezil', 'Quetiapine', 'Lorazepam', 'Multivitamin'],
            'function_score': 18,
            'cognitive_score': 1,
            'therapy_needs': [],
            'special_treatments': ['Modified diet', 'Feeding assistance', 'Behavioral management']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'HBS2',
            'nta_group': '12+'
        },
        projected_revenue=142600.00,
        projected_cost=168400.00,
        projected_los=90,
        margin_score=38,
        recommendation='Decline',
        explanation={
            'factors': [
                '❌ Lakeland Care FC - lower MCO reimbursement',
                '❌ Advanced dementia with NO therapy potential',
                '❌ Very high staff time for feeding/behavioral issues',
                '❌ Projected LOSS: -$25,800 (-18.1%)',
                '❌ Very long stay (90+ days) with negative margin'
            ],
            'risks': [
                '❌ Feeding aspiration risk',
                '❌ Behavioral issues disrupt other residents',
                '❌ Pressure ulcer care requirements',
                '❌ Family may resist hospice discussion',
                '❌ Financial loss accumulates over long LOS'
            ],
            'conclusion': 'DECLINE - Significant financial loss with high care burden. This is a hospice-appropriate case.'
        }
    )
    print(f"  {admission.case_number}: Advanced Dementia (Lakeland FC) - Score {admission.margin_score}")

    # Scenario 11: Hospice-appropriate cancer case
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_medicaid.id,
        case_number='WI-2025-011',
        extracted_data={
            'diagnoses': ['C34.90', 'C79.51', 'R53.0', 'R06.02', 'F32.9'],  # Lung cancer, bone mets, weakness, SOB, depression
            'medications': ['Morphine', 'Lorazepam', 'Dexamethasone', 'Ondansetron'],
            'function_score': 17,
            'cognitive_score': 8,
            'therapy_needs': [],
            'special_treatments': ['Pain management', 'O2 therapy']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'ES2',
            'nta_group': '12+'
        },
        projected_revenue=128400.00,
        projected_cost=152600.00,
        projected_los=45,
        margin_score=32,
        recommendation='Decline',
        explanation={
            'factors': [
                '❌ Medicaid reimbursement insufficient for end-of-life care',
                '❌ No therapy potential - comfort care only',
                '❌ Projected LOSS: -$24,200 (-18.9%)',
                '❌ High emotional burden on staff',
                '❌ This is a HOSPICE case, not skilled SNF'
            ],
            'risks': [
                '❌ Rapid decline likely',
                '❌ Morphine/controlled substance management',
                '❌ Family needs grief support beyond SNF scope',
                '❌ Medicare hospice benefit provides better care model'
            ],
            'conclusion': 'DECLINE - Refer to hospice. SNF not appropriate level of care. Financial loss significant.'
        }
    )
    print(f"  {admission.case_number}: Metastatic Cancer (Medicaid) - Score {admission.margin_score}")

    # Scenario 12: Behavioral psych - inappropriate for SNF
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicaid.id,
        case_number='WI-2025-012',
        extracted_data={
            'diagnoses': ['F20.9', 'F10.20', 'F31.81', 'R45.6'],  # Schizophrenia, alcohol dependence, bipolar, violent behavior
            'medications': ['Risperidone', 'Lithium', 'Lorazepam', 'Thiamine'],
            'function_score': 10,
            'cognitive_score': 6,
            'therapy_needs': [],
            'special_treatments': ['Behavioral management', '1:1 supervision']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'LBS2',
            'nta_group': '12+'
        },
        projected_revenue=115800.00,
        projected_cost=184600.00,
        projected_los=60,
        margin_score=22,
        recommendation='Decline',
        explanation={
            'factors': [
                '❌ Medicaid - insufficient for psych needs',
                '❌ Primary issue is psychiatric, not medical/skilled',
                '❌ Projected LOSS: -$68,800 (-59.4%)',
                '❌ May require 1:1 staffing = extremely expensive',
                '❌ SNF not appropriate setting for acute psych'
            ],
            'risks': [
                '❌ Safety risk to staff and other residents',
                '❌ Violent behavior liability',
                '❌ Substance withdrawal issues',
                '❌ Massive financial loss',
                '❌ Regulatory risk if patient harms others'
            ],
            'conclusion': 'DECLINE IMMEDIATELY - This patient needs psychiatric facility, not SNF. Severe financial and safety risk.'
        }
    )
    print(f"  {admission.case_number}: Acute Psychiatric (Medicaid) - Score {admission.margin_score}")

    # ===========================================================================
    # CATEGORY 5: COMPLEX/EDGE CASES (Variable scores 45-75)
    # ===========================================================================
    print("\n🔧 COMPLEX/EDGE CASES (Require special capabilities)")
    print("-" * 70)

    # Scenario 13: Bariatric patient - need equipment
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-013',
        extracted_data={
            'diagnoses': ['E66.01', 'Z98.84', 'I50.9', 'E11.9', 'J96.11'],  # Morbid obesity (BMI 52), bariatric surgery, CHF, diabetes, resp failure
            'medications': ['Furosemide', 'Insulin', 'CPAP'],
            'function_score': 10,
            'cognitive_score': 12,
            'therapy_needs': ['PT', 'OT'],
            'special_treatments': ['Bariatric bed', 'Ceiling lift', 'Bariatric wheelchair', 'O2']
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'TB',
            'slp_group': 'SA',
            'nursing_group': 'ES1',
            'nta_group': '12+'
        },
        projected_revenue=198400.00,
        projected_cost=164200.00,
        projected_los=32,
        margin_score=67,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Medicare reimbursement adequate for bariatric care',
                '✅ Facility HAS bariatric capabilities (beds, lifts, wheelchairs)',
                '✅ Post-surgical recovery = good therapy potential',
                '✅ Projected margin: $34,200 (17.2%)',
                '⚠️ Requires specialized equipment and staff training'
            ],
            'risks': [
                '⚠️ Equipment costs are high (bariatric bed $300/month)',
                '⚠️ Requires 2-person transfers (staff time)',
                '⚠️ OSA/CPAP compliance monitoring',
                '⚠️ CHF + obesity = decompensation risk'
            ],
            'conclusion': 'ACCEPT - Your facility has bariatric capabilities. Margin is acceptable for complexity level.'
        }
    )
    print(f"  {admission.case_number}: Bariatric Post-Surgery (Medicare) - Score {admission.margin_score}")

    # Scenario 14: Trach/vent - very high acuity
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-014',
        extracted_data={
            'diagnoses': ['J96.11', 'Z99.11', 'J69.0', 'G93.1'],  # Respiratory failure, trach, aspiration pneumonia, anoxic brain injury
            'medications': ['Vancomycin', 'Piperacillin-Tazobactam', 'Propofol wean'],
            'function_score': 18,
            'cognitive_score': 3,
            'therapy_needs': [],
            'special_treatments': ['Trach care', 'Ventilator', 'IV antibiotics', 'Specialized nursing']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'ES2',
            'nta_group': '12+'
        },
        projected_revenue=224600.00,
        projected_cost=248200.00,
        projected_los=60,
        margin_score=48,
        recommendation='Decline',
        explanation={
            'factors': [
                '❌ Facility does NOT have ventilator capability',
                '❌ Requires specialized respiratory therapist 24/7',
                '❌ Projected LOSS: -$23,600 (-10.5%)',
                '❌ Very poor prognosis with anoxic brain injury',
                '❌ This case needs specialized vent unit, not standard SNF'
            ],
            'risks': [
                '❌ Your facility lacks vent capability per admission notes',
                '❌ High liability if vent malfunction',
                '❌ Staff not trained for vent management',
                '❌ Equipment costs exceed reimbursement',
                '❌ Family may have unrealistic expectations'
            ],
            'conclusion': 'DECLINE - Facility does not have ventilator capability. Refer to specialized vent SNF.'
        }
    )
    print(f"  {admission.case_number}: Trach/Vent (Medicare) - Score {admission.margin_score} - DECLINE (no vent capability)")

    # Scenario 15: ESRD on dialysis
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-015',
        extracted_data={
            'diagnoses': ['N18.6', 'Z99.2', 'I50.9', 'E11.22'],  # ESRD, dialysis dependence, CHF, diabetic CKD
            'medications': ['Sevelamer', 'Epoetin', 'Insulin', 'Carvedilol', 'Furosemide'],
            'function_score': 12,
            'cognitive_score': 11,
            'therapy_needs': ['PT'],
            'special_treatments': ['Hemodialysis 3x/week', 'Fistula care', 'Renal diet']
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'OB',
            'slp_group': 'SA',
            'nursing_group': 'HBS1',
            'nta_group': '12+'
        },
        projected_revenue=178400.00,
        projected_cost=152600.00,
        projected_los=28,
        margin_score=71,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Facility HAS dialysis capability (transport arrangement)',
                '✅ Medicare ESRD + SNF dual reimbursement',
                '✅ Moderate therapy potential between dialysis days',
                '✅ Projected margin: $25,800 (14.5%)',
                '✅ Established relationship with dialysis center'
            ],
            'risks': [
                '⚠️ Dialysis transport 3x/week ($150/trip = $1,800/week)',
                '⚠️ Hemodynamic instability post-dialysis',
                '⚠️ Fistula infection risk',
                '⚠️ Complex medication management',
                '⚠️ Must coordinate therapy around dialysis schedule'
            ],
            'conclusion': 'ACCEPT - Facility has dialysis support. Margin acceptable for ESRD complexity.'
        }
    )
    print(f"  {admission.case_number}: ESRD/Dialysis (Medicare) - Score {admission.margin_score}")

    # Scenario 16: Multiple sclerosis exacerbation
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_humana.id,
        case_number='WI-2025-016',
        extracted_data={
            'diagnoses': ['G35', 'G83.11', 'N31.2', 'L89.201'],  # MS, monoplegia, neurogenic bladder, pressure ulcer
            'medications': ['Methylprednisolone IV', 'Baclofen', 'Oxybutynin', 'Gabapentin'],
            'function_score': 14,
            'cognitive_score': 10,
            'therapy_needs': ['PT', 'OT'],
            'special_treatments': ['IV steroids', 'Foley catheter', 'Wound care']
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'TB',
            'slp_group': 'SA',
            'nursing_group': 'HBS1',
            'nta_group': '12+'
        },
        projected_revenue=168200.00,
        projected_cost=128400.00,
        projected_los=24,
        margin_score=69,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Humana MA - good reimbursement',
                '✅ MS exacerbation responds well to steroids + therapy',
                '✅ Good functional improvement potential',
                '✅ Projected margin: $39,800 (23.7%)',
                '✅ Standard 3-4 week recovery timeline'
            ],
            'risks': [
                '⚠️ Steroid side effects (hyperglycemia, agitation)',
                '⚠️ UTI risk with Foley catheter',
                '⚠️ Pressure ulcer Stage 2 - needs management',
                '⚠️ MS progression unpredictable'
            ],
            'conclusion': 'ACCEPT - Good neuro rehab case with solid MA reimbursement and improvement potential.'
        }
    )
    print(f"  {admission.case_number}: Multiple Sclerosis (Humana MA) - Score {admission.margin_score}")

    # Scenario 17: Sepsis with multi-organ issues
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-017',
        extracted_data={
            'diagnoses': ['A41.9', 'N17.9', 'R65.20', 'E87.6', 'J96.01'],  # Sepsis, AKI, severe sepsis, hypokalemia, resp failure
            'medications': ['Meropenem', 'Norepinephrine wean', 'Potassium', 'Albumin'],
            'function_score': 16,
            'cognitive_score': 8,
            'therapy_needs': [],
            'special_treatments': ['IV antibiotics', 'Frequent labs', 'Aggressive hydration']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'ES2',
            'nta_group': '12+'
        },
        projected_revenue=156800.00,
        projected_cost=148200.00,
        projected_los=28,
        margin_score=56,
        recommendation='Defer',
        explanation={
            'factors': [
                '⚠️ Medicare reimbursement adequate but tight margin',
                '⚠️ Post-sepsis recovery - very high acuity',
                '⚠️ Minimal therapy potential until medically stable',
                '⚠️ Projected margin: $8,600 (5.5%)',
                '⚠️ High re-hospitalization risk (30-40%)'
            ],
            'risks': [
                '⚠️ May decompensate and require re-hospitalization',
                '⚠️ AKI may progress to dialysis need',
                '⚠️ Medication costs high (Meropenem $200/day)',
                '⚠️ Requires close MD oversight',
                '⚠️ Tight margin leaves no room for complications'
            ],
            'conclusion': 'DEFER - Very high risk case. Accept only if you have strong hospitalist support and low census.'
        }
    )
    print(f"  {admission.case_number}: Post-Sepsis/Multi-Organ (Medicare) - Score {admission.margin_score}")

    # Scenario 18: ALS patient - palliative
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_care_wi.id,
        case_number='WI-2025-018',
        extracted_data={
            'diagnoses': ['G12.21', 'J96.11', 'R13.10', 'R53.1'],  # ALS, respiratory insufficiency, dysphagia, weakness
            'medications': ['Riluzole', 'BiPAP', 'Morphine'],
            'function_score': 18,
            'cognitive_score': 14,
            'therapy_needs': [],
            'special_treatments': ['BiPAP', 'Modified diet', 'Palliative care']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'ES1',
            'nta_group': '12+'
        },
        projected_revenue=148200.00,
        projected_cost=172400.00,
        projected_los=60,
        margin_score=42,
        recommendation='Decline',
        explanation={
            'factors': [
                '❌ Care Wisconsin FC - limited palliative reimbursement',
                '❌ ALS is progressive, terminal disease',
                '❌ Projected LOSS: -$24,200 (-16.3%)',
                '❌ No therapy benefit (disease is degenerative)',
                '❌ This is a HOSPICE case'
            ],
            'risks': [
                '❌ Progressive respiratory failure',
                '❌ Aspiration risk with dysphagia',
                '❌ Emotional burden on staff with terminal diagnosis',
                '❌ Family may struggle with hospice acceptance',
                '❌ Financial loss over extended LOS'
            ],
            'conclusion': 'DECLINE - Refer to hospice. ALS is terminal condition best served by hospice benefit, not SNF.'
        }
    )
    print(f"  {admission.case_number}: ALS/Palliative (Care WI FC) - Score {admission.margin_score}")

    # Scenario 19: Young traumatic brain injury - long rehab potential
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='WI-2025-019',
        extracted_data={
            'diagnoses': ['S06.2X5A', 'G93.1', 'R41.0', 'F07.81'],  # Diffuse TBI, anoxic injury, disorientation, personality change
            'medications': ['Levetiracetam', 'Sertraline', 'Donepezil'],
            'function_score': 15,
            'cognitive_score': 5,
            'therapy_needs': ['PT', 'OT', 'SLP', 'Cognitive therapy'],
            'special_treatments': ['Behavioral management', 'Cognitive rehab']
        },
        pdpm_groups={
            'pt_group': 'TA',
            'ot_group': 'TA',
            'slp_group': 'SC',
            'nursing_group': 'HBS1',
            'nta_group': '12+'
        },
        projected_revenue=268400.00,
        projected_cost=212600.00,
        projected_los=60,
        margin_score=73,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ Medicare - high reimbursement for intensive rehab',
                '✅ All therapy disciplines billable (PT/OT/SLP/Cognitive)',
                '✅ Young patient (52) with good recovery potential',
                '✅ Projected margin: $55,800 (20.8%)',
                '✅ Long LOS allows comprehensive neuro rehab',
                '✅ Strong discharge to home potential'
            ],
            'risks': [
                '⚠️ Behavioral issues with frontal lobe injury',
                '⚠️ Requires specialized TBI rehab expertise',
                '⚠️ Family may have unrealistic recovery expectations',
                '⚠️ Seizure management required'
            ],
            'conclusion': 'ACCEPT - Excellent neuro rehab case. High therapy utilization with good margin and meaningful recovery potential.'
        }
    )
    print(f"  {admission.case_number}: Traumatic Brain Injury (Medicare) - Score {admission.margin_score}")

    # Scenario 20: GI bleed with anemia - short-term medical
    admission = Admission.create(
        organization_id=org.id,
        facility_id=facility2.id,
        payer_id=payer_uhc.id,
        case_number='WI-2025-020',
        extracted_data={
            'diagnoses': ['K92.2', 'D62', 'K25.4', 'E87.1'],  # GI bleed, anemia, gastric ulcer, dehydration
            'medications': ['Pantoprazole IV', 'Iron supplementation', 'Blood transfusion x2'],
            'function_score': 13,
            'cognitive_score': 12,
            'therapy_needs': ['PT'],
            'special_treatments': ['IV PPI', 'Serial H/H monitoring']
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'OB',
            'slp_group': 'SA',
            'nursing_group': 'HBS1',
            'nta_group': '6-11'
        },
        projected_revenue=128400.00,
        projected_cost=96200.00,
        projected_los=14,
        margin_score=75,
        recommendation='Accept',
        explanation={
            'factors': [
                '✅ UHC MA - good short-term per diem',
                '✅ Post-bleed stabilization = good therapy potential',
                '✅ Short LOS (10-14 days) = quick bed turnover',
                '✅ Projected margin: $32,200 (25.1%)',
                '✅ Good discharge plan to home once stable'
            ],
            'risks': [
                '⚠️ Re-bleeding risk (monitor H/H q12h)',
                '⚠️ IV PPI requires nursing time',
                '⚠️ Anemia recovery may take longer than expected'
            ],
            'conclusion': 'ACCEPT - Good short-term medical case with solid margin and quick turnover.'
        }
    )
    print(f"  {admission.case_number}: GI Bleed/Anemia (UHC MA) - Score {admission.margin_score}")

    # ===========================================================================
    # SUMMARY
    # ===========================================================================
    print("\n" + "=" * 70)
    print("✅ REALISTIC DATA SEEDING COMPLETE")
    print("=" * 70)
    print("\n📊 ADMISSION BREAKDOWN:")
    print("-" * 70)
    print("  ✅ HIGH-MARGIN WINNERS (80-95):        3 cases  → ACCEPT")
    print("  💼 SOLID PERFORMERS (65-79):           3 cases  → ACCEPT")
    print("  ⚠️  MARGINAL CASES (50-64):             3 cases  → DEFER/CONSIDER")
    print("  ❌ HIGH-RISK/LOW-MARGIN (30-49):       3 cases  → DECLINE")
    print("  🔧 COMPLEX/EDGE CASES (Variable):      8 cases  → Depends on capabilities")
    print("  " + "-" * 66)
    print("  TOTAL:                                20 realistic scenarios")
    print("-" * 70)

    print("\n🏆 PAYER MIX:")
    print("  • Medicare FFS:            8 cases")
    print("  • Medicare Advantage:      6 cases (Humana, UHC, Anthem)")
    print("  • Medicaid:                3 cases")
    print("  • Family Care MCOs:        3 cases (iCare, Lakeland, Care WI)")
    print()

    print("🎯 CASE TYPES:")
    print("  • Orthopedic (hip/knee):   3 cases")
    print("  • Neuro (stroke, TBI, MS): 3 cases")
    print("  • Cardiac/Pulmonary:       3 cases")
    print("  • Wound care:              2 cases")
    print("  • GI/Medical:              2 cases")
    print("  • Dementia/Behavioral:     3 cases")
    print("  • Hospice-appropriate:     2 cases")
    print("  • High-acuity (dialysis, bariatric, etc.): 2 cases")
    print()

    print("=" * 70)
    print("🚀 READY TO DEMO!")
    print("=" * 70)
    print("\nThese 20 cases represent the real-world mix of referrals Wisconsin SNFs")
    print("receive daily. Use them to demonstrate:")
    print()
    print("  1. How the system identifies HIGH-MARGIN winners (orthopedic, stroke)")
    print("  2. How it flags MARGINAL cases that need careful review")
    print("  3. How it DECLINES money-losing admissions (hospice, acute psych)")
    print("  4. How it handles COMPLEX cases (dialysis, bariatric, TBI)")
    print("  5. How payer mix affects profitability (Medicare vs Medicaid vs FC)")
    print()
    print("Login at: https://admissions-genie.onrender.com")
    print("Email:    jthayer@verisightanalytics.com")
    print("Password: TempPass2024!")
    print()
    print("=" * 70)


if __name__ == '__main__':
    seed_realistic_data()
