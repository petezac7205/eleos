-- =============================================================================
-- Eleos Seed Data
-- Standard Benchmark Dataset & Demo Scenarios from eleos_blueprint.md
-- =============================================================================

-- =============================================================================
-- 1. COST BENCHMARKS (Regional & Category Reference Dataset)
-- =============================================================================

INSERT INTO cost_benchmarks (
    category, item, unit, unit_cost_low, unit_cost_mid, unit_cost_high,
    state, district, country, source_name, source_url, authority_type, review_cycle_months,
    disaster_multiplier, rural_premium_pct, notes
) VALUES
-- Demo 1: Disaster Relief (Nepal / General Flood Relief)
('food', 'Rice', 'kg', 28.00, 32.00, 40.00, 'Tamil Nadu', 'Chennai', 'India', 'PDS retail, TN', 'https://tnpds.gov.in', 'statutory_order', 6, 1.30, 10.00, 'Standard retail price for staple rice in Southern/Eastern distribution'),
('food', 'Wheat flour', 'kg', 25.00, 30.00, 38.00, NULL, NULL, 'India', 'PDS retail', 'https://dfpd.gov.in', 'statutory_order', 6, 1.30, 10.00, 'Atta/wheat flour procurement norms'),
('food', 'Dal/lentils', 'kg', 80.00, 100.00, 130.00, NULL, NULL, 'India', 'MOSPI CPI', 'https://mospi.gov.in', 'cpi_basket', 3, 1.30, 15.00, 'Toor/moong dal average retail index'),
('food', 'Cooking oil', 'litre', 120.00, 150.00, 180.00, NULL, NULL, 'India', 'Market avg', NULL, 'market_survey', 3, 1.30, 10.00, 'Edible vegetable/mustard oil'),
('shelter', 'Emergency tent (4-person)', 'unit', 700.00, 900.00, 1400.00, NULL, NULL, 'India', 'NDRF procurement', 'https://ndrf.gov.in', 'statutory_order', 12, 1.50, 15.00, 'Waterproof high-grade emergency relief shelter tent'),
('shelter', 'Blanket', 'unit', 150.00, 250.00, 400.00, NULL, NULL, 'India', 'Market avg', NULL, 'market_survey', 6, 1.30, 10.00, 'Fleece/wool emergency relief blanket'),
('food', 'Emergency food kit (family, 1 week)', 'kit', 400.00, 600.00, 900.00, NULL, NULL, 'India', 'Relief org benchmarks', NULL, 'historical_average', 6, 1.50, 20.00, 'Contains dry ration, pulses, oil, salt, biscuits for 4 people'),
('medical', 'Medical first-aid kit', 'kit', 300.00, 400.00, 600.00, NULL, NULL, 'India', 'CGHS', 'https://cghs.nic.in', 'statutory_order', 12, 1.30, 10.00, 'Antiseptic, bandages, ORS, paracetamol, water purification tablets'),
('transport', 'Transport (truck, per trip, intra-state)', 'trip', 8000.00, 12000.00, 18000.00, NULL, NULL, 'India', 'State transport', NULL, 'market_survey', 6, 2.00, 25.00, 'Medium commercial vehicle up to 250 km'),
('transport', 'Transport (cross-border India->Nepal)', 'trip', 15000.00, 25000.00, 40000.00, 'Bihar', 'Raxaul', 'India', 'Customs + logistics', NULL, 'market_survey', 6, 1.50, 30.00, 'Logistics across border checkpoint including transit handling'),
('labor', 'Field worker (daily wage)', 'day', 500.00, 700.00, 1000.00, NULL, NULL, 'India', 'Min wage + NGO avg', NULL, 'statutory_order', 12, 1.20, 0.00, 'Disaster relief ground relief volunteer/worker allowance'),
('medical', 'Doctor/medical professional', 'day', 2000.00, 3500.00, 5000.00, NULL, NULL, 'India', 'CGHS rates', 'https://cghs.nic.in', 'statutory_order', 12, 1.00, 20.00, 'Visiting physician emergency medical camp stipend'),

-- Demo 2: Mid-Day Meals (Vellore, TN)
('nutrition', 'Meal (primary school, class 1-5)', 'meal', 4.97, 5.45, 6.50, 'Tamil Nadu', 'Vellore', 'India', 'PM POSHAN FY25-26', 'https://pmposhan.education.gov.in', 'statutory_order', 12, 1.00, 5.00, 'Central & State prescribed cooking cost per child per day for primary classes'),
('nutrition', 'Meal (upper primary, class 6-8)', 'meal', 7.45, 8.17, 9.50, 'Tamil Nadu', 'Vellore', 'India', 'PM POSHAN FY25-26', 'https://pmposhan.education.gov.in', 'statutory_order', 12, 1.00, 5.00, 'Cooking cost per child per day for upper primary classes'),
('nutrition', 'Supplementary nutrition (egg/fruit)', 'meal', 2.00, 3.50, 5.00, 'Tamil Nadu', 'Vellore', 'India', 'State nutrition dept', NULL, 'statutory_order', 12, 1.00, 5.00, 'Additional boiled egg / banana nutrient complement'),
('equipment', 'Kitchen equipment (per center)', 'unit', 15000.00, 25000.00, 40000.00, 'Tamil Nadu', NULL, 'India', 'Market avg', NULL, 'market_survey', 24, 1.00, 10.00, 'Large cauldrons, burners, storage bins, steam cookers'),
('salary', 'Cook salary (monthly)', 'month', 3000.00, 5000.00, 8000.00, 'Tamil Nadu', 'Vellore', 'India', 'State-set rates', NULL, 'statutory_order', 12, 1.00, 0.00, 'Mid-day meal scheme cook-cum-helper honorarium'),
('food', 'Rice (bulk procurement, per kg)', 'kg', 22.00, 28.00, 35.00, 'Tamil Nadu', NULL, 'India', 'FCI/PDS bulk', NULL, 'statutory_order', 6, 1.00, 5.00, 'Wholesale institutional grains supply'),
('food', 'Vegetables (seasonal avg)', 'kg', 20.00, 35.00, 50.00, 'Tamil Nadu', 'Vellore', 'India', 'Mandi prices, TN', NULL, 'market_survey', 1, 1.00, 10.00, 'Fresh local vegetable produce for sambar/curry'),
('utilities', 'LPG cylinder', 'unit', 800.00, 900.00, 1050.00, 'Tamil Nadu', 'Vellore', 'India', 'IndianOil retail', 'https://iocl.com', 'statutory_order', 3, 1.00, 5.00, 'Commercial/institutional cooking gas 19kg/14.2kg subsidized'),

-- Demo 4: Marathon Fundraiser — School Libraries (Raigad, MH)
('construction', 'Library room construction', 'room', 250000.00, 350000.00, 500000.00, 'Maharashtra', 'Raigad', 'India', 'MH PWD SoR', 'https://mahapwd.gov.in', 'statutory_order', 12, 1.00, 15.00, 'Standard brick & mortar 400 sq ft library hall with electricals'),
('furniture', 'Bookshelves + furniture', 'room', 50000.00, 80000.00, 120000.00, 'Maharashtra', 'Raigad', 'India', 'Market survey', NULL, 'market_survey', 12, 1.00, 10.00, 'Steel double-sided book racks, study tables, chairs for 30 children'),
('supplies', 'Books (age-appropriate set)', 'set', 15000.00, 25000.00, 40000.00, 'Maharashtra', NULL, 'India', 'Publisher rates', NULL, 'market_survey', 12, 1.00, 5.00, '500+ curated Marathi and English illustrated children storybooks'),
('equipment', 'Computer + printer', 'unit', 25000.00, 35000.00, 50000.00, 'Maharashtra', NULL, 'India', 'Market', NULL, 'market_survey', 12, 1.00, 10.00, 'Desktop PC, UPS, and laser printer for digital cataloging'),
('salary', 'Librarian salary (annual)', 'year', 120000.00, 180000.00, 240000.00, 'Maharashtra', 'Raigad', 'India', 'State avg', NULL, 'statutory_order', 12, 1.00, 0.00, 'Part-time librarian & literacy tutor compensation'),
('salary', 'Program coordinator', 'year', 180000.00, 240000.00, 360000.00, 'Maharashtra', NULL, 'India', 'NGO avg salary', NULL, 'historical_average', 12, 1.00, 0.00, 'Cluster monitoring officer for rural libraries'),
('transport', 'Travel/site visits', 'trip', 20000.00, 40000.00, 60000.00, 'Maharashtra', 'Raigad', 'India', 'State transport rates', NULL, 'statutory_order', 12, 1.00, 15.00, 'Quarterly audit and monitoring visits across tribal school clusters')
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 2. USERS (Seed platform test accounts)
-- =============================================================================

-- Passwords are set to bcrypt hash of 'eleos@123'
-- Hash: $2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi
INSERT INTO users (id, email, password_hash, name, phone, role, avatar_url) VALUES
('11111111-1111-1111-1111-111111111111', 'admin@eleos.app', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'Eleos Platform Admin', '+919876543210', 'admin', 'https://api.dicebear.com/7.x/bottts/svg?seed=admin'),
('22222222-2222-2222-2222-222222222222', 'reviewer@eleos.app', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'Vikram Mehra (Senior Auditor)', '+919876543211', 'reviewer', 'https://api.dicebear.com/7.x/avataaars/svg?seed=vikram'),
('33333333-3333-3333-3333-333333333333', 'hoperelief@eleos.app', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'HopeRelief Admin', '+919876543212', 'ngo_admin', 'https://api.dicebear.com/7.x/identicon/svg?seed=hoperelief'),
('44444444-4444-4444-4444-444444444444', 'annapurna@eleos.app', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'Annapurna Trust Admin', '+919876543213', 'ngo_admin', 'https://api.dicebear.com/7.x/identicon/svg?seed=annapurna'),
('55555555-5555-5555-5555-555555555555', 'teachforchange@eleos.app', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'Teach For Change Admin', '+919876543214', 'ngo_admin', 'https://api.dicebear.com/7.x/identicon/svg?seed=teachforchange'),
('66666666-6666-6666-6666-666666666666', 'globalaid.fake@eleos.app', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'GlobalAid Admin (Flagged)', '+919876543215', 'ngo_admin', 'https://api.dicebear.com/7.x/identicon/svg?seed=globalaid'),
('77777777-7777-7777-7777-777777777777', 'riya.sharma@example.com', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'Riya Sharma', '+919876543216', 'donor', 'https://api.dicebear.com/7.x/avataaars/svg?seed=riya'),
('88888888-8888-8888-8888-888888888888', 'kavya.patel@example.com', '$2b$10$Fcmrqd6XYjRWv0JuZETGZubhzvx0lPy7h9N9AJIr7dMPcJ2X8wcQi', 'Kavya Patel', '+919876543217', 'volunteer', 'https://api.dicebear.com/7.x/avataaars/svg?seed=kavya')
ON CONFLICT (email) DO NOTHING;


-- =============================================================================
-- 3. NGO PROFILES
-- =============================================================================

INSERT INTO ngo_profiles (
    id, user_id, name, registration_type, registration_number, pan, darpan_id,
    fcra_registered, fcra_number, tax_12a, tax_80g, state, district, city,
    founded_year, website, description, logo_url, bank_account_name, bank_ifsc,
    bank_account_last4, verification_status, verified_at, verified_by
) VALUES
-- Demo 1 NGO: HopeRelief Foundation (Legitimate, High Trust, FCRA registered)
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '33333333-3333-3333-3333-333333333333',
 'HopeRelief Foundation', 'trust', 'TR/2019/CHN/1029', 'AAATH1234F', 'TN/2019/0234567',
 true, '076210234', true, true, 'Tamil Nadu', 'Chennai', 'Chennai',
 2019, 'https://hoperelief.org', 'Rapid humanitarian and emergency flood relief across South Asia with verified audit trails.',
 'https://images.unsplash.com/photo-1593113598332-cd288d649433?w=150', 'HopeRelief Foundation General Trust', 'HDFC0000123',
 '4892', 'verified', NOW() - INTERVAL '30 days', '22222222-2222-2222-2222-222222222222'),

-- Demo 2 NGO: Annapurna Trust (Legitimate, Mid-Day Meals)
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '44444444-4444-4444-4444-444444444444',
 'Annapurna Trust', 'society', 'SOC/2018/VEL/5521', 'AABTA5678K', 'TN/2018/0198765',
 false, NULL, true, true, 'Tamil Nadu', 'Vellore', 'Katpadi',
 2018, 'https://annapurnatrust.org', 'Eradicating classroom hunger through hygienic mid-day meal programs in rural government schools.',
 'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=150', 'Annapurna Trust School Feeding Fund', 'SBIN0001234',
 '1092', 'verified', NOW() - INTERVAL '60 days', '22222222-2222-2222-2222-222222222222'),

-- Demo 4 NGO: Teach For Change India (Legitimate, Education)
('cccccccc-cccc-cccc-cccc-cccccccccccc', '55555555-5555-5555-5555-555555555555',
 'Teach For Change India', 'section_8', 'U85300MH2020NPL12984', 'AAACT9012M', 'MH/2020/0345678',
 true, '083420199', true, true, 'Maharashtra', 'Mumbai', 'Mumbai',
 2020, 'https://teachforchangeindia.org', 'Building rural digital libraries and literacy hubs across tribal districts in Maharashtra.',
 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=150', 'Teach For Change India Foundation', 'ICIC0000456',
 '9812', 'verified', NOW() - INTERVAL '90 days', '22222222-2222-2222-2222-222222222222'),

-- Demo 3 NGO: GlobalAid Relief Network (Fake / Suspicious / High Risk)
('dddddddd-dddd-dddd-dddd-dddddddddddd', '66666666-6666-6666-6666-666666666666',
 'GlobalAid Relief Network', 'trust', 'TEMP/992/UNREG', 'AAXPG9999Z', NULL,
 false, NULL, false, false, 'Delhi', 'New Delhi', 'Delhi',
 2026, 'https://globalaid-emergency-relief.fake', 'Emergency fundraising entity established during monsoon flash floods.',
 'https://images.unsplash.com/photo-1532629345422-7515f3d16bb6?w=150', 'Personal Account G. Sharma', 'PYTM0123456',
 '0021', 'rejected', NULL, NULL)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 4. NGO TRUSTABILITY SCORES
-- =============================================================================

INSERT INTO trustability_scores (
    ngo_id, identity_legal_score, financial_transparency_score,
    operational_performance_score, governance_score, data_completeness_score,
    overall_score, overall_label, methodology_version, breakdown
) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 95, 82, 88, 85, 78, 87, 'verified', '1.0', jsonb_build_object(
    'dimensions', jsonb_build_array(
        jsonb_build_object('dimension', 'Identity & Legal', 'score', 95, 'details', 'Darpan verified (TN/2019/0234567), Active FCRA (076210234), 12A/80G active, 5+ yrs operating'),
        jsonb_build_object('dimension', 'Financial Transparency', 'score', 82, 'details', '3 years audited reports uploaded, 87% program spend ratio, 9% admin overhead'),
        jsonb_build_object('dimension', 'Operational Performance', 'score', 88, 'details', '5 completed campaigns on Eleos, 94% milestone completion rate'),
        jsonb_build_object('dimension', 'Data Completeness', 'score', 78, 'details', 'Core documents uploaded, board member list last updated 2024')
    )
)),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 90, 85, 92, 80, 85, 88, 'verified', '1.0', jsonb_build_object(
    'dimensions', jsonb_build_array(
        jsonb_build_object('dimension', 'Identity & Legal', 'score', 90, 'details', 'Darpan registered, domestic trust compliance complete, 12A/80G active'),
        jsonb_build_object('dimension', 'Financial Transparency', 'score', 85, 'details', 'PDS grain reconciliation audited, 91% program spend ratio'),
        jsonb_build_object('dimension', 'Operational Performance', 'score', 92, 'details', '12 completed feeding cycles, zero unresolved disputes'),
        jsonb_build_object('dimension', 'Data Completeness', 'score', 85, 'details', 'Full compliance certificate and trustee disclosures submitted')
    )
)),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 95, 88, 85, 90, 90, 91, 'verified', '1.0', jsonb_build_object(
    'dimensions', jsonb_build_array(
        jsonb_build_object('dimension', 'Identity & Legal', 'score', 95, 'details', 'Section 8 company, MCA verified, FCRA active, 12A/80G'),
        jsonb_build_object('dimension', 'Financial Transparency', 'score', 88, 'details', 'Audited annual reports with PWD rate reconciliations'),
        jsonb_build_object('dimension', 'Operational Performance', 'score', 85, 'details', '8 rural libraries established on schedule'),
        jsonb_build_object('dimension', 'Data Completeness', 'score', 90, 'details', 'All statutory and child safeguarding policies uploaded')
    )
)),
('dddddddd-dddd-dddd-dddd-dddddddddddd', 5, 0, 0, 10, 15, 12, 'high_risk', '1.0', jsonb_build_object(
    'dimensions', jsonb_build_array(
        jsonb_build_object('dimension', 'Identity & Legal', 'score', 5, 'details', 'No NGO Darpan registry match, No FCRA registration for foreign relief, newly registered entity (<30 days)'),
        jsonb_build_object('dimension', 'Financial Transparency', 'score', 0, 'details', 'Zero audit reports or financial statements submitted'),
        jsonb_build_object('dimension', 'Operational Performance', 'score', 0, 'details', 'No verified project delivery history on platform'),
        jsonb_build_object('dimension', 'Data Completeness', 'score', 15, 'details', 'Only preliminary registration certificate provided, PAN mismatch flagged')
    )
))
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 5. CAMPAIGNS
-- =============================================================================

INSERT INTO campaigns (
    id, ngo_id, title, description, category, location_state, location_district,
    location_country, target_amount, raised_amount, currency, beneficiary_count,
    status, safety_tier, is_disaster_relief, start_date, end_date, cover_image_url,
    blockchain_project_hash, approved_at, approved_by
) VALUES
-- Demo 1: Nepal Flood Relief 2026 (HopeRelief Foundation)
('10000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
 'Nepal Flood Relief 2026',
 'Emergency food, waterproof shelter tents, clean water kits, and mobile healthcare units for 5,000 families displaced by Kathmandu Valley monsoon flash floods.',
 'disaster_relief', 'Bagmati', 'Kathmandu', 'Nepal',
 4700000.00, 2300000.00, 'INR', 5000,
 'active', 'no_volunteers', true, CURRENT_DATE - INTERVAL '14 days', CURRENT_DATE + INTERVAL '16 days',
 'https://images.unsplash.com/photo-1547683905-f686c993aae5?w=800',
 '0x1a2b3c4d5e6f708192a1b2c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3d4e5',
 NOW() - INTERVAL '14 days', '22222222-2222-2222-2222-222222222222'),

-- Demo 2: Mid-Day Meal Program (Annapurna Trust)
('20000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
 'Mid-Day Meal Program — Katpadi & Vellore Schools',
 'Providing wholesome, hot, nutritious mid-day meals and supplementary nutrition for 1,500 children across 12 rural government primary schools for an entire academic term.',
 'nutrition', 'Tamil Nadu', 'Vellore', 'India',
 2200000.00, 1800000.00, 'INR', 1500,
 'active', 'open', false, CURRENT_DATE - INTERVAL '45 days', CURRENT_DATE + INTERVAL '45 days',
 'https://images.unsplash.com/photo-1577896851231-70ef18881754?w=800',
 '0x2b3c4d5e6f708192a1b2c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3d4e5f6',
 NOW() - INTERVAL '45 days', '22222222-2222-2222-2222-222222222222'),

-- Demo 4: TMM Marathon Fundraiser — Rural Libraries (Teach For Change India)
('40000000-0000-0000-0000-000000000004', 'cccccccc-cccc-cccc-cccc-cccccccccccc',
 'TMM 2026 — Rural Tribal School Digital Libraries',
 'Building 3 complete library hubs with books, solar lighting, digital e-readers, and reading tutors for 2,000 tribal students in Raigad district.',
 'education', 'Maharashtra', 'Raigad', 'India',
 2500000.00, 1200000.00, 'INR', 2000,
 'active', 'open', false, CURRENT_DATE - INTERVAL '20 days', CURRENT_DATE + INTERVAL '40 days',
 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=800',
 '0x4d5e6f708192a1b2c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3d4e5f67081',
 NOW() - INTERVAL '20 days', '22222222-2222-2222-2222-222222222222'),

-- Demo 3: Fake Campaign — Nepal Emergency Aid Fund (GlobalAid Relief Network)
('30000000-0000-0000-0000-000000000003', 'dddddddd-dddd-dddd-dddd-dddddddddddd',
 'Nepal Emergency Aid Fund',
 'Urgent expedited disaster relief collection for immediate cash and relief supply distribution in flood areas.',
 'disaster_relief', 'Bagmati', 'Kathmandu', 'Nepal',
 5000000.00, 0.00, 'INR', 1000,
 'pending_review', 'no_volunteers', true, CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days',
 'https://images.unsplash.com/photo-1547683905-f686c993aae5?w=800',
 NULL, NULL, NULL)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 6. BUDGET LINE ITEMS
-- =============================================================================

INSERT INTO budget_items (
    campaign_id, category, description, unit, unit_cost, quantity, total_cost,
    benchmark_unit_cost, benchmark_source, cost_ratio, flag, sort_order
) VALUES
-- Demo 1 Budget Items (Nepal Floods — realistic with transport disaster multiplier)
('10000000-0000-0000-0000-000000000001', 'food', 'Staple Rice (Fortified)', 'kg', 38.00, 50000.00, 1900000.00, 32.00, 'PDS retail, TN', 1.19, 'pass', 1),
('10000000-0000-0000-0000-000000000001', 'shelter', 'Waterproof 4-Person Relief Tents', 'unit', 1200.00, 1000.00, 1200000.00, 900.00, 'NDRF procurement', 1.33, 'pass', 2),
('10000000-0000-0000-0000-000000000001', 'transport', 'Cross-Border Trucking & Remote Transit', 'trip', 35000.00, 10.00, 350000.00, 25000.00, 'Customs + logistics', 1.40, 'pass', 3),
('10000000-0000-0000-0000-000000000001', 'medical', 'Emergency Trauma & Waterborne Medical Kits', 'kit', 450.00, 897.00, 404000.00, 400.00, 'CGHS', 1.13, 'pass', 4),
('10000000-0000-0000-0000-000000000001', 'admin', 'Field Logistics & Emergency Coordination (8%)', 'lump', 376000.00, 1.00, 376000.00, 470000.00, 'FCRA max 20% limit', 0.80, 'pass', 5),
('10000000-0000-0000-0000-000000000001', 'contingency', 'Emergency Route Contingency (10%)', 'lump', 470000.00, 1.00, 470000.00, 705000.00, 'Relief standard <=15%', 0.67, 'pass', 6),

-- Demo 2 Budget Items (Mid-Day Meals — in line with PM POSHAN)
('20000000-0000-0000-0000-000000000002', 'food', 'Primary School Meals (Class 1-5)', 'meal', 5.50, 180000.00, 990000.00, 5.45, 'PM POSHAN FY25-26', 1.01, 'pass', 1),
('20000000-0000-0000-0000-000000000002', 'food', 'Upper Primary School Meals (Class 6-8)', 'meal', 8.20, 90000.00, 738000.00, 8.17, 'PM POSHAN FY25-26', 1.00, 'pass', 2),
('20000000-0000-0000-0000-000000000002', 'nutrition', 'Supplementary Nutrition (Eggs & Seasonal Fruit)', 'meal', 3.50, 60000.00, 210000.00, 3.50, 'State nutrition dept', 1.00, 'pass', 3),
('20000000-0000-0000-0000-000000000002', 'labor', 'Cook & Helper Monthly Honorarium', 'month', 5000.00, 24.00, 120000.00, 5000.00, 'State-set rates', 1.00, 'pass', 4),
('20000000-0000-0000-0000-000000000002', 'admin', 'Kitchen Sanitization & Logistics (6.4%)', 'lump', 142000.00, 1.00, 142000.00, 220000.00, 'Standard <=20%', 0.65, 'pass', 5),

-- Demo 3 Budget Items (Fake Campaign — 4.2x inflated food and 40% misc)
('30000000-0000-0000-0000-000000000003', 'food', 'Emergency Rice & Rations', 'kg', 135.00, 15000.00, 2025000.00, 32.00, 'PDS retail, TN', 4.22, 'fail', 1),
('30000000-0000-0000-0000-000000000003', 'other', 'Miscellaneous Unitemized Relief Fund (40%)', 'lump', 2000000.00, 1.00, 2000000.00, 250000.00, 'Benchmark <=5% unitemized', 8.00, 'fail', 2),
('30000000-0000-0000-0000-000000000003', 'admin', 'Emergency Handling & Management Fees (19.5%)', 'lump', 975000.00, 1.00, 975000.00, 500000.00, 'Standard admin ceiling', 1.95, 'warning', 3)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 7. FEASIBILITY SCORES
-- =============================================================================

INSERT INTO feasibility_scores (
    campaign_id, budget_realism_score, cost_evidence_score,
    beneficiary_consistency_score, timeline_realism_score, operational_capacity_score,
    overall_score, overall_label, context_adjustments, breakdown
) VALUES
('10000000-0000-0000-0000-000000000001', 88, 85, 90, 85, 87, 87, 'high',
 jsonb_build_object('disaster_multiplier', 1.5, 'cross_border_premium', 1.3, 'note', 'Transport cost is 1.4x domestic benchmark; adjusted within cross-border flood logistics window.'),
 jsonb_build_object('summary', 'Budget is realistic and matches emergency disaster relief procurement norms.')
),
('20000000-0000-0000-0000-000000000002', 95, 92, 96, 90, 92, 93, 'high',
 jsonb_build_object('benchmark_source', 'PM POSHAN FY25-26', 'per_meal_cost', 7.80),
 jsonb_build_object('summary', 'Per meal cost of ₹7.80 aligns with national nutrition scheme benchmark schedules.')
),
('40000000-0000-0000-0000-000000000004', 90, 88, 85, 88, 85, 87, 'high',
 jsonb_build_object('infrastructure_schedule', 'MH PWD SoR 2025-26'),
 jsonb_build_object('summary', 'Library room construction costs adhere to Maharashtra PWD Schedule of Rates.')
),
('30000000-0000-0000-0000-000000000003', 10, 5, 25, 20, 10, 14, 'low',
 jsonb_build_object('severe_anomaly', 'Food unit cost is 4.22x benchmark; 40% lump sum unitemized.'),
 jsonb_build_object('summary', 'Multiple severe budget anomalies detected. Blocked for donor safety.')
)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 8. MILESTONES
-- =============================================================================

INSERT INTO milestones (
    campaign_id, title, description, target_date, status,
    evidence_urls, evidence_hash, blockchain_tx_hash, completed_at, verified_by, sort_order
) VALUES
-- Demo 1: Nepal Flood Relief Milestones
('10000000-0000-0000-0000-000000000001', 'Procurement of Grains & Tents', 'Bulk procurement of 50 tonnes of rice and 1,000 waterproof tents with certified vendor receipts.',
 CURRENT_DATE - INTERVAL '10 days', 'verified',
 ARRAY['https://eleos-documents.s3.amazonaws.com/evidence/m1_invoice_01.pdf', 'https://eleos-documents.s3.amazonaws.com/evidence/m1_logistics.pdf'],
 'a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0',
 '0x4a2f89b1c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3',
 NOW() - INTERVAL '10 days', '22222222-2222-2222-2222-222222222222', 1),

('10000000-0000-0000-0000-000000000001', 'First Delivery Batch & Camp Dispatch', 'Delivery of 500 tents and ration kits to flood victims in Lalitpur with geotagged photography logs.',
 CURRENT_DATE - INTERVAL '5 days', 'verified',
 ARRAY['https://eleos-documents.s3.amazonaws.com/evidence/m2_geotagged_delivery.pdf'],
 'b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01a',
 '0x7c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3d4e5f6708192a1b2c3d4e5f67',
 NOW() - INTERVAL '5 days', '22222222-2222-2222-2222-222222222222', 2),

('10000000-0000-0000-0000-000000000001', 'Mobile Medical Camp Setup', 'Deployment of 3 mobile clinics and emergency trauma care dispensaries.',
 CURRENT_DATE + INTERVAL '5 days', 'in_progress',
 NULL, NULL, NULL, NULL, NULL, 3),

('10000000-0000-0000-0000-000000000001', 'Final Relief Distribution Report & Audit', 'Complete reconciliation of all beneficiary aid kits and independent local authority endorsement.',
 CURRENT_DATE + INTERVAL '15 days', 'pending',
 NULL, NULL, NULL, NULL, NULL, 4)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 9. DONATIONS
-- =============================================================================

INSERT INTO donations (
    id, donor_id, campaign_id, amount, currency, payment_method,
    payment_gateway_order_id, payment_gateway_payment_id, status,
    blockchain_tx_hash, blockchain_confirmed, donor_message, is_anonymous, created_at, completed_at
) VALUES
('90000000-0000-0000-0000-000000000001', '77777777-7777-7777-7777-777777777777',
 '10000000-0000-0000-0000-000000000001', 500.00, 'INR', 'upi',
 'order_Qz981029481203', 'pay_Qz981029481203', 'completed',
 '0x3f2a4b5c6d7e8f90123456789abcdef0123456789abcdef0123456789abcdef0', true,
 'Praying for safety in the Kathmandu valley 🙏', false, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),

('90000000-0000-0000-0000-000000000002', '77777777-7777-7777-7777-777777777777',
 '20000000-0000-0000-0000-000000000002', 100.00, 'INR', 'upi',
 'order_Qz981029481204', 'pay_Qz981029481204', 'completed',
 '0x8b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c', true,
 'For the school children in Vellore', false, NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'),

('90000000-0000-0000-0000-000000000003', '77777777-7777-7777-7777-777777777777',
 '40000000-0000-0000-0000-000000000004', 1000.00, 'INR', 'card',
 'order_Qz981029481205', 'pay_Qz981029481205', 'completed',
 '0x5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d', true,
 'Keep building libraries!', false, NOW() - INTERVAL '8 days', NOW() - INTERVAL '8 days')
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 10. VOLUNTEER OPPORTUNITIES & CREDENTIALS
-- =============================================================================

INSERT INTO volunteer_opportunities (
    id, campaign_id, title, description, location,
    start_date, end_date, spots_total, spots_filled, safety_tier, skills_required, min_age
) VALUES
('80000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000004',
 'TMM 2026 — Marathon Day Logistics & Hydration Station',
 'Manage water & electrolyte stations and runner cheer hubs at Tata Mumbai Marathon to raise library funding awareness.',
 'Mumbai, Maharashtra', CURRENT_DATE + INTERVAL '20 days', CURRENT_DATE + INTERVAL '20 days',
 50, 24, 'open', ARRAY['Event management', 'First aid', 'Crowd management'], 18),

('80000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002',
 'Weekend Community Kitchen — Mid-Day Meal Prep',
 'Assist cooks with washing vegetables, packing hot food containers, and distributing meals to students.',
 'Katpadi, Vellore, Tamil Nadu', CURRENT_DATE + INTERVAL '5 days', CURRENT_DATE + INTERVAL '5 days',
 15, 8, 'open', ARRAY['Kitchen hygiene', 'Food packaging'], 16),

('80000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001',
 'Nepal Flood Relief — Remote Data & Translation Support',
 'Digitize local shelter records, translate relief notices into Nepali/Hindi, and maintain beneficiary counts.',
 'Remote', CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days',
 20, 12, 'open', ARRAY['Data entry', 'Translation', 'Social media'], 18)
ON CONFLICT DO NOTHING;

INSERT INTO volunteer_applications (
    id, opportunity_id, user_id, status, applied_at, approved_at
) VALUES
('70000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000001',
 '88888888-8888-8888-8888-888888888888', 'completed', NOW() - INTERVAL '15 days', NOW() - INTERVAL '14 days')
ON CONFLICT DO NOTHING;

INSERT INTO volunteer_credentials (
    id, application_id, hours_logged, ngo_confirmed, ngo_confirmed_at,
    blockchain_tx_hash, certificate_url, certificate_hash
) VALUES
('60000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001',
 8.0, true, NOW() - INTERVAL '10 days',
 '0x5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d',
 'https://eleos-certificates.s3.amazonaws.com/certs/cert_riya_tmm2026.pdf',
 'c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01234'
)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- 11. REVIEW QUEUE
-- =============================================================================

INSERT INTO review_queue (
    entity_type, entity_id, priority, flags, status, reviewer_notes, decision
) VALUES
('ngo', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'critical',
 jsonb_build_array('No NGO Darpan match', 'No FCRA registration', 'Organization age < 30 days', 'PAN mismatch MCA record'),
 'pending', 'Flagged automatically by system scoring pipeline on registration.', NULL),

('campaign', '30000000-0000-0000-0000-000000000003', 'critical',
 jsonb_build_array('Budget item Food cost 4.22x benchmark', '40% budget unitemized miscellaneous', 'Associated with unverified NGO'),
 'pending', 'Immediate hold placed on campaign activation.', NULL)
ON CONFLICT DO NOTHING;

