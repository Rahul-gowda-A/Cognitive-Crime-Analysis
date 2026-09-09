"""
test_bns_parser.py
==================
Standalone pytest test suite for case_parser.py:
  1. Snatching offense -> BNS Section 304 mapping
  2. Cheating/Fraud offense -> BNS Section 318 mapping
  3. Mixed text -> Structured NER entity extraction
"""

try:
    import pytest
except ImportError:
    pytest = None

from case_parser import extract_case_intelligence, extract_entities_ner


def test_snatching_offense_bns_304():
    """Verify mock FIR containing snatching maps to BNS Section 304."""
    fir_text = "Accused on a Pulsar bike snatched a gold chain from complainant near Jayanagar."
    res = extract_case_intelligence(fir_text)
    
    assert res is not None
    assert res['status'] == 'success'
    
    categories = res['ipc_categories']
    snatching_entry = next((c for c in categories if c['category'] == 'Snatching'), None)
    assert snatching_entry is not None, "Snatching category should be detected"
    assert "BNS Sec.304" in snatching_entry['ipc_sections']


def test_cheating_offense_bns_318():
    """Verify mock FIR containing fraud/cheating maps to BNS Section 318."""
    fir_text = "Suspect indulged in fake bank OTP fraud and cheating victim of 50000 rupees."
    res = extract_case_intelligence(fir_text)
    
    assert res is not None
    assert res['status'] == 'success'
    
    categories = res['ipc_categories']
    fraud_entry = next((c for c in categories if c['category'] == 'Financial & Cyber Offense'), None)
    assert fraud_entry is not None, "Financial & Cyber Offense category should be detected"
    assert "BNS Sec.318" in fraud_entry['ipc_sections']


def test_mixed_text_entity_extraction():
    """Verify mixed Kanglish/English narrative populates structured NER entity keys."""
    fir_text = "Aaropi Vicky attacked victim with macchu near Indiranagar-dalli and escaped in KA01AB1234 vehicle."
    res = extract_case_intelligence(fir_text)
    
    assert res is not None
    ner = res['ner_entities']
    
    # Verify entity keys exist
    assert 'suspects' in ner
    assert 'weapons_used' in ner
    assert 'incident_location' in ner
    assert 'vehicle_details' in ner
    
    # Verify entities are populated
    assert len(ner['suspects']) > 0
    assert len(ner['weapons_used']) > 0
    assert len(ner['incident_location']) > 0
    assert len(ner['vehicle_details']) > 0
    
    # Verify exact entity matches
    suspect_names = [s['entity'] for s in ner['suspects']]
    assert any('Vicky' in name for name in suspect_names)
    
    vehicle_regs = [v['entity'] for v in ner['vehicle_details']]
    assert 'KA01AB1234' in vehicle_regs

if __name__ == '__main__':
    print("=" * 60)
    print("RUNNING BNS 2023 PARSER & NER EXTRACTION TESTS")
    print("=" * 60)
    test_snatching_offense_bns_304()
    print("[PASS] test_snatching_offense_bns_304")
    test_cheating_offense_bns_318()
    print("[PASS] test_cheating_offense_bns_318")
    test_mixed_text_entity_extraction()
    print("[PASS] test_mixed_text_entity_extraction")
    print("=" * 60)
    print("ALL BNS PARSER TESTS PASSED (100%)!")
    print("=" * 60)
