"""Curated, provenance-aware source and PYQ catalogue.

This module stores discovery metadata and source links only. It deliberately does not
mirror copyrighted books, coaching PDFs, or complete third-party question banks.
"""
import sqlite3
from datetime import datetime, timezone

SOURCES = [
    ("upsc-pyq-current", "UPSC Previous Question Papers", "exam_authority", "https://www.upsc.gov.in/exam-documents/question-papers/", "https://www.upsc.gov.in/examinations/previous-question-papers", "official", "daily", "CSE, IFoS and other UPSC exams", "Question-paper landing page; discover year/exam/paper links from the official portal."),
    ("upsc-pyq-archive", "UPSC Previous Question Papers Archives", "exam_authority", "https://www.upsc.gov.in/archived-exam-documents/question-papers/", "https://www.upsc.gov.in/examinations/previous-question-papers/archives", "official", "weekly", "CSE, IFoS and other UPSC exams", "Historical papers; archive coverage and link availability vary by year."),
    ("upsc-exam-details", "UPSC Previous Exam Details", "exam_authority", "https://upsc.gov.in/previous-exam-details/", "https://upsc.gov.in/previous-exam-details/", "official", "weekly", "UPSC exams", "Question papers, answer keys, cut-offs, notices and results where published."),
    ("uppsc-pyq", "UPPSC Previous Year Question Papers", "exam_authority", "https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues", "https://uppsc.up.nic.in/Home", "official", "daily", "PCS, ACF/RFO and other UPPSC exams", "Portal has exam/year/paper filters; visible papers and expiry windows change."),
    ("upsc-notifications", "UPSC Examination Notifications", "exam_authority", "https://upsc.gov.in/examinations", "https://upsc.gov.in/", "official", "daily", "CSE and IFoS", "Use the target-cycle notification as the legal source of scheme, syllabus and eligibility."),
    ("uppsc-notifications", "UPPSC Notifications and Advertisements", "exam_authority", "https://uppsc.up.nic.in/", "https://uppsc.up.nic.in/", "official", "daily", "PCS and ACF/RFO", "Verify the exact advertisement, corrigenda and recruitment rules on the Commission portal."),
    ("egazette", "Gazette of India", "gazette", "https://egazette.gov.in/", "https://egazette.gov.in/", "official", "daily", "CSE, IFoS, laws and policies", "Primary legal notifications, rules and amendments."),
    ("pib", "Press Information Bureau", "government_news", "https://www.pib.gov.in/", "https://www.pib.gov.in/allRelease.aspx?lang=1&reg=1", "official", "daily", "GS, current affairs, schemes", "Government releases and explainers; corroborate claims against originating ministry documents."),
    ("indiabudget", "Union Budget Documents", "government_report", "https://www.indiabudget.gov.in/", "https://www.indiabudget.gov.in/", "official", "annual", "Economy, governance, social sector", "Budget speech, expenditure, receipts, FRBM statements and outcome documents."),
    ("economic-survey", "Economic Survey of India", "government_report", "https://www.indiabudget.gov.in/economicsurvey/", "https://www.indiabudget.gov.in/", "official", "annual", "Economy, agriculture, social development", "Annual analytical source; retain edition and chapter/page metadata."),
    ("mospi-reports", "MoSPI Publications and Reports", "government_statistics", "https://mospi.gov.in/publications-reports", "https://mospi.gov.in/", "official", "monthly", "Economy, social statistics, demography", "Survey reports and official statistical publications; check data dissemination terms."),
    ("data-gov-in", "Open Government Data Platform India", "government_dataset", "https://www.data.gov.in/", "https://www.data.gov.in/", "official", "weekly", "Economy, agriculture, health, environment", "Dataset-level licence/terms and update frequency must be checked before reuse."),
    ("rbi-publications", "Reserve Bank of India Publications", "regulator_report", "https://www.rbi.org.in/scripts/Publications.aspx", "https://www.rbi.org.in/scripts/Publications.aspx", "official", "monthly", "Economy, banking, finance", "Annual reports, monetary policy, financial stability, state finances and handbooks."),
    ("rbi-dbie", "RBI Database on Indian Economy", "government_dataset", "https://data.rbi.org.in/", "https://data.rbi.org.in/", "official", "monthly", "Macroeconomy, banking, external sector", "Structured time series; capture series ID, unit, base year and reference period."),
    ("niti-reports", "NITI Aayog Reports", "government_report", "https://www.niti.gov.in/documents/reports", "https://www.niti.gov.in/", "official", "monthly", "Governance, economy, social sector, SDGs", "Policy reports and indices; capture report edition and methodology."),
    ("moefcc", "Ministry of Environment, Forest and Climate Change", "ministry", "https://moef.gov.in/", "https://moef.gov.in/", "official", "weekly", "Environment, biodiversity, climate, forestry", "Notifications, rules, schemes, reports and national commitments."),
    ("fsi-isfr", "Forest Survey of India — India State of Forest Report", "government_report", "https://www.fsi.nic.in/forest-report-2023", "https://www.fsi.nic.in/reports-publications", "official", "biennial", "IFoS, ACF/RFO, environment", "ISFR 2023 page includes forest/tree/mangrove and carbon-stock datasets."),
    ("icfre-nirantar", "ICFRE NIRANTAR Research and Publications Portal", "research_repository", "https://www.nirantar.moef.gov.in/integrated-portal", "https://www.nirantar.moef.gov.in/integrated-portal", "official", "monthly", "Forestry, ecology, environment", "Research and publications from MoEFCC institutes; verify document-specific rights."),
    ("ncert-textbooks", "NCERT Online Textbooks", "textbook_catalogue", "https://ncert.nic.in/textbook.php", "https://ncert.nic.in/textbook.php", "official", "annual", "History, geography, polity, economy, science", "Copyrighted textbooks: link users to NCERT; do not redistribute or bundle copies."),
    ("epathshala", "NCERT ePathshala", "educational_repository", "https://epathshala.nic.in/", "https://www.ciet.ncert.gov.in/initiative/epathshala", "official", "monthly", "School-level foundation and reference", "Digital educational resources; respect item-level terms."),
    ("prs", "PRS Legislative Research", "secondary_analysis", "https://prsindia.org/", "https://prsindia.org/acts/parliament", "secondary", "weekly", "Polity, governance, laws, Parliament", "Independent non-government analysis; use as secondary context and verify laws on official sources."),
    ("supreme-court", "Supreme Court of India Judgments", "judiciary", "https://www.sci.gov.in/judgements-judgement-date/", "https://www.sci.gov.in/", "official", "weekly", "Polity, governance, rights, environment", "Judgment metadata and primary text; retain case number, date and paragraph locator."),
    ("indiacode", "India Code — Central Acts", "legal_repository", "https://www.indiacode.nic.in/", "https://www.indiacode.nic.in/", "official", "weekly", "Polity, governance, environment, economy", "Central Acts and amendments; check commencement and amendment status."),
    ("up-gov", "Government of Uttar Pradesh", "state_government", "https://up.gov.in/", "https://up.gov.in/", "official", "weekly", "UPPCS, UP economy, schemes, geography", "State policies, budget, departments and official statistics."),
    ("up-budget", "Uttar Pradesh Budget", "state_government_report", "https://budget.up.nic.in/", "https://budget.up.nic.in/", "official", "annual", "UP economy, agriculture, social sector", "Budget documents and demands for grants; preserve fiscal year."),
    ("up-economic-survey", "Uttar Pradesh Economic Survey / Economic Review", "state_government_report", "https://up.gov.in/", "https://up.gov.in/", "official", "annual", "UPPCS economy, agriculture, demographics", "Discover current edition through state portal; do not assume a stable deep link."),
    ("imd", "India Meteorological Department", "technical_agency", "https://mausam.imd.gov.in/", "https://mausam.imd.gov.in/", "official", "daily", "Geography, climate, disaster management", "Weather/climate bulletins and reports; distinguish forecast from observed data."),
    ("isro", "Indian Space Research Organisation", "technical_agency", "https://www.isro.gov.in/", "https://www.isro.gov.in/Media.html", "official", "weekly", "Science and technology, space", "Mission updates and technical publications."),
    ("moa", "Ministry of Agriculture and Farmers Welfare", "ministry", "https://agriwelfare.gov.in/", "https://agriwelfare.gov.in/", "official", "weekly", "Agriculture, economy, food security", "Schemes, crop statistics, annual reports and policy documents."),
    ("mha", "Ministry of Home Affairs", "ministry", "https://www.mha.gov.in/", "https://www.mha.gov.in/", "official", "weekly", "Internal security, disaster management, governance", "Annual reports, acts, advisories and security-related official releases."),
    ("mea", "Ministry of External Affairs", "ministry", "https://www.mea.gov.in/", "https://www.mea.gov.in/press-releases.htm", "official", "daily", "International relations", "Official bilateral/multilateral statements and agreements."),
    ("cag", "Comptroller and Auditor General of India", "constitutional_auditor", "https://cag.gov.in/en/audit-report", "https://cag.gov.in/", "official", "monthly", "Governance, public finance, accountability", "Audit reports with report number, state/union, table and paragraph metadata."),
    ("parliament", "Digital Sansad", "parliament", "https://sansad.in/", "https://sansad.in/", "official", "weekly", "Polity, governance, legislation", "Questions, debates, committee reports and parliamentary documents."),
]

PYQ_COLLECTIONS = [
    ("upsc-cse-prelims", "upsc_cse", "preliminary", "UPSC Civil Services Preliminary Examination — GS Paper I and CSAT", "https://www.upsc.gov.in/examinations/previous-question-papers", "https://www.upsc.gov.in/examinations/previous-question-papers/archives", "", "Official portal current and archive listings; confirm each paper's presence before marking acquired."),
    ("upsc-cse-mains", "upsc_cse", "mains", "UPSC Civil Services Main Examination — Essay, GS I–IV, language and optional papers", "https://www.upsc.gov.in/examinations/previous-question-papers", "https://www.upsc.gov.in/examinations/previous-question-papers/archives", "", "Discover paper/year links dynamically; optional and language paper coverage varies."),
    ("upsc-ifos-prelims", "upsc_ifos", "preliminary", "IFoS screening — common Civil Services Preliminary papers", "https://www.upsc.gov.in/examinations/previous-question-papers", "https://www.upsc.gov.in/examinations/previous-question-papers/archives", "", "Shared paper assets should reference the CSE paper record rather than duplicate binaries; discover years dynamically."),
    ("upsc-ifos-mains", "upsc_ifos", "mains", "Indian Forest Service Main — English, General Knowledge and optional subject papers", "https://www.upsc.gov.in/examinations/previous-question-papers", "https://www.upsc.gov.in/examinations/previous-question-papers/archives", "", "Discover years dynamically from official UPSC listings; do not infer a complete year range."),
    ("uppsc-pcs-prelims", "uppsc_pcs", "preliminary", "UPPSC PCS Preliminary — General Studies I and II", "https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues", "https://uppsc.up.nic.in/Home", "2025,2024,2023,2021,2020,2018,2017", "Years surfaced on the official portal at catalogue preparation; paper availability is exam/filter-specific and may expire."),
    ("uppsc-pcs-mains", "uppsc_pcs", "mains", "UPPSC PCS Main — General Hindi, Essay and GS I–VI", "https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues", "https://uppsc.up.nic.in/Home", "2025,2024,2023,2021,2020,2018,2017", "Official portal page showed 2025 mains Hindi, Essay and GS I–VI; dynamically verify remaining years and papers."),
    ("uppsc-acf-rfo", "uppsc_acf_rfo", "preliminary_and_mains", "UPPSC ACF/RFO — common prelims and notification-specific mains/optional papers", "https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues", "https://uppsc.up.nic.in/Home", "", "Discover using exam/year/paper filters; keep ACF and RFO recruitment cycles and optional papers distinct."),
]

def ensure_resource_schema(database_path: str) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS resource_sources (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                canonical_url TEXT NOT NULL,
                landing_url TEXT NOT NULL,
                authority_level TEXT NOT NULL,
                check_frequency TEXT NOT NULL,
                exam_scope TEXT NOT NULL,
                notes TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pyq_collections (
                collection_id TEXT PRIMARY KEY,
                exam_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                title TEXT NOT NULL,
                current_index_url TEXT NOT NULL,
                archive_index_url TEXT NOT NULL,
                years_observed TEXT NOT NULL,
                coverage_notes TEXT NOT NULL,
                acquisition_status TEXT NOT NULL DEFAULT 'discovery_only',
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resource_sources_type ON resource_sources(source_type, authority_level)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_pyq_exam_stage ON pyq_collections(exam_id, stage)")
        now = datetime.now(timezone.utc).isoformat()
        connection.executemany("""
            INSERT INTO resource_sources(source_id,title,source_type,canonical_url,landing_url,authority_level,
              check_frequency,exam_scope,notes,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET title=excluded.title, source_type=excluded.source_type,
              canonical_url=excluded.canonical_url, landing_url=excluded.landing_url,
              authority_level=excluded.authority_level, check_frequency=excluded.check_frequency,
              exam_scope=excluded.exam_scope, notes=excluded.notes, updated_at=excluded.updated_at
        """, [(*row, now, now) for row in SOURCES])
        connection.executemany("""
            INSERT INTO pyq_collections(collection_id,exam_id,stage,title,current_index_url,archive_index_url,
              years_observed,coverage_notes,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(collection_id) DO UPDATE SET exam_id=excluded.exam_id, stage=excluded.stage,
              title=excluded.title, current_index_url=excluded.current_index_url,
              archive_index_url=excluded.archive_index_url, years_observed=excluded.years_observed,
              coverage_notes=excluded.coverage_notes, updated_at=excluded.updated_at
        """, [(*row, now) for row in PYQ_COLLECTIONS])

def list_sources(database_path: str, source_type: str | None = None, exam_query: str | None = None):
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT * FROM resource_sources WHERE enabled=1"
        params = []
        if source_type:
            query += " AND source_type=?"
            params.append(source_type)
        if exam_query:
            query += " AND (exam_scope LIKE ? OR exam_scope LIKE '%GS%')"
            scope_aliases = {"upsc_cse": "CSE", "upsc_ifos": "IFoS", "uppsc_pcs": "PCS", "uppsc_acf_rfo": "ACF/RFO"}
            params.append(f"%{scope_aliases.get(exam_query, exam_query)}%")
        query += " ORDER BY authority_level, source_type, title"
        return [dict(row) for row in connection.execute(query, params)]

def list_pyq_collections(database_path: str, exam_id: str | None = None, stage: str | None = None):
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT * FROM pyq_collections WHERE 1=1"
        params = []
        if exam_id:
            query += " AND exam_id=?"
            params.append(exam_id)
        if stage:
            query += " AND stage=?"
            params.append(stage)
        query += " ORDER BY exam_id, stage"
        rows = []
        for row in connection.execute(query, params):
            item = dict(row)
            item["years_observed"] = [int(y) for y in item["years_observed"].split(",") if y.strip()]
            rows.append(item)
        return rows
