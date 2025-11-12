"""
Database seeding script to populate with sample data for testing.
Run this after initializing the database.
"""

from datetime import date, datetime
from config.database import init_db
from models.organization import Organization
from models.facility import Facility
from models.payer import Payer
from models.rates import Rate
from models.cost_model import CostModel
from models.user import User
from models.admission import Admission


def seed_database():
    """Seed database with sample data."""
    print("🌱 Seeding database with sample data...")

    # Initialize database first
    init_db()

    # Get or create organization (MULTI-TENANT)
    print("\n1. Getting or creating organization...")
    org = Organization.get_by_subdomain("demo")
    if not org:
        org = Organization.create(
            name="Demo SNF",
            subdomain="demo",
            subscription_tier=Organization.TIER_TRIAL
        )
        print(f"  ✅ Created organization: {org.name} (ID: {org.id})")
    else:
        print(f"  ℹ️  Organization already exists: {org.name} (ID: {org.id})")

    # Create sample facilities
    print("\n2. Creating facilities...")
    facility1 = Facility.create(
        organization_id=org.id,
        name="Sunshine SNF",
        wage_index=1.0234,
        vbp_multiplier=0.98,
        capabilities={
            'dialysis': True,
            'iv_abx': True,
            'wound_vac': True,
            'trach': True,
            'ventilator': False,
            'bariatric': True
        }
    )
    print(f"  ✅ Created: {facility1.name}")

    facility2 = Facility.create(
        organization_id=org.id,
        name="Green Valley Care Center",
        wage_index=0.9876,
        vbp_multiplier=1.01,
        capabilities={
            'dialysis': False,
            'iv_abx': True,
            'wound_vac': True,
            'trach': False,
            'ventilator': False,
            'bariatric': False
        }
    )
    print(f"  ✅ Created: {facility2.name}")

    # Create sample payers
    print("\n3. Creating payers...")
    payer_medicare = Payer.create(org.id, Payer.MEDICARE_FFS)
    print(f"  ✅ Created: {payer_medicare.get_display_name()}")

    payer_ma = Payer.create(org.id, Payer.MEDICARE_ADVANTAGE, "Humana Gold Plus")
    print(f"  ✅ Created: {payer_ma.get_display_name()}")

    payer_medicaid = Payer.create(org.id, Payer.MEDICAID_FFS)
    print(f"  ✅ Created: {payer_medicaid.get_display_name()}")

    payer_fc = Payer.create(org.id, Payer.FAMILY_CARE, "iCare Family Care MCO")
    print(f"  ✅ Created: {payer_fc.get_display_name()}")

    # Create sample rates
    print("\n3. Creating rates...")

    # Medicare FFS rates for facility 1
    medicare_rate_data = {
        'pt_component': 64.89,
        'ot_component': 64.38,
        'slp_component': 26.43,
        'nursing_component': 105.81,
        'nta_component': 86.72,
        'non_case_mix': 98.13,
        'fiscal_year': 2025
    }
    rate1 = Rate.create(
        org.id,
        facility1.id,
        payer_medicare.id,
        Rate.MEDICARE_FFS,
        medicare_rate_data,
        date(2024, 10, 1)
    )
    print(f"  ✅ Created Medicare FFS rate for {facility1.name}")

    # MA rates for facility 1
    ma_rate_data = {
        'contract_type': 'per_diem',
        'day_tiers': {
            '1-30': 450.00,
            '31-60': 400.00,
            '61-100': 375.00
        }
    }
    rate2 = Rate.create(
        org.id,
        facility1.id,
        payer_ma.id,
        Rate.MA_COMMERCIAL,
        ma_rate_data,
        date(2025, 1, 1)
    )
    print(f"  ✅ Created MA rate for {facility1.name}")

    # Medicaid WI rates for facility 1
    medicaid_rate_data = {
        'component_nursing': 185.00,
        'component_therapy': 95.00,
        'component_room': 45.00
    }
    rate3 = Rate.create(
        org.id,
        facility1.id,
        payer_medicaid.id,
        Rate.MEDICAID_WI,
        medicaid_rate_data,
        date(2025, 1, 1)
    )
    print(f"  ✅ Created Medicaid WI rate for {facility1.name}")

    # Family Care rates for facility 1
    fc_rate_data = {
        'nursing_matrix': {
            'ES1': 320.00,
            'ES2': 295.00,
            'HBS1': 285.00,
            'HBS2': 275.00,
            'LBS1': 250.00,
            'LBS2': 240.00
        },
        'nta_matrix': {
            '12+': 100.00,
            '6-11': 85.00,
            '0-5': 70.00
        }
    }
    rate4 = Rate.create(
        org.id,
        facility1.id,
        payer_fc.id,
        Rate.FAMILY_CARE_WI,
        fc_rate_data,
        date(2025, 1, 1)
    )
    print(f"  ✅ Created Family Care rate for {facility1.name}")

    # Create cost models for facility 1
    print("\n4. Creating cost models...")

    for acuity in [CostModel.LOW, CostModel.MEDIUM, CostModel.HIGH, CostModel.COMPLEX]:
        hours_map = {
            CostModel.LOW: 3.0,
            CostModel.MEDIUM: 4.0,
            CostModel.HIGH: 5.5,
            CostModel.COMPLEX: 7.0
        }
        supply_map = {
            CostModel.LOW: 40.00,
            CostModel.MEDIUM: 50.00,
            CostModel.HIGH: 60.00,
            CostModel.COMPLEX: 75.00
        }

        cost_model = CostModel.create(
            org.id,
            facility1.id,
            acuity,
            hours_map[acuity],
            35.00,  # Hourly rate
            supply_map[acuity],
            50.00,  # Pharmacy addon
            150.00  # Transport cost
        )
        print(f"  ✅ Created {acuity} acuity cost model for {facility1.name}")

    # Create rates for facility 2
    print("\n4b. Creating rates for facility 2...")

    # Medicare FFS rates for facility 2 (slightly different rates)
    medicare_rate_data_f2 = {
        'pt_component': 62.50,
        'ot_component': 62.00,
        'slp_component': 25.50,
        'nursing_component': 102.00,
        'nta_component': 84.00,
        'non_case_mix': 95.00,
        'fiscal_year': 2025
    }
    Rate.create(
        org.id,
        facility2.id,
        payer_medicare.id,
        Rate.MEDICARE_FFS,
        medicare_rate_data_f2,
        date(2024, 10, 1)
    )
    print(f"  ✅ Created Medicare FFS rate for {facility2.name}")

    # MA rates for facility 2
    ma_rate_data_f2 = {
        'contract_type': 'per_diem',
        'day_tiers': {
            '1-30': 425.00,
            '31-60': 380.00,
            '61-100': 360.00
        }
    }
    Rate.create(
        org.id,
        facility2.id,
        payer_ma.id,
        Rate.MA_COMMERCIAL,
        ma_rate_data_f2,
        date(2025, 1, 1)
    )
    print(f"  ✅ Created MA rate for {facility2.name}")

    # Medicaid rates for facility 2
    medicaid_rate_data_f2 = {
        'basic_rate': 295.00,
        'high_acuity_addon': 45.00
    }
    Rate.create(
        org.id,
        facility2.id,
        payer_medicaid.id,
        Rate.MEDICAID_WI,
        medicaid_rate_data_f2,
        date(2025, 1, 1)
    )
    print(f"  ✅ Created Medicaid WI rate for {facility2.name}")

    # Family Care rates for facility 2
    fc_rate_data_f2 = {
        'nursing_matrix': {
            'ES1': 310.00,
            'ES2': 285.00,
            'HBS1': 275.00,
            'HBS2': 265.00,
            'LBS1': 245.00,
            'LBS2': 235.00
        },
        'nta_matrix': {
            '12+': 95.00,
            '6-11': 82.00,
            '0-5': 68.00
        }
    }
    Rate.create(
        org.id,
        facility2.id,
        payer_fc.id,
        Rate.FAMILY_CARE_WI,
        fc_rate_data_f2,
        date(2025, 1, 1)
    )
    print(f"  ✅ Created Family Care rate for {facility2.name}")

    # Create cost models for facility 2
    print("\n4c. Creating cost models for facility 2...")

    for acuity in [CostModel.LOW, CostModel.MEDIUM, CostModel.HIGH, CostModel.COMPLEX]:
        hours_map = {
            CostModel.LOW: 3.2,
            CostModel.MEDIUM: 4.2,
            CostModel.HIGH: 5.7,
            CostModel.COMPLEX: 7.2
        }
        supply_map = {
            CostModel.LOW: 42.00,
            CostModel.MEDIUM: 52.00,
            CostModel.HIGH: 62.00,
            CostModel.COMPLEX: 77.00
        }

        CostModel.create(
            org.id,
            facility2.id,
            acuity,
            hours_map[acuity],
            36.00,  # Slightly higher hourly rate
            supply_map[acuity],
            32.00,  # Base pharmacy cost
            0.22    # Overhead percentage
        )
        print(f"  ✅ Created {acuity} acuity cost model for {facility2.name}")

    # Create sample users (skip if already exist)
    print("\n5. Creating users...")

    admin_user = User.get_by_email("admin@admissionsgenie.com")
    if not admin_user:
        admin_user = User.create(
            organization_id=org.id,
            email="admin@admissionsgenie.com",
            password="admin123",
            full_name="Admin User",
            facility_id=facility1.id,
            role=User.ADMIN
        )
        print(f"  ✅ Created admin user: {admin_user.email}")
    else:
        print(f"  ℹ️  Admin user already exists: {admin_user.email}")

    regular_user = User.get_by_email("user@admissionsgenie.com")
    if not regular_user:
        regular_user = User.create(
            organization_id=org.id,
            email="user@admissionsgenie.com",
            password="user123",
            full_name="Regular User",
            facility_id=facility1.id,
            role=User.USER
        )
        print(f"  ✅ Created regular user: {regular_user.email}")
    else:
        print(f"  ℹ️  Regular user already exists: {regular_user.email}")

    # Create additional user for jthayer@verisightanalytics.com
    jt_user = User.get_by_email("jthayer@verisightanalytics.com")
    if not jt_user:
        jt_user = User.create(
            organization_id=org.id,
            email="jthayer@verisightanalytics.com",
            password="admin123",  # Same as admin for now
            full_name="Josh Thayer",
            facility_id=facility1.id,
            role=User.ADMIN
        )
        print(f"  ✅ Created user: {jt_user.email}")
    else:
        print(f"  ℹ️  User already exists: {jt_user.email}")

    # Create sample admissions for demo
    print("\n6. Creating sample admissions for demo...")

    # Sample 1: High-margin Medicare hip fracture case (Score: 87)
    admission1 = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicare.id,
        case_number='DEMO-001',
        extracted_data={
            'diagnoses': ['Z96.641', 'M96.661', 'E11.9'],
            'medications': ['Warfarin', 'Metformin', 'Acetaminophen'],
            'function_score': 8,
            'cognitive_score': 12,
            'therapy_needs': ['PT', 'OT'],
            'special_treatments': ['IV antibiotics']
        },
        pdpm_groups={
            'pt_group': 'TA',
            'ot_group': 'TA',
            'slp_group': 'SA',
            'nursing_group': 'ES1',
            'nta_group': '6-11'
        },
        projected_revenue=202576.25,
        projected_cost=127000.00,
        projected_los=25,
        margin_score=87,
        recommendation='Accept',
        explanation={
            'factors': [
                'High therapy potential with excellent reimbursement',
                'Low denial risk for hip replacement with complications',
                'Facility has required capabilities (IV antibiotics)',
                'Strong projected margin of $75,576'
            ],
            'risks': ['Minimal - standard post-surgical care'],
            'conclusion': 'Excellent admission opportunity'
        }
    )
    print(f"  ✅ Created high-margin admission: {admission1.case_number} (Score: {admission1.margin_score})")

    # Sample 2: Medium-margin MA case (Score: 62)
    admission2 = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_ma.id,
        case_number='DEMO-002',
        extracted_data={
            'diagnoses': ['I50.9', 'J44.1', 'N18.3'],
            'medications': ['Furosemide', 'Albuterol', 'Lisinopril', 'Insulin'],
            'function_score': 11,
            'cognitive_score': 10,
            'therapy_needs': ['PT'],
            'special_treatments': []
        },
        pdpm_groups={
            'pt_group': 'TB',
            'ot_group': 'TB',
            'slp_group': 'SB',
            'nursing_group': 'HBS1',
            'nta_group': '6-11'
        },
        projected_revenue=135000.00,
        projected_cost=94590.00,
        projected_los=18,
        margin_score=62,
        recommendation='Defer',
        explanation={
            'factors': [
                'MA per diem contract provides stable revenue',
                'Multiple comorbidities (CHF, COPD, CKD) create moderate complexity',
                'Census at 85% - capacity available',
                'Reasonable projected margin of $40,410'
            ],
            'risks': ['Monitor for clinical decline', 'CHF exacerbation risk'],
            'conclusion': 'Moderate admission opportunity - acceptable with close monitoring'
        }
    )
    print(f"  ✅ Created medium-margin admission: {admission2.case_number} (Score: {admission2.margin_score})")

    # Sample 3: Low-margin Medicaid long-stay case (Score: 38)
    admission3 = Admission.create(
        organization_id=org.id,
        facility_id=facility1.id,
        payer_id=payer_medicaid.id,
        case_number='DEMO-003',
        extracted_data={
            'diagnoses': ['G30.9', 'I10', 'M81.0', 'R26.81'],
            'medications': ['Donepezil', 'Amlodipine', 'Calcium/VitD', 'Lorazepam'],
            'function_score': 18,
            'cognitive_score': 2,
            'therapy_needs': [],
            'special_treatments': ['Behavioral management']
        },
        pdpm_groups={
            'pt_group': 'PD',
            'ot_group': 'OD',
            'slp_group': 'SD',
            'nursing_group': 'HBS2',
            'nta_group': '12+'
        },
        projected_revenue=146250.00,
        projected_cost=158287.50,
        projected_los=45,
        margin_score=38,
        recommendation='Decline',
        explanation={
            'factors': [
                'Medicaid reimbursement insufficient for high care needs',
                'Advanced dementia with behavioral issues requires significant staff time',
                'Extended LOS (45 days) with minimal therapy revenue',
                'Projected negative margin of -$12,037'
            ],
            'risks': [
                'Financial loss likely',
                'Behavioral management challenges',
                'Minimal rehabilitation potential'
            ],
            'conclusion': 'High-risk admission. Consider only if strategic need to maintain Medicaid census for licensing.'
        }
    )
    print(f"  ✅ Created low-margin admission: {admission3.case_number} (Score: {admission3.margin_score})")

    print("\n✅ Database seeding complete!")
    print("\n📋 Login Credentials:")
    print("=" * 50)
    print(f"Admin Login:")
    print(f"  Email: admin@admissionsgenie.com")
    print(f"  Password: admin123")
    print(f"\nJosh Thayer Login:")
    print(f"  Email: jthayer@verisightanalytics.com")
    print(f"  Password: admin123")
    print(f"\nRegular User Login:")
    print(f"  Email: user@admissionsgenie.com")
    print(f"  Password: user123")
    print("=" * 50)
    print(f"\n📊 Sample Admissions Created:")
    print(f"  1. {admission1.case_number} - Medicare Hip Fracture (Score: {admission1.margin_score}) - ✅ ACCEPT")
    print(f"  2. {admission2.case_number} - MA Multi-Comorbid (Score: {admission2.margin_score}) - ⚠️  CONSIDER")
    print(f"  3. {admission3.case_number} - Medicaid Dementia (Score: {admission3.margin_score}) - ❌ DECLINE")
    print("=" * 50)


if __name__ == '__main__':
    seed_database()
