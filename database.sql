-- ============================================================
-- EcoTrace
-- Environmental Sample Lifecycle Tracking System
-- PostgreSQL 18
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- CLEAN PREVIOUS VERSION
-- ============================================================

DROP VIEW IF EXISTS v_sample_overview CASCADE;
DROP VIEW IF EXISTS v_sample_lifecycle CASCADE;
DROP VIEW IF EXISTS v_test_summary CASCADE;
DROP VIEW IF EXISTS v_audit_history CASCADE;

DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS storage CASCADE;
DROP TABLE IF EXISTS test_results CASCADE;
DROP TABLE IF EXISTS sample_tests CASCADE;
DROP TABLE IF EXISTS tests CASCADE;
DROP TABLE IF EXISTS sample_transfers CASCADE;
DROP TABLE IF EXISTS samples CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- 1. USERS
-- ============================================================

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,

    username VARCHAR(50) NOT NULL UNIQUE,

    full_name VARCHAR(100) NOT NULL,

    password_hash TEXT NOT NULL,

    role VARCHAR(20) NOT NULL
        CHECK (
            role IN (
                'ADMIN',
                'COLLECTOR',
                'LAB',
                'STORAGE',
                'AUDITOR'
            )
        ),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. SAMPLES
-- ============================================================

CREATE TABLE samples (
    sample_id BIGSERIAL PRIMARY KEY,

    sample_code VARCHAR(30) NOT NULL UNIQUE,

    sample_type VARCHAR(80) NOT NULL,

    source_name VARCHAR(120) NOT NULL,

    source_location VARCHAR(200) NOT NULL,

    collected_at TIMESTAMPTZ NOT NULL,

    collected_by BIGINT NOT NULL
        REFERENCES users(user_id),

    quantity NUMERIC(12,3) NOT NULL
        CHECK (quantity > 0),

    unit VARCHAR(20) NOT NULL DEFAULT 'g',

    sample_condition VARCHAR(20) NOT NULL DEFAULT 'GOOD'
        CHECK (
            sample_condition IN (
                'GOOD',
                'DAMAGED',
                'CONTAMINATED',
                'UNKNOWN'
            )
        ),

    status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED'
        CHECK (
            status IN (
                'COLLECTED',
                'REGISTERED',
                'IN_TRANSIT',
                'RECEIVED',
                'TESTING',
                'TESTED',
                'STORED',
                'DISPOSED',
                'REJECTED'
            )
        ),

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. SAMPLE TRANSFERS
-- ============================================================

CREATE TABLE sample_transfers (
    transfer_id BIGSERIAL PRIMARY KEY,

    sample_id BIGINT NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    from_location VARCHAR(200) NOT NULL,

    to_location VARCHAR(200) NOT NULL,

    transferred_by BIGINT NOT NULL
        REFERENCES users(user_id),

    transfer_time TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    received_time TIMESTAMPTZ,

    condition_on_transfer VARCHAR(20) NOT NULL
        CHECK (
            condition_on_transfer IN (
                'GOOD',
                'DAMAGED',
                'CONTAMINATED',
                'UNKNOWN'
            )
        ),

    remarks TEXT,

    CHECK (to_location <> from_location),

    CHECK (
        received_time IS NULL
        OR received_time >= transfer_time
    )
);

-- ============================================================
-- 4. TEST MASTER
-- ============================================================

CREATE TABLE tests (
    test_id BIGSERIAL PRIMARY KEY,

    test_code VARCHAR(30) NOT NULL UNIQUE,

    test_name VARCHAR(120) NOT NULL,

    method VARCHAR(150) NOT NULL,

    result_unit VARCHAR(30),

    normal_range VARCHAR(80),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. SAMPLE TEST ASSIGNMENTS
-- ============================================================

CREATE TABLE sample_tests (
    sample_test_id BIGSERIAL PRIMARY KEY,

    sample_id BIGINT NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    test_id BIGINT NOT NULL
        REFERENCES tests(test_id),

    assigned_to BIGINT
        REFERENCES users(user_id),

    assigned_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    status VARCHAR(20) NOT NULL DEFAULT 'ASSIGNED'
        CHECK (
            status IN (
                'ASSIGNED',
                'IN_PROGRESS',
                'COMPLETED',
                'CANCELLED'
            )
        ),

    priority VARCHAR(10) NOT NULL DEFAULT 'NORMAL'
        CHECK (
            priority IN (
                'LOW',
                'NORMAL',
                'HIGH'
            )
        ),

    remarks TEXT,

    UNIQUE (sample_id, test_id)
);

-- ============================================================
-- 6. TEST RESULTS
-- ============================================================

CREATE TABLE test_results (
    result_id BIGSERIAL PRIMARY KEY,

    sample_test_id BIGINT NOT NULL UNIQUE
        REFERENCES sample_tests(sample_test_id)
        ON DELETE CASCADE,

    result_value NUMERIC(14,4),

    result_text TEXT,

    result_unit VARCHAR(30),

    observed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    entered_by BIGINT NOT NULL
        REFERENCES users(user_id),

    remarks TEXT,

    CHECK (
        result_value IS NOT NULL
        OR NULLIF(TRIM(result_text), '') IS NOT NULL
    )
);

-- ============================================================
-- 7. STORAGE
-- ============================================================

CREATE TABLE storage (
    storage_id BIGSERIAL PRIMARY KEY,

    sample_id BIGINT NOT NULL
        REFERENCES samples(sample_id)
        ON DELETE CASCADE,

    location VARCHAR(200) NOT NULL,

    shelf VARCHAR(50),

    temperature_c NUMERIC(6,2),

    sample_condition VARCHAR(20) NOT NULL DEFAULT 'GOOD'
        CHECK (
            sample_condition IN (
                'GOOD',
                'DAMAGED',
                'CONTAMINATED',
                'UNKNOWN'
            )
        ),

    stored_from TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    stored_to TIMESTAMPTZ,

    remarks TEXT,

    CHECK (
        stored_to IS NULL
        OR stored_to >= stored_from
    )
);

-- ============================================================
-- 8. AUDIT LOG
-- ============================================================

CREATE TABLE audit_log (
    audit_id BIGSERIAL PRIMARY KEY,

    table_name VARCHAR(100) NOT NULL,

    record_id BIGINT,

    action VARCHAR(30) NOT NULL,

    changed_by BIGINT
        REFERENCES users(user_id),

    changed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    reason TEXT,

    old_data JSONB,

    new_data JSONB
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_samples_sample_code
ON samples(sample_code);

CREATE INDEX idx_samples_status
ON samples(status);

CREATE INDEX idx_samples_type
ON samples(sample_type);

CREATE INDEX idx_samples_collection_date
ON samples(collected_at);

CREATE INDEX idx_samples_source
ON samples(source_name);

CREATE INDEX idx_transfers_sample
ON sample_transfers(sample_id);

CREATE INDEX idx_sample_tests_sample
ON sample_tests(sample_id);

CREATE INDEX idx_sample_tests_test
ON sample_tests(test_id);

CREATE INDEX idx_test_results_assignment
ON test_results(sample_test_id);

CREATE INDEX idx_storage_sample
ON storage(sample_id);

CREATE INDEX idx_audit_record
ON audit_log(table_name, record_id);

CREATE INDEX idx_audit_changed_at
ON audit_log(changed_at);

-- ============================================================
-- UPDATED_AT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_samples_updated_at
BEFORE UPDATE ON samples
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- AUDIT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION audit_sample_changes()
RETURNS TRIGGER
AS $$
DECLARE
    current_user_id BIGINT;
BEGIN

    BEGIN
        current_user_id :=
            NULLIF(current_setting('app.user_id', true), '')::BIGINT;
    EXCEPTION
        WHEN OTHERS THEN
            current_user_id := NULL;
    END;

    IF TG_OP = 'INSERT' THEN

        INSERT INTO audit_log (
            table_name,
            record_id,
            action,
            changed_by,
            new_data
        )
        VALUES (
            TG_TABLE_NAME,
            NEW.sample_id,
            'INSERT',
            current_user_id,
            to_jsonb(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN

        INSERT INTO audit_log (
            table_name,
            record_id,
            action,
            changed_by,
            old_data,
            new_data
        )
        VALUES (
            TG_TABLE_NAME,
            NEW.sample_id,
            'UPDATE',
            current_user_id,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN

        INSERT INTO audit_log (
            table_name,
            record_id,
            action,
            changed_by,
            old_data
        )
        VALUES (
            TG_TABLE_NAME,
            OLD.sample_id,
            'DELETE',
            current_user_id,
            to_jsonb(OLD)
        );

        RETURN OLD;

    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_samples_audit
AFTER INSERT OR UPDATE OR DELETE
ON samples
FOR EACH ROW
EXECUTE FUNCTION audit_sample_changes();

-- ============================================================
-- SAMPLE LIFECYCLE VIEW
-- ============================================================

CREATE VIEW v_sample_lifecycle AS
SELECT
    s.sample_id,
    s.sample_code,
    s.sample_type,
    s.source_name,
    s.source_location,
    s.collected_at,
    s.status,
    s.quantity,
    s.unit,
    s.sample_condition,

    u.full_name AS collected_by,

    (
        SELECT st.to_location
        FROM sample_transfers st
        WHERE st.sample_id = s.sample_id
        ORDER BY st.transfer_time DESC
        LIMIT 1
    ) AS latest_transfer_location,

    (
        SELECT st.received_time
        FROM sample_transfers st
        WHERE st.sample_id = s.sample_id
        ORDER BY st.transfer_time DESC
        LIMIT 1
    ) AS latest_received_time

FROM samples s
JOIN users u
    ON u.user_id = s.collected_by;

-- ============================================================
-- SAMPLE OVERVIEW VIEW
-- ============================================================

CREATE VIEW v_sample_overview AS
SELECT
    s.sample_id,
    s.sample_code,
    s.sample_type,
    s.source_name,
    s.source_location,
    s.status,
    s.collected_at,
    s.quantity,
    s.unit,
    u.full_name AS collected_by,

    COUNT(DISTINCT st.sample_test_id) AS total_tests,

    COUNT(DISTINCT tr.result_id) AS completed_results,

    (
        SELECT storage.location
        FROM storage
        WHERE storage.sample_id = s.sample_id
          AND storage.stored_to IS NULL
        ORDER BY storage.stored_from DESC
        LIMIT 1
    ) AS current_storage_location

FROM samples s

JOIN users u
    ON u.user_id = s.collected_by

LEFT JOIN sample_tests st
    ON st.sample_id = s.sample_id

LEFT JOIN test_results tr
    ON tr.sample_test_id = st.sample_test_id

GROUP BY
    s.sample_id,
    u.full_name;

-- ============================================================
-- TEST SUMMARY VIEW
-- ============================================================

CREATE VIEW v_test_summary AS
SELECT
    s.sample_id,
    s.sample_code,
    t.test_code,
    t.test_name,
    t.method,
    st.status AS assignment_status,
    st.priority,
    tr.result_value,
    COALESCE(tr.result_unit, t.result_unit) AS result_unit,
    tr.result_text,
    tr.observed_at,
    u.full_name AS entered_by

FROM samples s

JOIN sample_tests st
    ON st.sample_id = s.sample_id

JOIN tests t
    ON t.test_id = st.test_id

LEFT JOIN test_results tr
    ON tr.sample_test_id = st.sample_test_id

LEFT JOIN users u
    ON u.user_id = tr.entered_by;

-- ============================================================
-- AUDIT VIEW
-- ============================================================

CREATE VIEW v_audit_history AS
SELECT
    a.audit_id,
    a.table_name,
    a.record_id,
    a.action,
    COALESCE(u.full_name, 'System') AS changed_by,
    a.changed_at,
    a.reason,
    a.old_data,
    a.new_data

FROM audit_log a

LEFT JOIN users u
    ON u.user_id = a.changed_by;

-- ============================================================
-- CONTROLLED SAMPLE STATUS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION update_sample_status(
    p_sample_id BIGINT,
    p_new_status VARCHAR,
    p_reason TEXT
)
RETURNS VOID
AS $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM samples
        WHERE sample_id = p_sample_id
    ) THEN

        RAISE EXCEPTION
            'Sample % does not exist',
            p_sample_id;

    END IF;

    IF p_new_status NOT IN (
        'COLLECTED',
        'REGISTERED',
        'IN_TRANSIT',
        'RECEIVED',
        'TESTING',
        'TESTED',
        'STORED',
        'DISPOSED',
        'REJECTED'
    ) THEN

        RAISE EXCEPTION
            'Invalid sample status: %',
            p_new_status;

    END IF;

    UPDATE samples

    SET status = p_new_status

    WHERE sample_id = p_sample_id;

END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- END OF DATABASE SCHEMA
-- ============================================================





SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
SELECT * FROM samples;
SELECT extname
FROM pg_extension
WHERE extname = 'pgcrypto';