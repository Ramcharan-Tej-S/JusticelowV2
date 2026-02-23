# utils/seed_data.py — Realistic legal case seeder
# Case summaries inspired by real Indian court case patterns (public domain)
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db.database import (
    get_connection, insert_case, insert_historical_case,
    insert_entity, insert_edge, update_case,
)

# ─── Historical Cases (inspired by real Indian court patterns) ───────
HISTORICAL_CASES = [
    {
        "id": "HC001", "category": "landlord_tenant",
        "summary": "Tenant withheld rent for 6 months claiming uninhabitable conditions including persistent water leakage and electrical hazards. Landlord filed for eviction. Building inspector confirmed structural issues but tenant failed to notify landlord in writing as required by lease.",
        "outcome": "settled", "outcome_summary": "Settled at 40% of owed rent; landlord required to complete repairs within 90 days",
        "jurisdiction": "Delhi District Court", "year": 2022,
        "key_statutes": ["Delhi Rent Control Act 1958 S.14", "Transfer of Property Act S.108"],
        "dna_vector": [0.1, 0.7, 0.25, 0.6, 0.7, 0.2],
    },
    {
        "id": "HC002", "category": "employment",
        "summary": "Software engineer terminated without notice after reporting safety violations in the product codebase. Company claims poor performance; employee presents 4 years of positive performance reviews and documented retaliation timeline.",
        "outcome": "plaintiff_won", "outcome_summary": "Wrongful termination established; awarded 18 months compensation plus reinstatement offer",
        "jurisdiction": "Bangalore Labour Court", "year": 2023,
        "key_statutes": ["Industrial Disputes Act 1947 S.25F", "Whistleblower Protection Act 2014"],
        "dna_vector": [0.2, 0.8, 0.5, 0.8, 0.6, 0.4],
    },
    {
        "id": "HC003", "category": "contract",
        "summary": "Construction company failed to deliver residential project within stipulated 36-month timeline. 47 homebuyers filed joint complaint. Builder cites COVID delays and regulatory hold-ups. Buyers have documented 18-month pre-COVID delay.",
        "outcome": "plaintiff_won", "outcome_summary": "Builder ordered to pay 9% annual interest on deposits plus Rs. 5 lakh compensation per buyer",
        "jurisdiction": "RERA Maharashtra", "year": 2023,
        "key_statutes": ["RERA Act 2016 S.18", "Consumer Protection Act 2019 S.34"],
        "dna_vector": [0.3, 0.9, 0.75, 0.7, 0.5, 0.3],
    },
    {
        "id": "HC004", "category": "family",
        "summary": "Contested divorce with custody dispute. Both parents seeking primary custody of two minor children. Mother alleges domestic violence with medical records. Father claims fabricated evidence and seeks equal custody citing recent bonding time.",
        "outcome": "settled", "outcome_summary": "Joint custody awarded with primary residence with mother; father gets weekend and vacation custody; counseling mandated",
        "jurisdiction": "Family Court Mumbai", "year": 2022,
        "key_statutes": ["Hindu Marriage Act 1955 S.13", "Protection of Women from DV Act 2005", "Guardians and Wards Act 1890"],
        "dna_vector": [0.5, 0.6, 0.25, 0.5, 0.9, 0.3],
    },
    {
        "id": "HC005", "category": "consumer",
        "summary": "E-commerce platform delivered counterfeit luxury goods despite advertising authenticity guarantee. Consumer paid Rs. 85,000 for a handbag verified as fake by brand's authorized dealer. Platform's return window had expired due to their own shipping delays.",
        "outcome": "plaintiff_won", "outcome_summary": "Full refund plus Rs. 25,000 compensation for mental agony and unfair trade practice",
        "jurisdiction": "Consumer Forum Delhi", "year": 2023,
        "key_statutes": ["Consumer Protection Act 2019 S.2(47)", "E-Commerce Rules 2020"],
        "dna_vector": [0.9, 0.8, 0.5, 0.8, 0.4, 0.3],
    },
    {
        "id": "HC006", "category": "personal_injury",
        "summary": "Road accident caused by pothole on national highway. Motorcyclist sustained multiple fractures and permanent disability. NHAI claims regular maintenance; plaintiff produces RTI responses showing no maintenance for 14 months in that stretch.",
        "outcome": "plaintiff_won", "outcome_summary": "Rs. 32 lakh compensation for medical expenses, loss of earning capacity and pain & suffering",
        "jurisdiction": "Motor Accident Claims Tribunal", "year": 2022,
        "key_statutes": ["Motor Vehicles Act 1988 S.166", "NH Act 1956 S.7A"],
        "dna_vector": [0.4, 0.7, 0.75, 0.9, 0.6, 0.4],
    },
    {
        "id": "HC007", "category": "landlord_tenant",
        "summary": "Commercial tenant operating restaurant sublet part of premises to a cloud kitchen without landlord's consent. Lease expressly prohibits subletting. Tenant argues the cloud kitchen arrangement is a 'license' not a sublease.",
        "outcome": "defendant_won", "outcome_summary": "Court held subletting clause violated; eviction ordered with 3-month grace period",
        "jurisdiction": "Delhi High Court", "year": 2023,
        "key_statutes": ["Transfer of Property Act S.108(j)", "Delhi Rent Control Act S.14(1)(b)"],
        "dna_vector": [0.1, 0.9, 0.5, 0.7, 0.3, 0.5],
    },
    {
        "id": "HC008", "category": "employment",
        "summary": "Group of 23 contract workers at automobile factory seek permanent employment after working for 7 consecutive years through the same contractor. Company maintains they are contractor's employees. Workers prove they worked under company's direct supervision and used company tools.",
        "outcome": "plaintiff_won", "outcome_summary": "Workers deemed employees of principal employer; ordered to be regularized with back wages for 2 years",
        "jurisdiction": "Industrial Tribunal Chennai", "year": 2021,
        "key_statutes": ["Contract Labour Act 1970 S.10", "Industrial Disputes Act S.2(j)"],
        "dna_vector": [0.2, 0.7, 0.5, 0.7, 0.5, 0.3],
    },
    {
        "id": "HC009", "category": "property",
        "summary": "Ancestral property dispute between three siblings. Eldest brother claims sole ownership based on a contested will. Other siblings allege undue influence on elderly father and present evidence of altered documents. Property valued at Rs. 3.2 crore.",
        "outcome": "settled", "outcome_summary": "Equal three-way partition ordered; eldest brother's will declared not genuine; mediation achieved amicable division",
        "jurisdiction": "Civil Court Hyderabad", "year": 2022,
        "key_statutes": ["Indian Succession Act 1925", "Hindu Succession Act 1956 S.8", "Transfer of Property Act"],
        "dna_vector": [0.9, 0.6, 0.75, 0.6, 0.8, 0.4],
    },
    {
        "id": "HC010", "category": "contract",
        "summary": "IT services vendor failed to deliver committed cybersecurity audit for a bank within the SLA period. Bank suffered a data breach during the delay period. Vendor claims scope creep by bank's team made deadline impossible.",
        "outcome": "settled", "outcome_summary": "Vendor bore 60% liability for breach-related losses; penalized for SLA violation; contract renegotiated",
        "jurisdiction": "Arbitration Tribunal Mumbai", "year": 2023,
        "key_statutes": ["Indian Contract Act 1872 S.73", "IT Act 2000 S.43A", "Arbitration Act 1996"],
        "dna_vector": [0.3, 0.8, 0.75, 0.6, 0.4, 0.5],
    },
    {
        "id": "HC011", "category": "consumer",
        "summary": "Insurance company denied health claim citing pre-existing condition not disclosed. Policyholder proves the condition was diagnosed after policy inception and all premiums were paid for 5 years. Company's investigator relied on incorrect medical records.",
        "outcome": "plaintiff_won", "outcome_summary": "Full claim amount of Rs. 12 lakh settled plus Rs. 1 lakh for harassment and deficiency in service",
        "jurisdiction": "State Consumer Commission Kerala", "year": 2023,
        "key_statutes": ["Insurance Act 1938 S.45", "Consumer Protection Act 2019 S.38"],
        "dna_vector": [0.9, 0.7, 0.5, 0.8, 0.5, 0.3],
    },
    {
        "id": "HC012", "category": "small_claims",
        "summary": "Freelance graphic designer not paid for completed branding project. Client accepted all deliverables but disputes final invoice claiming work was substandard despite signed acceptance emails. Outstanding amount: Rs. 75,000.",
        "outcome": "plaintiff_won", "outcome_summary": "Full payment ordered plus 12% interest from due date; client to pay litigation costs",
        "jurisdiction": "Small Causes Court Pune", "year": 2023,
        "key_statutes": ["Indian Contract Act 1872 S.65", "CPC Order 37"],
        "dna_vector": [0.6, 0.7, 0.25, 0.8, 0.4, 0.2],
    },
    {
        "id": "HC013", "category": "employment",
        "summary": "Female employee filed sexual harassment complaint under POSH Act. Internal Committee found complaint valid but company transferred the complainant instead of the accused. Employee challenges retaliatory transfer.",
        "outcome": "plaintiff_won", "outcome_summary": "Transfer reversed; accused suspended; company fined for procedural violations under POSH Act",
        "jurisdiction": "High Court Delhi", "year": 2023,
        "key_statutes": ["POSH Act 2013 S.13", "Vishaka Guidelines"],
        "dna_vector": [0.2, 0.8, 0.25, 0.7, 0.9, 0.5],
    },
    {
        "id": "HC014", "category": "landlord_tenant",
        "summary": "Landlord increased rent by 85% mid-lease citing property valuation increase. Tenant refuses; landlord cuts water supply. Tenant documents 3 months of harassment including late-night visits and threats.",
        "outcome": "plaintiff_won", "outcome_summary": "Landlord ordered to restore services; rent increase capped at 10% per Rent Control Act; compensation for harassment",
        "jurisdiction": "Rent Controller Mumbai", "year": 2022,
        "key_statutes": ["Maharashtra Rent Control Act 1999 S.8", "IPC S.506"],
        "dna_vector": [0.1, 0.8, 0.25, 0.7, 0.9, 0.2],
    },
    {
        "id": "HC015", "category": "personal_injury",
        "summary": "Medical negligence case where patient underwent wrong-side knee surgery. Hospital initially denied error but operating theatre records confirmed the mistake. Patient required corrective surgery and 8 months additional recovery.",
        "outcome": "plaintiff_won", "outcome_summary": "Rs. 45 lakh compensation including corrective surgery costs, mental anguish, and loss of 8 months income",
        "jurisdiction": "National Consumer Commission", "year": 2023,
        "key_statutes": ["Consumer Protection Act 2019", "Indian Medical Council Regulations"],
        "dna_vector": [0.4, 0.8, 0.75, 0.9, 0.7, 0.6],
    },
    {
        "id": "HC016", "category": "contract",
        "summary": "Wedding event management company cancelled 2 days before the wedding date citing 'force majeure' (heavy rain forecast). Weather was normal on the wedding day. Couple had to arrange last-minute alternatives at 3x cost.",
        "outcome": "plaintiff_won", "outcome_summary": "Full refund plus Rs. 5 lakh compensation for mental distress; weather forecast does not constitute force majeure",
        "jurisdiction": "Consumer Forum Bangalore", "year": 2022,
        "key_statutes": ["Indian Contract Act 1872 S.56", "Consumer Protection Act 2019"],
        "dna_vector": [0.3, 0.7, 0.5, 0.8, 0.8, 0.5],
    },
    {
        "id": "HC017", "category": "property",
        "summary": "Developer sold same flat to two different buyers using separate agreements. Second buyer registered the sale deed first. First buyer has earlier agreement to sell and proof of full payment via bank transfers.",
        "outcome": "plaintiff_won", "outcome_summary": "First buyer declared rightful owner based on prior agreement and full consideration; developer convicted of fraud",
        "jurisdiction": "Civil Court Noida", "year": 2023,
        "key_statutes": ["Specific Relief Act 1963 S.16", "IPC S.420", "Registration Act 1908"],
        "dna_vector": [0.9, 0.7, 0.75, 0.8, 0.6, 0.5],
    },
    {
        "id": "HC018", "category": "family",
        "summary": "Maintenance petition by elderly parents against son who moved abroad. Son earns $120K annually but stopped financial support after marriage. Parents survive on meager pension and need medical care.",
        "outcome": "plaintiff_won", "outcome_summary": "Son ordered to pay Rs. 50,000 monthly maintenance; passport impounding threatened for non-compliance",
        "jurisdiction": "Maintenance Tribunal Delhi", "year": 2023,
        "key_statutes": ["Maintenance and Welfare of Parents Act 2007 S.4", "CrPC S.125"],
        "dna_vector": [0.5, 0.7, 0.5, 0.7, 0.8, 0.3],
    },
    {
        "id": "HC019", "category": "small_claims",
        "summary": "Online coaching platform refused refund after student found pre-recorded content was outdated by 3 years, contrary to advertisement of 'latest curriculum 2023'. Platform hides behind no-refund policy in fine print.",
        "outcome": "plaintiff_won", "outcome_summary": "Full refund ordered; unfair contract terms clause struck down; platform warned against misleading ads",
        "jurisdiction": "Consumer Forum Online", "year": 2023,
        "key_statutes": ["Consumer Protection Act 2019 S.2(46)", "E-Commerce Rules 2020 R.4"],
        "dna_vector": [0.6, 0.6, 0.25, 0.7, 0.5, 0.3],
    },
    {
        "id": "HC020", "category": "employment",
        "summary": "Delivery driver classified as 'independent contractor' by food delivery app seeks employee benefits after 3 years of full-time work. Proves company controls work hours, mandates uniform, imposes penalties for rejection of assignments.",
        "outcome": "pending", "outcome_summary": "Case pending; interim order granted minimum wage protection pending final determination",
        "jurisdiction": "Labour Court Delhi", "year": 2024,
        "key_statutes": ["Code on Social Security 2020 S.2(35)", "EPF Act 1952"],
        "dna_vector": [0.2, 0.6, 0.25, 0.6, 0.5, 0.8],
    },
    {
        "id": "HC021", "category": "consumer",
        "summary": "Bank charged hidden processing fees, documentation charges, and insurance premium on a home loan without explicit consent. Borrower discovers Rs. 2.8 lakh in undisclosed charges embedded in the loan disbursement.",
        "outcome": "plaintiff_won", "outcome_summary": "All hidden charges reversed; bank fined Rs. 10 lakh for unfair trade practice; directed to issue revised account statement",
        "jurisdiction": "Banking Ombudsman RBI", "year": 2023,
        "key_statutes": ["Banking Regulation Act S.35A", "RBI Fair Practices Code", "Consumer Protection Act 2019"],
        "dna_vector": [0.9, 0.8, 0.5, 0.8, 0.5, 0.3],
    },
    {
        "id": "HC022", "category": "landlord_tenant",
        "summary": "PG accommodation operator evicted 15 tenants overnight by changing locks citing 'renovation needed'. Tenants' belongings held hostage until they signed no-claim agreements. Several tenants were women living alone.",
        "outcome": "plaintiff_won", "outcome_summary": "Immediate access restored; operator fined for illegal eviction; compensation of Rs. 20,000 per tenant ordered",
        "jurisdiction": "Metropolitan Magistrate Bangalore", "year": 2023,
        "key_statutes": ["Karnataka Rent Act 1999 S.27", "IPC S.441", "IPC S.503"],
        "dna_vector": [0.1, 0.7, 0.25, 0.8, 0.9, 0.4],
    },
    {
        "id": "HC023", "category": "personal_injury",
        "summary": "Factory worker lost three fingers in an industrial accident due to missing safety guards on machinery. Employer had received 2 prior warnings from factory inspector about the same machine. Worker seeks compensation for permanent disability.",
        "outcome": "plaintiff_won", "outcome_summary": "Rs. 28 lakh compensation including disability pension; factory license suspended for 6 months; mandatory safety audit ordered",
        "jurisdiction": "Commissioner for Workmen's Compensation", "year": 2022,
        "key_statutes": ["Factories Act 1948 S.21", "Employee Compensation Act 1923 S.4", "OSH Code 2020"],
        "dna_vector": [0.4, 0.8, 0.5, 0.9, 0.6, 0.3],
    },
    {
        "id": "HC024", "category": "contract",
        "summary": "Startup founder's non-compete agreement prevents joining any tech company for 2 years after leaving. Former employer sues when founder starts a competing SaaS product. Founder argues non-compete is unreasonable restraint of trade.",
        "outcome": "defendant_won", "outcome_summary": "Non-compete held void under Section 27; founder allowed to continue but ordered not to solicit former employer's clients for 6 months",
        "jurisdiction": "High Court Bombay", "year": 2023,
        "key_statutes": ["Indian Contract Act 1872 S.27", "Specific Relief Act 1963 S.14"],
        "dna_vector": [0.3, 0.9, 0.5, 0.6, 0.4, 0.7],
    },
    {
        "id": "HC025", "category": "family",
        "summary": "NRI husband filed for divorce in US court while wife in India seeks maintenance under Indian law. Husband claims US court jurisdiction; wife argues matrimonial home was India and marriage was solemnized under Hindu rites.",
        "outcome": "settled", "outcome_summary": "Indian court assumed jurisdiction; mutual consent divorce with Rs. 75 lakh one-time settlement and child's education fund",
        "jurisdiction": "Family Court Delhi", "year": 2023,
        "key_statutes": ["Hindu Marriage Act S.13", "CPC S.9", "Family Courts Act 1984"],
        "dna_vector": [0.5, 0.5, 0.75, 0.5, 0.7, 0.5],
    },
]


# ─── Demo Active Cases ──────────────────────────────────────────────
DEMO_CASES = [
    {
        "title": "Gupta v. Skyline Realty - Delayed Possession",
        "description": "Homebuyer Ramesh Gupta purchased a 3BHK flat in Skyline Heights for Rs. 95 lakhs in 2020 with promised possession by March 2023. Builder has missed deadline by 18 months with no communication. Flat is still under construction. Buyer has been paying EMI of Rs. 45,000 monthly while also paying rent of Rs. 25,000. Builder denies delay, blaming COVID and cement shortage.",
        "category": "property", "jurisdiction": "RERA Noida",
        "claim_amount": 2500000, "plaintiff": "Ramesh Gupta", "defendant": "Skyline Realty Pvt Ltd",
    },
    {
        "title": "Sharma v. TechCorp - Wrongful Termination",
        "description": "Senior developer Priya Sharma was terminated after 5 years of service, 2 weeks after filing a complaint about unpaid overtime. Company cites 'restructuring' but hired 3 new developers at lower salaries immediately after. Sharma has email evidence of manager threatening her job after overtime complaint.",
        "category": "employment", "jurisdiction": "Labour Court Bangalore",
        "claim_amount": 1800000, "plaintiff": "Priya Sharma", "defendant": "TechCorp India Ltd",
    },
    {
        "title": "Kumar v. Kumar - Inheritance Dispute",
        "description": "Three brothers disputing father's ancestral house in Old Delhi valued at Rs. 4 crore. Eldest brother Vikram claims exclusive possession based on oral promise. Middle brother Raj has been maintaining the property and paying taxes for 15 years. Youngest brother Arjun was excluded from family discussions. No written will exists.",
        "category": "property", "jurisdiction": "Civil Court Delhi",
        "claim_amount": 40000000, "plaintiff": "Raj Kumar", "defendant": "Vikram Kumar",
    },
    {
        "title": "Singh v. MedCare Hospital - Negligence",
        "description": "Patient Harpreet Singh underwent routine appendectomy but surgical sponge was left inside abdomen. Discovered 3 months later after persistent pain and infection. Required second surgery and 6 weeks hospitalization. Patient lost 4 months of work as a taxi driver. Hospital initially denied negligence until sponge was removed and documented.",
        "category": "personal_injury", "jurisdiction": "Consumer Forum Chandigarh",
        "claim_amount": 3500000, "plaintiff": "Harpreet Singh", "defendant": "MedCare Super Specialty Hospital",
    },
    {
        "title": "Patel v. QuickDeliver - Labour Misclassification",
        "description": "Delivery executive Mehul Patel worked 10-hour shifts for QuickDeliver app for 2 years, classified as 'partner' not employee. Denied PF, ESI, and paid leave. After accident during delivery, app refused to cover medical expenses citing independent contractor status. Patel proves app controlled routes, timings, and imposed penalties.",
        "category": "employment", "jurisdiction": "Labour Court Mumbai",
        "claim_amount": 800000, "plaintiff": "Mehul Patel", "defendant": "QuickDeliver Technologies",
    },
]


def seed_all() -> tuple[int, int, int]:
    """Seed all demo data. Returns (case_count, entity_count, edge_count)."""
    from db.database import get_connection
    conn = get_connection()

    # Check if already seeded
    existing = conn.execute("SELECT COUNT(*) FROM historical_cases").fetchone()[0]
    if existing >= 20:
        conn.close()
        return (0, 0, 0)

    conn.close()

    # Seed historical cases
    for hc in HISTORICAL_CASES:
        insert_historical_case(
            case_id=hc["id"],
            summary=hc["summary"],
            category=hc["category"],
            outcome=hc["outcome"],
            dna_vector=hc["dna_vector"],
            jurisdiction=hc["jurisdiction"],
            year=hc["year"],
            outcome_summary=hc.get("outcome_summary", ""),
            key_statutes=hc.get("key_statutes", []),
        )

    # Seed demo active cases
    case_ids = []
    for dc in DEMO_CASES:
        cid = insert_case(
            title=dc["title"],
            description=dc["description"],
            category=dc["category"],
            jurisdiction=dc["jurisdiction"],
            claim_amount=dc["claim_amount"],
            plaintiff_name=dc["plaintiff"],
            defendant_name=dc["defendant"],
        )
        case_ids.append(cid)

    # Count entities and edges
    conn = get_connection()
    entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM case_edges").fetchone()[0]
    conn.close()

    return (len(HISTORICAL_CASES) + len(DEMO_CASES), entity_count, edge_count)
