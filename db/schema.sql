-- schema.sql — JusticeFlow V2 database tables

CREATE TABLE IF NOT EXISTS cases (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    category        TEXT,
    jurisdiction    TEXT,
    claim_amount    REAL,
    plaintiff_id    TEXT,
    defendant_id    TEXT,
    status          TEXT DEFAULT 'intake',
    filed_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- AI analysis fields
    dna_vector      TEXT,           -- JSON float list
    cot_reasoning   TEXT,           -- Chain-of-thought reasoning from DNA agent
    dls_score       REAL,
    dls_reasons     TEXT,           -- JSON: {reason: score}
    dls_critique    TEXT,           -- LLM-as-Judge critique text
    dls_confidence  REAL,          -- 0.0-1.0
    emotional_temp  REAL,
    emotion_detail  TEXT,           -- JSON: aspect-level emotion breakdown
    filter_result   TEXT,           -- JSON: {passed, reason, routing}
    settlement_text TEXT,
    ai_recommendation TEXT,        -- Judge agent recommendation
    ai_confidence   REAL
);

CREATE TABLE IF NOT EXISTS entities (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    type            TEXT,           -- person, company, court, government
    registered_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         TEXT,
    entity_a        TEXT,
    entity_b        TEXT,
    edge_type       TEXT,           -- plaintiff_vs_defendant, settled, dismissed
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS negotiation_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         TEXT,
    turn            INTEGER,
    speaker         TEXT,
    message         TEXT,
    offer_amount    REAL,
    emotion_score   REAL,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historical_cases (
    id              TEXT PRIMARY KEY,
    summary         TEXT,
    category        TEXT,
    outcome         TEXT,
    outcome_summary TEXT,
    key_statutes    TEXT,           -- JSON list of relevant statutes
    dna_vector      TEXT,           -- JSON float list
    jurisdiction    TEXT,
    year            INTEGER
);
