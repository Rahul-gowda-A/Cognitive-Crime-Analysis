"""
test_baseline_modules.py
========================
Verification suite for Multi-Module Baseline Update:
1. Spatio-Temporal Beat Engine (Week 3)
2. Generative Case Briefing Engine (Week 4)
3. Role-Based Access Control & Dashboard Routing (Week 5)
"""

import json
import unittest
from app import app, db, User, ROLE_FIELD_OFFICER, ROLE_SP_ADMIN, verify_user_role
from spatial_beat_engine import (
    extract_temporal_features,
    generate_patrol_route,
    SpatialBeatEngine,
    downscale_macro_to_beat
)
from case_briefing_copilot import generate_case_brief


class TestBaselineModules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    # -----------------------------------------------------------------------
    # 1. SPATIO-TEMPORAL BEAT ENGINE TESTS (Week 3)
    # -----------------------------------------------------------------------

    def test_01_feature_extraction(self):
        """Verify extraction of hour_of_day, day_of_week, is_weekend, shift_window."""
        print("\n[TEST 1] Verifying Spatio-Temporal Feature Extraction...")

        # Case A: Night shift weekend
        f1 = extract_temporal_features("2026-08-15 23:45:00")
        self.assertEqual(f1['hour_of_day'], 23)
        self.assertEqual(f1['day_of_week'], 5)  # Saturday
        self.assertEqual(f1['day_name'], "Saturday")
        self.assertEqual(f1['is_weekend'], 1)
        self.assertEqual(f1['shift_window'], "Night")

        # Case B: Morning shift weekday
        f2 = extract_temporal_features("2026-08-17 09:30:00")
        self.assertEqual(f2['hour_of_day'], 9)
        self.assertEqual(f2['day_of_week'], 0)  # Monday
        self.assertEqual(f2['day_name'], "Monday")
        self.assertEqual(f2['is_weekend'], 0)
        self.assertEqual(f2['shift_window'], "Morning")

        # Case C: Evening shift weekday
        f3 = extract_temporal_features("2026-08-19 19:15:00")
        self.assertEqual(f3['hour_of_day'], 19)
        self.assertEqual(f3['shift_window'], "Evening")

        print("  -> Passed: All temporal features extracted accurately.")

    def test_02_spatial_downscaling_and_kmeans_patrol_route(self):
        """Verify K-Means patrol route generation returns ordered list of high-risk waypoints."""
        print("\n[TEST 2] Verifying K-Means High-Risk Patrol Route Generator...")

        waypoints = generate_patrol_route(beat_id="BEAT_101", shift="night", num_waypoints=5)
        self.assertIsInstance(waypoints, list)
        self.assertEqual(len(waypoints), 5)

        for i, wp in enumerate(waypoints, 1):
            self.assertEqual(wp['waypoint_order'], i)
            self.assertIn('latitude', wp)
            self.assertIn('longitude', wp)
            self.assertIn('risk_score', wp)
            self.assertIn('risk_level', wp)
            self.assertIn('tactical_instruction', wp)
            self.assertIn('landmark', wp)
            self.assertGreater(wp['latitude'], 12.0)
            self.assertGreater(wp['longitude'], 77.0)

        # Verify fallback on arbitrary custom beat ID
        custom_route = generate_patrol_route(beat_id="BEAT_ZONAL_999", shift="evening", num_waypoints=4)
        self.assertEqual(len(custom_route), 4)
        print(f"  -> Passed: Generated {len(waypoints)} sequenced waypoints with risk scores and instructions.")

    def test_03_api_patrol_route_endpoint(self):
        """Verify POST /api/patrol-route endpoint in app.py."""
        print("\n[TEST 3] Verifying POST /api/patrol-route Flask endpoint...")

        res = self.client.post('/api/patrol-route', json={
            'beat_id': 'BEAT_102',
            'shift': 'night',
            'num_waypoints': 5
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['beat_id'], 'BEAT_102')
        self.assertEqual(data['shift'], 'night')
        self.assertIn('waypoints', data)
        self.assertEqual(len(data['waypoints']), 5)
        print(f"  -> Passed: /api/patrol-route returned 200 OK with {len(data['waypoints'])} waypoints.")

    # -----------------------------------------------------------------------
    # 2. GENERATIVE CASE BRIEFING ENGINE TESTS (Week 4)
    # -----------------------------------------------------------------------

    def test_04_case_briefing_copilot_logic(self):
        """Verify generate_case_brief returns timeline, evidence gaps, and interrogation questions."""
        print("\n[TEST 4] Verifying Generative Case Briefing Engine Logic...")

        sample_fir = """
        FIR No: 104/2026, Station: Indiranagar Police Station, Date: 15/08/2026, Time: 23:45 hrs.
        Complainant reported that while driving near CMH Road, Bengaluru, two suspects on a motorcycle intercepted the victim.
        One suspect brandished a country-made deshi katta pistol and fired a shot, while the second suspect threatened with a sharp knife and iron rod.
        The victim suffered bleeding injuries and grievous hurt. Suspects extorted Rs. 50,000 cash and gold ornaments.
        Vehicle registration noticed was KA-03-HA-1122. Suspect known by alias 'Kalia'. Contact trace: +919876543210.
        IPC 307, 392, 395, 326 and Arms Act 25 invoked.
        """
        brief = generate_case_brief(sample_fir)

        self.assertEqual(brief['status'], 'success')

        # a) Chronological Timeline of Events
        timeline = brief['chronological_timeline']
        self.assertIsInstance(timeline, list)
        self.assertGreaterEqual(len(timeline), 2)
        self.assertIn('time_marker', timeline[0])
        self.assertIn('event_description', timeline[0])

        # b) Missing Evidence Gaps
        gaps = brief['missing_evidence_gaps']
        self.assertIsInstance(gaps, list)
        self.assertGreaterEqual(len(gaps), 3)
        gap_categories = [g['category'] for g in gaps]
        self.assertTrue(any('Weapon' in cat for cat in gap_categories))
        self.assertTrue(any('CCTV' in cat for cat in gap_categories))

        # c) Suggested Suspect Interrogation Questions
        questions = brief['suggested_interrogation_questions']
        self.assertIsInstance(questions, list)
        self.assertGreaterEqual(len(questions), 4)
        self.assertIn('question_text', questions[0])
        self.assertIn('tactical_objective', questions[0])
        self.assertIn('counter_probe', questions[0])

        print(f"  -> Passed: Dossier generated: {len(timeline)} timeline events, {len(gaps)} evidence gaps, {len(questions)} interrogation questions.")

    def test_05_api_case_briefing_endpoint(self):
        """Verify POST /api/case-briefing endpoint in app.py."""
        print("\n[TEST 5] Verifying POST /api/case-briefing Flask endpoint...")

        res = self.client.post('/api/case-briefing', json={
            'case_narrative': 'On 20 August 2026 at 03:00 HRS, suspects broke open retail shutters using iron crowbar and stole cash in Connaught Place.'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('case_brief', data)
        self.assertIn('chronological_timeline', data['case_brief'])
        self.assertIn('missing_evidence_gaps', data['case_brief'])
        self.assertIn('suggested_interrogation_questions', data['case_brief'])
        print("  -> Passed: /api/case-briefing returned 200 OK with full briefing structure.")

    # -----------------------------------------------------------------------
    # 3. ROLE-BASED ACCESS CONTROL & DASHBOARD ROUTING TESTS (Week 5)
    # -----------------------------------------------------------------------

    def test_06_rbac_verification_logic(self):
        """Verify User model roles and verify_user_role helper."""
        print("\n[TEST 6] Verifying RBAC User Roles & Verification Logic...")

        with app.app_context():
            field_user = User.query.filter_by(username='field_officer').first()
            sp_user = User.query.filter_by(username='sp_admin').first()
            public_user = User.query.filter_by(username='public_user').first()

            self.assertIsNotNone(field_user)
            self.assertIsNotNone(sp_user)
            self.assertIsNotNone(public_user)

            self.assertTrue(field_user.is_field_officer)
            self.assertFalse(field_user.is_sp_admin)

            self.assertTrue(sp_user.is_sp_admin)
            self.assertFalse(sp_user.is_field_officer)

            # Test backwards-compatible case-insensitivity
            self.assertTrue(field_user.role == 'field_officer')
            self.assertTrue(field_user.role == 'FIELD_OFFICER')
            self.assertTrue(field_user.has_role('field_officer'))
            self.assertTrue(field_user.has_role('FIELD_OFFICER'))

        print("  -> Passed: RBAC roles and case-insensitive helpers verified.")

    def test_07_role_aware_dashboard_payload_field_officer(self):
        """Verify role-aware payload for FIELD_OFFICER (beat alerts and patrol route)."""
        print("\n[TEST 7] Verifying FIELD_OFFICER Dashboard Routing & Payload...")

        res = self.client.post('/api/role-dashboard', json={
            'role': 'FIELD_OFFICER',
            'beat_id': 'BEAT_101',
            'shift': 'night'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['role'], 'FIELD_OFFICER')
        self.assertEqual(data['dashboard_type'], 'OPERATIONAL_TACTICAL_FIELD')

        payload = data['payload']
        self.assertIn('beat_alerts', payload)
        self.assertIn('patrol_route', payload)
        self.assertIn('waypoints', payload['patrol_route'])
        self.assertIn('tactical_checklist', payload)
        print(f"  -> Passed: FIELD_OFFICER received {len(payload['beat_alerts'])} beat alerts and {len(payload['patrol_route']['waypoints'])} patrol waypoints.")

    def test_08_role_aware_dashboard_payload_sp_admin(self):
        """Verify role-aware payload for SP_ADMIN (macro-level crime trend analytics)."""
        print("\n[TEST 8] Verifying SP_ADMIN Dashboard Routing & Payload...")

        res = self.client.post('/api/role-dashboard', json={
            'role': 'SP_ADMIN',
            'state': 'KARNATAKA'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['role'], 'SP_ADMIN')
        self.assertEqual(data['dashboard_type'], 'STRATEGIC_MACRO_ANALYTICS')

        payload = data['payload']
        self.assertIn('macro_crime_trends', payload)
        self.assertIn('historical_trajectory', payload['macro_crime_trends'])
        self.assertIn('top_crime_categories', payload['macro_crime_trends'])
        self.assertIn('district_risk_matrix', payload)
        self.assertIn('resource_allocation', payload)
        self.assertIn('strategic_advisories', payload)
        print(f"  -> Passed: SP_ADMIN received macro crime trends, district risk matrix, and {len(payload['strategic_advisories'])} advisories.")

    def test_09_role_aware_dashboard_unauthorized(self):
        """Verify unauthorized/unknown roles receive 403 Forbidden."""
        print("\n[TEST 9] Verifying Unauthorized Role Access Rejection...")

        res = self.client.post('/api/role-dashboard', json={'role': 'CIVILIAN'})
        self.assertEqual(res.status_code, 403)

        res_no_role = self.client.post('/api/role-dashboard', json={})
        self.assertEqual(res_no_role.status_code, 401)
        print("  -> Passed: Unauthorized access correctly rejected with 401/403.")


if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING COGNITIVE CRIME ANALYSIS MULTI-MODULE BASELINE TEST SUITE")
    print("=" * 70)
    unittest.main(verbosity=2)
