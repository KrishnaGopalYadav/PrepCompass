"""Versioned, source-linked syllabus catalogue.

Only syllabus headings represented in the cited examination documents are seeded here.
The catalogue is cycle-specific; a past-cycle source is never silently promoted to 2028.
"""
import sqlite3
from datetime import datetime, timezone

SOURCES = [
    {
        "source_id": "upsc-cse-2026-notice",
        "exam_id": "upsc_cse",
        "cycle_year": 2026,
        "title": "Civil Services Examination 2026 — Examination Notice No. 05/2026-CSE",
        "issuing_body": "Union Public Service Commission",
        "document_url": "https://www.upsc.gov.in/sites/default/files/Notif-CSP-2026-Engl-060226Rev.pdf",
        "landing_url": "https://www.upsc.gov.in/examinations/Civil%20Services%20%28Preliminary%29%20Examination%2C%202026",
        "publication_date": "2026-02-04",
        "source_kind": "official_notice",
        "verification_status": "official_publisher",
        "notes": "Official UPSC notice. Syllabus is in Appendix I, Section III. Use as a 2026 baseline only; refresh against the applicable 2028 notice before exam-specific scheduling.",
    },
    {
        "source_id": "upsc-ifos-2026-rules",
        "exam_id": "upsc_ifos",
        "cycle_year": 2026,
        "title": "Indian Forest Service Examination 2026 Rules",
        "issuing_body": "Ministry of Environment, Forest and Climate Change / Government of India",
        "document_url": "https://egazette.gov.in/WriteReadData/2026/269830.pdf",
        "landing_url": "https://egazette.gov.in/",
        "publication_date": "2026-02-04",
        "source_kind": "gazette_notification",
        "verification_status": "official_publisher",
        "notes": "Official Gazette of India notification. The IFoS preliminary stage uses the Civil Services Preliminary Examination. Main syllabus and optional subject rules are in the Gazette appendices. Refresh for 2028.",
    },
    {
        "source_id": "uppsc-combined-2025-notice",
        "exam_id": "uppsc_pcs",
        "cycle_year": 2025,
        "title": "UPPSC Combined State / Upper Subordinate Services and ACF/RFO Services Examination 2025 — Advertisement A-1/E-1/2025",
        "issuing_body": "Uttar Pradesh Public Service Commission",
        "document_url": "https://cdn-images.prepp.in/public/image/View_Enclosure_UPPSC_Notification_ce87c8a0e4cc86ea56b1eec167db36b9.pdf",
        "landing_url": "https://uppsc.up.nic.in/Home",
        "publication_date": "2025-02-20",
        "source_kind": "official_notification_copy_mirrored",
        "verification_status": "official_document_copy_mirrored",
        "notes": "The PDF text identifies UPPSC Advertisement A-1/E-1/2025. The accessible copy is hosted by a third-party mirror, not the Commission domain; treat it as a transcription/reference copy and confirm the same document on the UPPSC portal before relying on it for a live cycle.",
    },
    {
        "source_id": "uppsc-acf-rfo-2025-appendices",
        "exam_id": "uppsc_acf_rfo",
        "cycle_year": 2025,
        "title": "UPPSC ACF/RFO Services Examination 2025 — Appendices 3, 5 and 6 of Advertisement A-1/E-1/2025",
        "issuing_body": "Uttar Pradesh Public Service Commission",
        "document_url": "https://cdn-images.prepp.in/public/image/View_Enclosure_UPPSC_Notification_ce87c8a0e4cc86ea56b1eec167db36b9.pdf",
        "landing_url": "https://uppsc.up.nic.in/Home",
        "publication_date": "2025-02-20",
        "source_kind": "official_notification_copy_mirrored",
        "verification_status": "official_document_copy_mirrored",
        "notes": "The accessible copy includes the common preliminary syllabus, ACF/RFO main scheme, optional subject list and optional subject syllabus. Verify the official UPPSC-hosted notice and the applicable recruitment rules before using for a live cycle.",
    },
]

# Each node is tied to one source and one paper/stage. Parent IDs express hierarchy.
NODES = [
    # CSE
    ("cse-pre", None, "preliminary", "GS-I", "General Studies Paper I", "Current events; Indian history and national movement; Indian and world geography; polity and governance; economic and social development; environment, biodiversity and climate change; general science.", 1, "paper"),
    ("cse-pre-current", "cse-pre", "preliminary", "GS-I", "Current events of national and international importance", "Current events of national and international importance.", 1, "topic"),
    ("cse-pre-history", "cse-pre", "preliminary", "GS-I", "History of India and Indian National Movement", "History of India and the Indian National Movement.", 2, "topic"),
    ("cse-pre-geography", "cse-pre", "preliminary", "GS-I", "Indian and World Geography", "Physical, social and economic geography of India and the world.", 3, "topic"),
    ("cse-pre-polity", "cse-pre", "preliminary", "GS-I", "Indian Polity and Governance", "Constitution, political system, Panchayati Raj, public policy and rights issues.", 4, "topic"),
    ("cse-pre-economy", "cse-pre", "preliminary", "GS-I", "Economic and Social Development", "Sustainable development, poverty, inclusion, demographics and social sector initiatives.", 5, "topic"),
    ("cse-pre-environment", "cse-pre", "preliminary", "GS-I", "Environment, Biodiversity and Climate Change", "General issues not requiring subject specialisation.", 6, "topic"),
    ("cse-pre-science", "cse-pre", "preliminary", "GS-I", "General Science", "General Science.", 7, "topic"),
    ("cse-csat", None, "preliminary", "GS-II", "General Studies Paper II (CSAT)", "Comprehension, interpersonal skills, logical reasoning, decision making, general mental ability, basic numeracy and data interpretation. Qualifying paper; minimum 33%.", 2, "paper"),
    ("cse-mains-essay", None, "mains", "P-I", "Essay", "Essay paper.", 1, "paper"),
    ("cse-mains-gs1", None, "mains", "GS-I", "Indian Heritage, History, Society and Geography", "Indian culture; modern and world history; Indian society; physical, world and Indian geography.", 2, "paper"),
    ("cse-mains-gs2", None, "mains", "GS-II", "Governance, Constitution, Polity, Social Justice and International Relations", "Constitution, governance, social justice and international relations.", 3, "paper"),
    ("cse-mains-gs3", None, "mains", "GS-III", "Technology, Economic Development, Biodiversity, Environment, Security and Disaster Management", "Economy, agriculture, science and technology, environment, disaster management and internal security.", 4, "paper"),
    ("cse-mains-gs4", None, "mains", "GS-IV", "Ethics, Integrity and Aptitude", "Ethics and human interface, attitude, aptitude, emotional intelligence, public service values, probity and case studies.", 5, "paper"),
    ("cse-mains-optional", None, "mains", "P-VI/VII", "Optional Subject Papers", "Two papers in one optional subject selected from the CSE notification's list; do not assume IFoS optionals apply.", 6, "paper"),
    ("cse-mains-language", None, "mains", "Qualifying", "Indian Language and English", "Qualifying language papers as specified in the applicable CSE notice.", 7, "paper"),
    ("cse-interview", None, "interview", "Personality Test", "Interview / Personality Test", "Personality assessment described in the CSE notice.", 8, "paper"),

    # IFoS
    ("ifos-pre", None, "preliminary", "CSE Prelims", "Civil Services Preliminary Examination (screening)", "IFoS screening uses the Civil Services Preliminary Examination: GS Paper I and qualifying GS Paper II.", 1, "paper"),
    ("ifos-main-english", None, "mains", "Paper I", "General English", "Compulsory General English paper, 300 marks in the 2026 rules.", 2, "paper"),
    ("ifos-main-gk", None, "mains", "Paper II", "General Knowledge", "Compulsory General Knowledge paper, 300 marks in the 2026 rules.", 3, "paper"),
    ("ifos-forestry", None, "mains", "Optional: Forestry", "Forestry (two papers)", "Optional subject with Paper I and Paper II. Includes silviculture, agroforestry, soils, watershed, forest management, protection, wildlife, economics and legislation.", 4, "optional"),
    ("ifos-forestry-silvi", "ifos-forestry", "mains", "Forestry Paper I", "Silviculture and silvicultural systems", "General silvicultural principles, regeneration, nursery and planting, tending, forest types and silvicultural systems.", 1, "topic"),
    ("ifos-forestry-agro", "ifos-forestry", "mains", "Forestry Paper I", "Agroforestry, social forestry and joint forest management", "Agroforestry, social/urban forestry, people's participation and joint forest management.", 2, "topic"),
    ("ifos-forestry-soils", "ifos-forestry", "mains", "Forestry Paper I", "Forest soils, soil conservation and watershed management", "Forest soil properties, erosion, soil conservation, watershed development and forest hydrology.", 3, "topic"),
    ("ifos-forestry-mgmt", "ifos-forestry", "mains", "Forestry Paper II", "Forest management and mensuration", "Forest management, working plans, inventory and mensuration.", 4, "topic"),
    ("ifos-forestry-protect", "ifos-forestry", "mains", "Forestry Paper II", "Forest protection and wildlife biology", "Forest injuries, pests, diseases, fire, grazing, wildlife impacts and protection.", 5, "topic"),
    ("ifos-forestry-law", "ifos-forestry", "mains", "Forestry Paper II", "Forest economics and legislation", "Forest economics, policies, Indian forest laws, conservation and wildlife legislation.", 6, "topic"),
    ("ifos-geology", None, "mains", "Optional: Geology", "Geology (two papers)", "Optional subject with Paper I and Paper II.", 5, "optional"),
    ("ifos-geology-general", "ifos-geology", "mains", "Geology Paper I", "General Geology", "Earth origin and interior, volcanism, earthquakes, plate tectonics and geologic processes.", 1, "topic"),
    ("ifos-geology-geomorph", "ifos-geology", "mains", "Geology Paper I", "Geomorphology and Remote Sensing", "Landforms, weathering, drainage, geomorphic cycles, remote sensing, GIS and GPS.", 2, "topic"),
    ("ifos-geology-structural", "ifos-geology", "mains", "Geology Paper I", "Structural Geology", "Geologic mapping, stress and strain, folds, faults, foliations and structural analysis.", 3, "topic"),
    ("ifos-geology-paleo", "ifos-geology", "mains", "Geology Paper I", "Paleontology", "Fossil preservation, microfossils, fossil groups and evolutionary trends.", 4, "topic"),
    ("ifos-geology-strat", "ifos-geology", "mains", "Geology Paper I", "Stratigraphy and Geology of India", "Stratigraphic classification, Indian geological sequences and Himalayan evolution.", 5, "topic"),
    ("ifos-geology-hydro", "ifos-geology", "mains", "Geology Paper I", "Hydrogeology and Engineering Geology", "Groundwater, aquifers, recharge, geological investigations, landslides and engineering properties of rocks.", 6, "topic"),
    ("ifos-interview", None, "interview", "Personality Test", "Interview / Personality Test", "Personality test as prescribed in the IFoS rules.", 6, "paper"),

    # UPPSC PCS
    ("pcs-pre-gs1", None, "preliminary", "GS-I", "General Studies Paper I", "Current events, history, geography, polity, economy and social development, environment and general science.", 1, "paper"),
    ("pcs-pre-csat", None, "preliminary", "GS-II", "General Studies Paper II", "Comprehension, communication, reasoning, decision making, mental ability, elementary mathematics, General English and General Hindi at the prescribed level.", 2, "paper"),
    ("pcs-mains-hindi", None, "mains", "Paper I", "General Hindi", "Compulsory General Hindi paper.", 1, "paper"),
    ("pcs-mains-essay", None, "mains", "Paper II", "Essay", "Compulsory essay paper.", 2, "paper"),
    ("pcs-mains-gs1", None, "mains", "GS-I", "General Studies Paper I", "History, Indian national movement and culture, population, environment, urbanisation, geography, current events, agriculture, trade and Uttar Pradesh-specific knowledge.", 3, "paper"),
    ("pcs-mains-gs2", None, "mains", "GS-II", "General Studies Paper II", "Constitution, governance, social justice, international relations and related topics as specified in the notice.", 4, "paper"),
    ("pcs-mains-gs3", None, "mains", "GS-III", "General Studies Paper III", "Economy, agriculture, science and technology, environment, security and disaster-related themes as specified in the notice.", 5, "paper"),
    ("pcs-mains-gs4", None, "mains", "GS-IV", "General Studies Paper IV", "Ethics, integrity and aptitude as specified in the notice.", 6, "paper"),
    ("pcs-mains-gs5", None, "mains", "GS-V", "General Studies Paper V", "Uttar Pradesh history, culture, society, polity, governance, security, health, education and current affairs.", 7, "paper"),
    ("pcs-mains-gs6", None, "mains", "GS-VI", "General Studies Paper VI", "Uttar Pradesh economy, budget, agriculture, forestry, geography, natural resources, environment and infrastructure.", 8, "paper"),
    ("pcs-interview", None, "interview", "Personality Test", "Personality Test", "Personality test as specified in the applicable UPPSC notice.", 9, "paper"),

    # UPPSC ACF/RFO
    ("acf-pre-gs1", None, "preliminary", "GS-I", "Common Preliminary General Studies Paper I", "The 2025 UPPSC notice states the same Appendix-3 preliminary syllabus applies to PCS and ACF/RFO.", 1, "paper"),
    ("acf-pre-gs2", None, "preliminary", "GS-II", "Common Preliminary General Studies Paper II", "The 2025 UPPSC notice states the same Appendix-3 preliminary syllabus applies to PCS and ACF/RFO.", 2, "paper"),
    ("acf-main-hindi-essay", None, "mains", "Paper I", "General Hindi and Essay", "Compulsory paper in the 2025 ACF/RFO scheme.", 1, "paper"),
    ("acf-main-gs1", None, "mains", "Paper II", "General Studies Paper I", "Compulsory General Studies paper.", 2, "paper"),
    ("acf-main-gs2", None, "mains", "Paper III", "General Studies Paper II", "Compulsory General Studies paper.", 3, "paper"),
    ("acf-main-optional-forestry", None, "mains", "Optional Subject", "Forestry (two papers)", "Listed optional subject in the 2025 ACF/RFO notice; verify subject-combination rules in the applicable cycle.", 4, "optional"),
    ("acf-main-optional-geology", None, "mains", "Optional Subject", "Geology (two papers)", "Listed optional subject in the 2025 ACF/RFO notice; verify subject-combination rules in the applicable cycle.", 5, "optional"),
    ("acf-main-gs-up", None, "mains", "Appendix 6: GS-V / GS-VI", "Uttar Pradesh-specific General Studies", "UP history, society, governance, economy, forestry, agriculture, geography, natural resources and environment topics in the 2025 ACF/RFO appendices.", 6, "paper"),
    ("acf-interview", None, "interview", "Personality Test", "Interview / Personality Test", "Personality test as specified in the applicable UPPSC ACF/RFO notice.", 7, "paper"),
]

# Explicit crosswalks only where the source documents state the same screening syllabus.
CROSSWALKS = [
    ("cse-pre", "ifos-pre", "same_exam_stage", "IFoS 2026 rules use the Civil Services Preliminary Examination for screening."),
    ("cse-csat", "ifos-pre", "shared_screening_component", "Both examinations use the CSE Preliminary GS Paper II as a qualifying paper; detailed paper linkage is shown in the IFoS rules."),
    ("pcs-pre-gs1", "acf-pre-gs1", "same_notice_appendix", "UPPSC 2025 Appendix 3 explicitly applies to both PCS and ACF/RFO."),
    ("pcs-pre-csat", "acf-pre-gs2", "same_notice_appendix", "UPPSC 2025 Appendix 3 explicitly applies to both PCS and ACF/RFO."),
]


def ensure_syllabus_schema(database_path: str) -> None:
    with sqlite3.connect(database_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS syllabus_sources (
            source_id TEXT PRIMARY KEY,
            exam_id TEXT NOT NULL,
            cycle_year INTEGER NOT NULL,
            title TEXT NOT NULL,
            issuing_body TEXT NOT NULL,
            document_url TEXT NOT NULL,
            landing_url TEXT NOT NULL,
            publication_date TEXT,
            source_kind TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            UNIQUE(exam_id, cycle_year, title)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS syllabus_nodes (
            node_id TEXT PRIMARY KEY,
            exam_id TEXT NOT NULL,
            source_id TEXT NOT NULL REFERENCES syllabus_sources(source_id),
            parent_node_id TEXT REFERENCES syllabus_nodes(node_id),
            stage TEXT NOT NULL,
            paper_code TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            node_type TEXT NOT NULL DEFAULT 'topic',
            UNIQUE(node_id, source_id)
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syllabus_nodes_exam_stage ON syllabus_nodes(exam_id, stage, sort_order)")
        conn.execute("""CREATE TABLE IF NOT EXISTS syllabus_crosswalks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id TEXT NOT NULL REFERENCES syllabus_nodes(node_id),
            target_node_id TEXT NOT NULL REFERENCES syllabus_nodes(node_id),
            relation TEXT NOT NULL,
            rationale TEXT NOT NULL,
            UNIQUE(source_node_id, target_node_id, relation)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS candidate_optional_subjects (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exam_id TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(user_id, exam_id, subject_code)
        )""")
        conn.commit()


def seed_syllabus_catalog(database_path: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(database_path) as conn:
        for source in SOURCES:
            conn.execute(
                """INSERT OR IGNORE INTO syllabus_sources
                (source_id,exam_id,cycle_year,title,issuing_body,document_url,landing_url,publication_date,
                 source_kind,verification_status,notes,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*[source[k] for k in ("source_id","exam_id","cycle_year","title","issuing_body","document_url","landing_url","publication_date","source_kind","verification_status","notes")], now),
            )
        source_for_exam = {s["exam_id"]: s["source_id"] for s in SOURCES}
        for node in NODES:
            node_id, parent, stage, paper, title, description, order, node_type = node
            exam_id = "upsc_cse" if node_id.startswith("cse-") else "upsc_ifos" if node_id.startswith("ifos-") else "uppsc_pcs" if node_id.startswith("pcs-") else "uppsc_acf_rfo"
            conn.execute(
                """INSERT OR IGNORE INTO syllabus_nodes
                (node_id,exam_id,source_id,parent_node_id,stage,paper_code,title,description,sort_order,node_type)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (node_id, exam_id, source_for_exam[exam_id], parent, stage, paper, title, description, order, node_type),
            )
        for left, right, relation, rationale in CROSSWALKS:
            conn.execute(
                "INSERT OR IGNORE INTO syllabus_crosswalks(source_node_id,target_node_id,relation,rationale) VALUES (?,?,?,?)",
                (left, right, relation, rationale),
            )
        conn.commit()
