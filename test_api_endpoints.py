import json
from app import app, db, User

def test_api_suite():
    print("=" * 60)
    print("RUNNING STANDARDIZED REST API & ALGORITHM INFO VERIFICATION")
    print("=" * 60)

    client = app.test_client()

    # Authenticate as field officer
    with app.app_context():
        user = User.query.filter_by(username='field_officer').first()
        assert user is not None, "field_officer account not found"

    with client:
        login_res = client.post('/login', data={'username': 'field_officer', 'password': 'officer123'}, follow_redirects=True)
        assert login_res.status_code == 200, f"Login failed: {login_res.status_code}"
        print("[PASS] Authenticated as Field Officer")

        # 1. TEST /cluster API (K-Means)
        res = client.post('/cluster', json={'state': 'KARNATAKA', 'district': 'BANGALORE COMMR.'})
        assert res.status_code == 200, f"/cluster failed: {res.status_code} - {res.data}"
        data = res.get_json()
        assert data.get('status') == 'success'
        assert data.get('algorithm_used') == 'K-Means Clustering Algorithm'
        assert 'algorithm_info' in data
        assert data['algorithm_info'].get('name') == 'K-Means Clustering Algorithm'
        assert 'predicted_zone' in data
        assert 'confidence_score' in data
        print(f"[PASS] /cluster API -> Algorithm: {data['algorithm_used']}, Zone: {data['predicted_zone']}, Confidence: {data['confidence_score']}")

        # 2. TEST /predict API (Random Forest)
        res = client.post('/predict', json={'state': 'KARNATAKA', 'district': 'BANGALORE COMMR.', 'year': 2026})
        assert res.status_code == 200, f"/predict failed: {res.status_code} - {res.data}"
        data = res.get_json()
        assert data.get('status') == 'success'
        assert data.get('algorithm_used') == 'Random Forest Classifier (Bagged Decision Trees Ensemble)'
        assert 'algorithm_info' in data
        assert data['algorithm_info'].get('name') == 'Random Forest Classifier'
        assert 'predicted_zone' in data
        assert 'confidence_score' in data
        assert 'projected_incidents' in data
        print(f"[PASS] /predict API -> Algorithm: {data['algorithm_used']}, Zone: {data['predicted_zone']}, Confidence: {data['confidence_score']}")

        # 3. TEST /analyze-fir API (VADER NLP + RegEx)
        sample_fir = "FIR No 45/2026. Suspect arrested with illegal country-made deshi katta pistol and sharp knife near Indiranagar, Bengaluru. Section 307 and Arms Act 25."
        res = client.post('/analyze-fir', json={'case_text': sample_fir})
        assert res.status_code == 200, f"/analyze-fir failed: {res.status_code} - {res.data}"
        data = res.get_json()
        assert data.get('status') == 'success'
        assert 'VADER NLP + RegEx Weighted' in data.get('algorithm_used', '')
        assert 'algorithm_info' in data
        assert 'VADER NLP + RegEx Weighted' in data['algorithm_info'].get('name', '')
        assert 'threat_score' in data
        assert 'severity_label' in data
        print(f"[PASS] /analyze-fir API -> Algorithm: {data['algorithm_used']}, Severity: {data['severity_label']}, Threat Score: {data['threat_score']}")

        # 4. TEST /regression API (OLS Linear Regression)
        res = client.post('/regression', json={'state': 'KARNATAKA', 'year': 2026})
        assert res.status_code == 200, f"/regression failed: {res.status_code} - {res.data}"
        data = res.get_json()
        assert data.get('status') == 'success'
        assert data.get('algorithm_used') == 'Ordinary Least Squares (OLS) Linear Regression'
        assert 'algorithm_info' in data
        assert 'predicted_total_ipc_crimes' in data
        assert 'projected_crime_rate_per_lakh' in data
        print(f"[PASS] /regression API -> Algorithm: {data['algorithm_used']}, Projected Crimes: {data['predicted_total_ipc_crimes']}")

        # 5. TEST /projections API (Facebook Prophet)
        res = client.get('/projections')
        assert res.status_code == 200, f"/projections failed: {res.status_code} - {res.data}"
        data = res.get_json()
        assert data.get('status') == 'success'
        assert data.get('algorithm_used') == 'Facebook Prophet (Additive Time-Series Model)'
        assert 'algorithm_info' in data
        assert data['algorithm_info'].get('name') == 'Facebook Prophet'
        print(f"[PASS] /projections API -> Algorithm: {data['algorithm_used']}, Accuracy: {data['algorithm_info'].get('validation_accuracy')}")

    print("=" * 60)
    print("ALL API ENDPOINTS & ALGORITHM INFO PAYLOADS VERIFIED 100%!")
    print("=" * 60)

if __name__ == '__main__':
    test_api_suite()
