import os
import io
import json
import pandas as pd
from app import app, db, User

def test_all():
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username='field_officer').first()
        assert user is not None

    with client:
        # 1. Login
        resp = client.post('/login', data={'username': 'field_officer', 'password': 'officer123'}, follow_redirects=True)
        assert resp.status_code == 200

        # ========================================================
        # TEST 1: K-MEANS FORM SUBMISSION (HTML POST)
        # ========================================================
        print("\n--- TEST 1: K-Means Form Submission ---")
        # Submit KARNATAKA / BANGALORE COMMR.
        res_km = client.post('/KMeansanalysis', data={
            'state_input': 'KARNATAKA',
            'district_input': 'BANGALORE COMMR.'
        }, follow_redirects=True)
        assert res_km.status_code == 200
        assert b'RED ZONE' in res_km.data or b'GREEN ZONE' in res_km.data or b'ORANGE ZONE' in res_km.data
        print("[PASS] K-Means Form submission returned rendered result!")

        # ========================================================
        # TEST 2: RANDOM FOREST FORM SUBMISSION (HTML POST)
        # ========================================================
        print("\n--- TEST 2: Random Forest Form Submission ---")
        res_rf = client.post('/randomfrstcls', data={
            'state_input': 'KARNATAKA',
            'district_input': 'BANGALORE COMMR.',
            'year': '2026'
        }, follow_redirects=True)
        assert res_rf.status_code == 200
        print("RF Response snippet:", [line for line in res_rf.data.decode('utf-8').split('\n') if 'prediction-text' in line or 'ZONE' in line][:5])
        assert b'RED ZONE' in res_rf.data or b'GREEN ZONE' in res_rf.data or b'ORANGE ZONE' in res_rf.data
        print("[PASS] Random Forest Form submission returned rendered result!")

        # ========================================================
        # TEST 3: LINEAR REGRESSION FORM SUBMISSION (HTML POST)
        # ========================================================
        print("\n--- TEST 3: Linear Regression Form Submission ---")
        res_lr = client.post('/linearreg', data={
            'state_input': 'Karnataka',
            'year': '2026'
        }, follow_redirects=True)
        assert res_lr.status_code == 200
        print("LR Response snippet:", [line for line in res_lr.data.decode('utf-8').split('\n') if 'PROJECTED' in line][:5])
        assert b'PROJECTED IPC VOL' in res_lr.data
        print("[PASS] Linear Regression Form submission returned rendered result!")

        # ========================================================
        # TEST 4: FIR CASE ANALYZER FORM SUBMISSION
        # ========================================================
        print("\n--- TEST 4: FIR Case Analyzer Form Submission ---")
        sample_fir = "Accused armed with firearm / pistol attacked complainant near Indiranagar, Bengaluru. Case registered under IPC 307."
        res_fir = client.post('/analyze_case', data={
            'case_text': sample_fir
        }, follow_redirects=True)
        assert res_fir.status_code == 200
        assert b'HIGH RISK' in res_fir.data
        print("[PASS] FIR Threat Assessment returned rendered result!")

        # ========================================================
        # TEST 5: TIME SERIES FORECASTING ROUTES
        # ========================================================
        print("\n--- TEST 5: Time Series Forecasting Routes ---")
        res_ts1 = client.get('/timeseriescr')
        assert res_ts1.status_code == 200
        assert b'Longitudinal Crime Projections' in res_ts1.data
        assert b'forecast.html' in res_ts1.data

        res_ts2 = client.get('/timeseriesipc')
        assert res_ts2.status_code == 200
        assert b'Longitudinal Crime Projections' in res_ts2.data
        assert b'forecast(total_ipc).html' in res_ts2.data
        print("[PASS] Both Time Series Horizon views returned 200 OK with correct assets!")

        # ========================================================
        # TEST 6: CRIME FEED & SCRAPER TRIGGER
        # ========================================================
        print("\n--- TEST 6: Crime Feed & Scraper Trigger ---")
        res_cf = client.get('/crimefeed')
        assert res_cf.status_code == 200
        assert b'Real-Time Spatial Heatmap HUD' in res_cf.data

        res_run = client.get('/run-file')
        assert res_run.status_code == 200
        print(f"Scraper execution response: {res_run.get_json()}")
        print("[PASS] Crime feed and scraper pipeline functional!")

        # ========================================================
        # TEST 7: VISUAL ANALYTICS ROUTES
        # ========================================================
        print("\n--- TEST 7: Visual Analytics Routes ---")
        assert client.get('/analysis').status_code == 200
        assert client.get('/analysis2').status_code == 200
        assert client.get('/analysis3').status_code == 200
        assert client.get('/datadisp').status_code == 200
        print("[PASS] Visual Analytics and Datasets functional!")

    print("\n========================================================")
    print("ALL TESTS COMPLETED!")
    print("========================================================")

if __name__ == '__main__':
    test_all()
