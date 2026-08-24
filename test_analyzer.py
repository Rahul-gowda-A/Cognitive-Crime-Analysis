import io
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app import app, db, User
from routes import extract_case_intelligence

def run_tests():
    print("==================================================")
    print("RUNNING CASE INTELLIGENCE ANALYZER VERIFICATION")
    print("==================================================")

    # TEST 1: Direct Narrative - Armed Assault & Robbery
    narrative_1 = """
    FIR No: 99/2026, Station: Indiranagar Police Station, Date: 15/08/2026, Time: 23:45 hrs.
    Complainant reported that while driving near CMH Road, Bengaluru, two suspects on a motorcycle intercepted the victim.
    One suspect brandished a country-made deshi katta pistol and fired a shot, while the second suspect threatened with a sharp knife and iron rod.
    The victim suffered bleeding injuries and grievous hurt. Suspects extorted Rs. 50,000 cash and gold ornaments.
    Vehicle registration noticed was KA-03-HA-1122. Suspect known by alias 'Kalia'. Contact trace: +919876543210.
    IPC 307, 392, 395, 326 and Arms Act 25 invoked.
    """
    res1 = extract_case_intelligence(narrative_1, "Test FIR 1")
    assert res1 is not None, "Test 1 failed: Result is None"
    assert res1['severity_label'] == "HIGH RISK", f"Test 1 failed: Expected HIGH RISK, got {res1['severity_label']}"
    assert len(res1['weapons']) > 0, "Test 1 failed: Expected detected weapons"
    assert any('Bangalore' in l or 'Bengaluru' in l or 'CMH Road' in l for l in res1['locations']), f"Test 1 failed locations: {res1['locations']}"
    assert len(res1['timeline']) > 0, f"Test 1 failed timeline: {res1['timeline']}"
    assert len(res1['ipc_categories']) > 0, f"Test 1 failed ipc_categories: {res1['ipc_categories']}"
    assert len(res1['tactical_signals']['vehicles']) > 0, f"Test 1 failed vehicles: {res1['tactical_signals']}"
    print("[PASS] Test 1: Armed Dacoity & Firearm FIR correctly classified as HIGH RISK with extracted entities.")
    print(f"       Threat Score: {res1['threat_score']}, Weapons: {len(res1['weapons'])}, Locations: {res1['locations']}")

    # TEST 2: Direct Narrative - Cyber Fraud
    narrative_2 = """
    Cyber Incident Report: On 10 June 2026 at 14:00 hours, victim in Whitefield, Bangalore was defrauded of Rs. 3,50,000 via phishing ransomware and forged bank documents. No physical weapons were used. IT Act 66D and IPC 420 applicable.
    """
    res2 = extract_case_intelligence(narrative_2, "Test FIR 2")
    assert res2 is not None, "Test 2 failed: Result is None"
    assert res2['severity_label'] in ["MODERATE THREAT", "LOW THREAT"], f"Test 2 failed: Expected MODERATE/LOW, got {res2['severity_label']}"
    print(f"[PASS] Test 2: Cyber Fraud correctly classified as {res2['severity_label']} with Threat Score {res2['threat_score']}.")

    # TEST 3: PDF Ingestion Simulation
    pdf_buffer = io.BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=letter)
    p.drawString(100, 750, "CRIME REPORT DOSSIER // RESTRICTED")
    p.drawString(100, 720, "Date: 12/07/2026, Location: Shivaji Nagar, Pune.")
    p.drawString(100, 690, "Police seized 5 kg contraband narcotics smack and an illegal revolver with 10 cartridges.")
    p.drawString(100, 660, "Suspect arrested under NDPS Act and Arms Act.")
    p.showPage()
    p.save()
    pdf_buffer.seek(0)

    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_buffer)
    extracted_pdf_text = "\n".join([page.extract_text() for page in reader.pages])
    res3 = extract_case_intelligence(extracted_pdf_text, "Test PDF")
    assert res3 is not None, "Test 3 failed: Result is None"
    assert any('NDPS' in c['category'] or 'Contraband' in c['category'] for c in res3['ipc_categories']), "Test 3 failed: NDPS not detected"
    print(f"[PASS] Test 3: PDF Document extraction & analysis successful. Severity: {res3['severity_label']}, Score: {res3['threat_score']}.")

    # TEST 4: Flask Test Client & Role-Based Access Control
    with app.test_client() as client:
        # 4a. Unauthenticated access to /analyze_case should redirect to /login
        resp_unauth = client.get('/analyze_case')
        assert resp_unauth.status_code == 302, f"Expected 302 redirect for unauth, got {resp_unauth.status_code}"
        assert '/login' in resp_unauth.headers['Location']
        print("[PASS] Test 4a: Unauthenticated access blocked and redirected to login.")

        # 4b. Authenticated as public_user -> Should be blocked (role_required('field_officer'))
        client.post('/login', data={'username': 'public_user', 'password': 'public123'})
        resp_public = client.get('/analyze_case')
        assert resp_public.status_code == 302, "Expected 302 redirect for public_user"
        print("[PASS] Test 4b: Public user access blocked by RBAC.")
        client.get('/logout')

        # 4c. Authenticated as field_officer -> GET /analyze_case should return 200 OK
        resp_login = client.post('/login', data={'username': 'field_officer', 'password': 'officer123'}, follow_redirects=True)
        assert resp_login.status_code == 200
        
        resp_officer_get = client.get('/analyze_case')
        assert resp_officer_get.status_code == 200, f"Expected 200 for field_officer GET, got {resp_officer_get.status_code}"
        assert b'Case Narrative Intelligence Engine' in resp_officer_get.data
        print("[PASS] Test 4c: Field Officer GET /analyze_case returned 200 OK with UI template.")

        # 4d. Field Officer POST /analyze_case with form narrative
        resp_officer_post = client.post('/analyze_case', data={
            'case_text': narrative_1
        }, follow_redirects=True)
        assert resp_officer_post.status_code == 200
        assert b'THREAT SEVERITY CLASSIFICATION' in resp_officer_post.data
        assert b'HIGH RISK' in resp_officer_post.data
        print("[PASS] Test 4d: Field Officer POST /analyze_case generated full intelligence dossier.")

        # 4e. Field Officer POST /analyze_case with uploaded PDF file
        pdf_buffer.seek(0)
        resp_officer_pdf = client.post('/analyze_case', data={
            'case_file': (pdf_buffer, 'incident_report.pdf')
        }, content_type='multipart/form-data', follow_redirects=True)
        assert resp_officer_pdf.status_code == 200
        assert b'THREAT SEVERITY CLASSIFICATION' in resp_officer_pdf.data
        print("[PASS] Test 4e: Field Officer POST with PDF file upload processed and rendered.")

        # 4f. Field Officer POST /analyze_case with uploaded TXT file
        txt_buffer = io.BytesIO(b"FIR: On 25/08/2026 at 21:00 hrs, suspect attacked officer with knife in Koramangala Bangalore.")
        resp_officer_txt = client.post('/analyze_case', data={
            'case_file': (txt_buffer, 'fir_statement.txt')
        }, content_type='multipart/form-data', follow_redirects=True)
        assert resp_officer_txt.status_code == 200
        assert b'THREAT SEVERITY CLASSIFICATION' in resp_officer_txt.data
        assert b'Koramangala' in resp_officer_txt.data or b'Bangalore' in resp_officer_txt.data
        print("[PASS] Test 4f: Field Officer POST with TXT file upload processed and rendered.")

    print("==================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
