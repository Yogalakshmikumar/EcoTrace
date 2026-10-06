-- ============================================================
-- EcoTrace Demo Data
-- ============================================================
-- Run this file AFTER database.sql
--
-- Demo users
-- admin       / admin123
-- collector1  / collector123
-- lab1        / lab123
-- storage1    / storage123
-- auditor1    / audit123
-- ============================================================


-- ============================================================
-- 1. USERS
-- ============================================================

INSERT INTO users
(
    username,
    full_name,
    password_hash,
    role
)
VALUES
(
    'admin',
    'EcoTrace Administrator',
    crypt('admin123', gen_salt('bf')),
    'ADMIN'
),
(
    'collector1',
    'Sample Collector',
    crypt('collector123', gen_salt('bf')),
    'COLLECTOR'
),
(
    'lab1',
    'Laboratory Analyst',
    crypt('lab123', gen_salt('bf')),
    'LAB'
),
(
    'storage1',
    'Storage Officer',
    crypt('storage123', gen_salt('bf')),
    'STORAGE'
),
(
    'auditor1',
    'Audit Officer',
    crypt('audit123', gen_salt('bf')),
    'AUDITOR'
)
ON CONFLICT (username)
DO NOTHING;


-- ============================================================
-- 2. TEST MASTER DATA
-- ============================================================

INSERT INTO tests
(
    test_code,
    test_name,
    method,
    result_unit,
    normal_range
)
VALUES
(
    'PH',
    'pH Measurement',
    'Digital pH meter',
    'pH',
    '6.5 - 8.5'
),
(
    'TURB',
    'Turbidity',
    'Nephelometric method',
    'NTU',
    '< 5'
),
(
    'TDS',
    'Total Dissolved Solids',
    'Conductivity/TDS meter',
    'mg/L',
    '< 500'
),
(
    'NITRATE',
    'Nitrate Concentration',
    'Colorimetric method',
    'mg/L',
    '< 45'
),
(
    'MICRO',
    'Microplastic Particle Count',
    'Microscopic counting',
    'particles/L',
    'Project-specific'
)
ON CONFLICT (test_code)
DO NOTHING;


-- ============================================================
-- 3. SAMPLE 1
-- ============================================================

INSERT INTO samples
(
    sample_code,
    sample_type,
    source_name,
    source_location,
    collected_at,
    collected_by,
    quantity,
    unit,
    sample_condition,
    status,
    description
)
SELECT
    'ECO-2026-001',
    'Water',
    'River Monitoring Point A',
    'Coimbatore - River Point A',
    CURRENT_TIMESTAMP - INTERVAL '3 days',
    u.user_id,
    500,
    'mL',
    'GOOD',
    'STORED',
    'Demonstration water sample'
FROM users u
WHERE u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM samples s
    WHERE s.sample_code = 'ECO-2026-001'
);


-- ============================================================
-- 4. SAMPLE 2
-- ============================================================

INSERT INTO samples
(
    sample_code,
    sample_type,
    source_name,
    source_location,
    collected_at,
    collected_by,
    quantity,
    unit,
    sample_condition,
    status,
    description
)
SELECT
    'ECO-2026-002',
    'Water',
    'Lake Monitoring Point B',
    'Coimbatore - Lake Point B',
    CURRENT_TIMESTAMP - INTERVAL '1 day',
    u.user_id,
    500,
    'mL',
    'GOOD',
    'RECEIVED',
    'Demonstration sample awaiting testing'
FROM users u
WHERE u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM samples s
    WHERE s.sample_code = 'ECO-2026-002'
);


-- ============================================================
-- 5. SAMPLE 3
-- ============================================================

INSERT INTO samples
(
    sample_code,
    sample_type,
    source_name,
    source_location,
    collected_at,
    collected_by,
    quantity,
    unit,
    sample_condition,
    status,
    description
)
SELECT
    'ECO-2026-003',
    'Soil',
    'Agricultural Field C',
    'Coimbatore - Field C',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    u.user_id,
    250,
    'g',
    'GOOD',
    'REGISTERED',
    'Agricultural soil sample'
FROM users u
WHERE u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM samples s
    WHERE s.sample_code = 'ECO-2026-003'
);


-- ============================================================
-- 6. SAMPLE 4
-- ============================================================

INSERT INTO samples
(
    sample_code,
    sample_type,
    source_name,
    source_location,
    collected_at,
    collected_by,
    quantity,
    unit,
    sample_condition,
    status,
    description
)
SELECT
    'ECO-2026-004',
    'Air',
    'Industrial Monitoring Point D',
    'Coimbatore - Industrial Area',
    CURRENT_TIMESTAMP - INTERVAL '5 days',
    u.user_id,
    100,
    'L',
    'GOOD',
    'IN_TRANSIT',
    'Air quality monitoring sample'
FROM users u
WHERE u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM samples s
    WHERE s.sample_code = 'ECO-2026-004'
);


-- ============================================================
-- 7. SAMPLE 5
-- ============================================================

INSERT INTO samples
(
    sample_code,
    sample_type,
    source_name,
    source_location,
    collected_at,
    collected_by,
    quantity,
    unit,
    sample_condition,
    status,
    description
)
SELECT
    'ECO-2026-005',
    'Sediment',
    'Lake Sediment Point E',
    'Coimbatore - Lake E',
    CURRENT_TIMESTAMP - INTERVAL '8 days',
    u.user_id,
    300,
    'g',
    'GOOD',
    'TESTING',
    'Sediment analysis sample'
FROM users u
WHERE u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM samples s
    WHERE s.sample_code = 'ECO-2026-005'
);


-- ============================================================
-- 8. TRANSFER - SAMPLE 1
-- ============================================================

INSERT INTO sample_transfers
(
    sample_id,
    from_location,
    to_location,
    transferred_by,
    condition_on_transfer,
    remarks,
    received_time
)
SELECT
    s.sample_id,
    s.source_location,
    'EcoTrace Laboratory',
    u.user_id,
    'GOOD',
    'Initial laboratory transfer',
    CURRENT_TIMESTAMP
FROM samples s
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-001'
AND u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_transfers t
    WHERE t.sample_id = s.sample_id
);


-- ============================================================
-- 9. TRANSFER - SAMPLE 2
-- ============================================================

INSERT INTO sample_transfers
(
    sample_id,
    from_location,
    to_location,
    transferred_by,
    condition_on_transfer,
    remarks,
    received_time
)
SELECT
    s.sample_id,
    s.source_location,
    'EcoTrace Laboratory',
    u.user_id,
    'GOOD',
    'Received by laboratory',
    CURRENT_TIMESTAMP
FROM samples s
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-002'
AND u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_transfers t
    WHERE t.sample_id = s.sample_id
);


-- ============================================================
-- 10. TRANSFER - SAMPLE 3
-- ============================================================

INSERT INTO sample_transfers
(
    sample_id,
    from_location,
    to_location,
    transferred_by,
    condition_on_transfer,
    remarks,
    received_time
)
SELECT
    s.sample_id,
    s.source_location,
    'EcoTrace Laboratory',
    u.user_id,
    'GOOD',
    'Soil sample transferred to laboratory',
    CURRENT_TIMESTAMP
FROM samples s
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-003'
AND u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_transfers t
    WHERE t.sample_id = s.sample_id
);


-- ============================================================
-- 11. TRANSFER - SAMPLE 4
-- ============================================================

INSERT INTO sample_transfers
(
    sample_id,
    from_location,
    to_location,
    transferred_by,
    condition_on_transfer,
    remarks,
    received_time
)
SELECT
    s.sample_id,
    s.source_location,
    'EcoTrace Laboratory',
    u.user_id,
    'GOOD',
    'Air quality sample transferred to laboratory',
    CURRENT_TIMESTAMP
FROM samples s
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-004'
AND u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_transfers t
    WHERE t.sample_id = s.sample_id
);


-- ============================================================
-- 12. TRANSFER - SAMPLE 5
-- ============================================================

INSERT INTO sample_transfers
(
    sample_id,
    from_location,
    to_location,
    transferred_by,
    condition_on_transfer,
    remarks,
    received_time
)
SELECT
    s.sample_id,
    s.source_location,
    'EcoTrace Laboratory',
    u.user_id,
    'GOOD',
    'Sediment sample transferred to laboratory',
    CURRENT_TIMESTAMP
FROM samples s
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-005'
AND u.username = 'collector1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_transfers t
    WHERE t.sample_id = s.sample_id
);


-- ============================================================
-- 13. TEST ASSIGNMENT - SAMPLE 1 - pH
-- ============================================================

INSERT INTO sample_tests
(
    sample_id,
    test_id,
    assigned_to,
    status,
    priority
)
SELECT
    s.sample_id,
    t.test_id,
    u.user_id,
    'COMPLETED',
    'NORMAL'
FROM samples s
CROSS JOIN tests t
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-001'
AND t.test_code = 'PH'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_tests st
    WHERE st.sample_id = s.sample_id
    AND st.test_id = t.test_id
);


-- ============================================================
-- 14. TEST ASSIGNMENT - SAMPLE 2 - MICROPLASTIC
-- ============================================================

INSERT INTO sample_tests
(
    sample_id,
    test_id,
    assigned_to,
    status,
    priority
)
SELECT
    s.sample_id,
    t.test_id,
    u.user_id,
    'ASSIGNED',
    'HIGH'
FROM samples s
CROSS JOIN tests t
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-002'
AND t.test_code = 'MICRO'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_tests st
    WHERE st.sample_id = s.sample_id
    AND st.test_id = t.test_id
);


-- ============================================================
-- 15. TEST ASSIGNMENT - SAMPLE 3 - NITRATE
-- ============================================================

INSERT INTO sample_tests
(
    sample_id,
    test_id,
    assigned_to,
    status,
    priority
)
SELECT
    s.sample_id,
    t.test_id,
    u.user_id,
    'COMPLETED',
    'NORMAL'
FROM samples s
CROSS JOIN tests t
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-003'
AND t.test_code = 'NITRATE'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_tests st
    WHERE st.sample_id = s.sample_id
    AND st.test_id = t.test_id
);


-- ============================================================
-- 16. TEST ASSIGNMENT - SAMPLE 4 - TDS
-- ============================================================

INSERT INTO sample_tests
(
    sample_id,
    test_id,
    assigned_to,
    status,
    priority
)
SELECT
    s.sample_id,
    t.test_id,
    u.user_id,
    'IN_PROGRESS',
    'HIGH'
FROM samples s
CROSS JOIN tests t
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-004'
AND t.test_code = 'TDS'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_tests st
    WHERE st.sample_id = s.sample_id
    AND st.test_id = t.test_id
);


-- ============================================================
-- 17. TEST ASSIGNMENT - SAMPLE 5 - TURBIDITY
-- ============================================================

INSERT INTO sample_tests
(
    sample_id,
    test_id,
    assigned_to,
    status,
    priority
)
SELECT
    s.sample_id,
    t.test_id,
    u.user_id,
    'COMPLETED',
    'NORMAL'
FROM samples s
CROSS JOIN tests t
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-005'
AND t.test_code = 'TURB'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM sample_tests st
    WHERE st.sample_id = s.sample_id
    AND st.test_id = t.test_id
);


-- ============================================================
-- 18. TEST RESULT - SAMPLE 1 - pH
-- ============================================================

INSERT INTO test_results
(
    sample_test_id,
    result_value,
    result_text,
    result_unit,
    entered_by,
    remarks
)
SELECT
    st.sample_test_id,
    7.20,
    NULL,
    'pH',
    u.user_id,
    'Normal demonstration result'
FROM sample_tests st
JOIN samples s
    ON s.sample_id = st.sample_id
JOIN tests t
    ON t.test_id = st.test_id
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-001'
AND t.test_code = 'PH'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM test_results r
    WHERE r.sample_test_id = st.sample_test_id
);


-- ============================================================
-- 19. TEST RESULT - SAMPLE 2 - MICROPLASTIC
-- ============================================================

INSERT INTO test_results
(
    sample_test_id,
    result_value,
    result_text,
    result_unit,
    entered_by,
    remarks
)
SELECT
    st.sample_test_id,
    12.00,
    NULL,
    'particles/L',
    u.user_id,
    'Demonstration microplastic particle count'
FROM sample_tests st
JOIN samples s
    ON s.sample_id = st.sample_id
JOIN tests t
    ON t.test_id = st.test_id
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-002'
AND t.test_code = 'MICRO'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM test_results r
    WHERE r.sample_test_id = st.sample_test_id
);


-- ============================================================
-- 20. TEST RESULT - SAMPLE 3 - NITRATE
-- ============================================================

INSERT INTO test_results
(
    sample_test_id,
    result_value,
    result_text,
    result_unit,
    entered_by,
    remarks
)
SELECT
    st.sample_test_id,
    28.50,
    NULL,
    'mg/L',
    u.user_id,
    'Demonstration nitrate result'
FROM sample_tests st
JOIN samples s
    ON s.sample_id = st.sample_id
JOIN tests t
    ON t.test_id = st.test_id
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-003'
AND t.test_code = 'NITRATE'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM test_results r
    WHERE r.sample_test_id = st.sample_test_id
);


-- ============================================================
-- 21. TEST RESULT - SAMPLE 4 - TDS
-- ============================================================

INSERT INTO test_results
(
    sample_test_id,
    result_value,
    result_text,
    result_unit,
    entered_by,
    remarks
)
SELECT
    st.sample_test_id,
    320.00,
    NULL,
    'mg/L',
    u.user_id,
    'Demonstration TDS result'
FROM sample_tests st
JOIN samples s
    ON s.sample_id = st.sample_id
JOIN tests t
    ON t.test_id = st.test_id
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-004'
AND t.test_code = 'TDS'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM test_results r
    WHERE r.sample_test_id = st.sample_test_id
);


-- ============================================================
-- 22. TEST RESULT - SAMPLE 5 - TURBIDITY
-- ============================================================

INSERT INTO test_results
(
    sample_test_id,
    result_value,
    result_text,
    result_unit,
    entered_by,
    remarks
)
SELECT
    st.sample_test_id,
    3.40,
    NULL,
    'NTU',
    u.user_id,
    'Demonstration turbidity result'
FROM sample_tests st
JOIN samples s
    ON s.sample_id = st.sample_id
JOIN tests t
    ON t.test_id = st.test_id
CROSS JOIN users u
WHERE s.sample_code = 'ECO-2026-005'
AND t.test_code = 'TURB'
AND u.username = 'lab1'
AND NOT EXISTS
(
    SELECT 1
    FROM test_results r
    WHERE r.sample_test_id = st.sample_test_id
);


-- ============================================================
-- 23. STORAGE - SAMPLE 1
-- ============================================================

INSERT INTO storage
(
    sample_id,
    location,
    shelf,
    temperature_c,
    sample_condition,
    remarks
)
SELECT
    s.sample_id,
    'EcoTrace Laboratory Store',
    'S-01',
    4.00,
    'GOOD',
    'Temporary refrigerated storage'
FROM samples s
WHERE s.sample_code = 'ECO-2026-001'
AND NOT EXISTS
(
    SELECT 1
    FROM storage st
    WHERE st.sample_id = s.sample_id
    AND st.stored_to IS NULL
);


-- ============================================================
-- 24. STORAGE - SAMPLE 2
-- ============================================================

INSERT INTO storage
(
    sample_id,
    location,
    shelf,
    temperature_c,
    sample_condition,
    remarks
)
SELECT
    s.sample_id,
    'EcoTrace Laboratory Store',
    'S-02',
    4.00,
    'GOOD',
    'Refrigerated water sample storage'
FROM samples s
WHERE s.sample_code = 'ECO-2026-002'
AND NOT EXISTS
(
    SELECT 1
    FROM storage st
    WHERE st.sample_id = s.sample_id
    AND st.stored_to IS NULL
);


-- ============================================================
-- 25. STORAGE - SAMPLE 3
-- ============================================================

INSERT INTO storage
(
    sample_id,
    location,
    shelf,
    temperature_c,
    sample_condition,
    remarks
)
SELECT
    s.sample_id,
    'EcoTrace Laboratory Store',
    'S-03',
    22.00,
    'GOOD',
    'Soil sample storage'
FROM samples s
WHERE s.sample_code = 'ECO-2026-003'
AND NOT EXISTS
(
    SELECT 1
    FROM storage st
    WHERE st.sample_id = s.sample_id
    AND st.stored_to IS NULL
);


-- ============================================================
-- 26. STORAGE - SAMPLE 4
-- ============================================================

INSERT INTO storage
(
    sample_id,
    location,
    shelf,
    temperature_c,
    sample_condition,
    remarks
)
SELECT
    s.sample_id,
    'EcoTrace Laboratory Store',
    'S-04',
    20.00,
    'GOOD',
    'Air quality sample storage'
FROM samples s
WHERE s.sample_code = 'ECO-2026-004'
AND NOT EXISTS
(
    SELECT 1
    FROM storage st
    WHERE st.sample_id = s.sample_id
    AND st.stored_to IS NULL
);


-- ============================================================
-- 27. STORAGE - SAMPLE 5
-- ============================================================

INSERT INTO storage
(
    sample_id,
    location,
    shelf,
    temperature_c,
    sample_condition,
    remarks
)
SELECT
    s.sample_id,
    'EcoTrace Laboratory Store',
    'S-05',
    4.00,
    'GOOD',
    'Sediment sample storage'
FROM samples s
WHERE s.sample_code = 'ECO-2026-005'
AND NOT EXISTS
(
    SELECT 1
    FROM storage st
    WHERE st.sample_id = s.sample_id
    AND st.stored_to IS NULL
);


-- ============================================================
-- 28. VERIFICATION
-- ============================================================

SELECT
    'Samples' AS item,
    COUNT(*) AS total
FROM samples

UNION ALL

SELECT
    'Transfers',
    COUNT(*)
FROM sample_transfers

UNION ALL

SELECT
    'Test Assignments',
    COUNT(*)
FROM sample_tests

UNION ALL

SELECT
    'Test Results',
    COUNT(*)
FROM test_results

UNION ALL

SELECT
    'Storage Records',
    COUNT(*)
FROM storage;


-- ============================================================
-- END OF ECOTRACE DEMO DATA
-- ============================================================