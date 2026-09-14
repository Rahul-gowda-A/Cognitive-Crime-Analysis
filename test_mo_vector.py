"""
Standalone pytest suite for MO Vector Engine (mo_vector_service.py) and /api/search-mo API.

Test Cases:
1. Adding 3 mock case narratives (two-wheeler snatching, cyber phishing fraud, residential burglary).
2. Querying 'stolen gold chain on motorcycle' and asserting the snatching case returns as top match with high similarity.
3. Verifying returned dictionary structure matches the /api/search-mo endpoint specification.
"""

import sys
import os
from unittest.mock import MagicMock
import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Dependency fallback stubs (allows running tests in environments where
# heavy ML libraries like chromadb or sentence_transformers are not installed)
# ---------------------------------------------------------------------------
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_REAL_DEPS = True
except ImportError:
    HAS_REAL_DEPS = False

    class MockSentenceTransformer:
        """Lightweight semantic feature encoder for testing without PyTorch."""
        def __init__(self, model_name="all-MiniLM-L6-v2"):
            self.model_name = model_name

        def encode(self, text):
            t = text.lower()
            # Feature dimensions: [snatching/gold/motorcycle, cyber/phishing/bank, burglary/house/window]
            features = [
                any(w in t for w in ["chain", "snatch", "motorcycle", "bike", "gold", "two-wheeler"]),
                any(w in t for w in ["phishing", "sms", "bank", "kyc", "cyber", "transfer", "siphoned"]),
                any(w in t for w in ["burglary", "house", "window", "bungalow", "grille", "safe"]),
            ]
            vec = np.array([1.0 if x else 0.05 for x in features], dtype=float)
            norm = np.linalg.norm(vec)
            return (vec / norm) if norm > 0 else vec

    class MockChromaCollection:
        """In-memory ChromaDB collection mock with cosine similarity calculations."""
        def __init__(self, name="modus_operandi", metadata=None):
            self.name = name
            self.metadata = metadata or {}
            self.docs = {}

        def count(self):
            return len(self.docs)

        def upsert(self, ids, embeddings, documents, metadatas):
            for cid, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
                self.docs[cid] = {
                    "embedding": np.array(emb, dtype=float),
                    "document": doc,
                    "metadata": meta,
                }

        def query(self, query_embeddings, n_results=5, where=None):
            if not self.docs:
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

            q = np.array(query_embeddings[0], dtype=float)
            scored = []
            for cid, data in self.docs.items():
                emb = data["embedding"]
                cos_sim = np.dot(q, emb) / (np.linalg.norm(q) * np.linalg.norm(emb) + 1e-9)
                cos_dist = max(0.0, float(1.0 - cos_sim))
                scored.append((cos_dist, cid, data["document"], data["metadata"]))

            scored.sort(key=lambda x: x[0])
            top = scored[:n_results]

            return {
                "ids": [[x[1] for x in top]],
                "documents": [[x[2] for x in top]],
                "metadatas": [[x[3] for x in top]],
                "distances": [[x[0] for x in top]],
            }

        def get(self, ids):
            found = [i for i in ids if i in self.docs]
            return {
                "ids": found,
                "documents": [self.docs[i]["document"] for i in found],
                "metadatas": [self.docs[i]["metadata"] for i in found],
            }

        def delete(self, ids):
            for i in ids:
                self.docs.pop(i, None)

    class MockChromaClient:
        """In-memory ChromaDB PersistentClient mock."""
        def __init__(self, path=None):
            self.path = path
            self.collections = {}

        def get_or_create_collection(self, name, metadata=None):
            if name not in self.collections:
                self.collections[name] = MockChromaCollection(name, metadata)
            return self.collections[name]

    mock_chroma = MagicMock()
    mock_chroma.PersistentClient = MockChromaClient
    sys.modules["chromadb"] = mock_chroma

    mock_st = MagicMock()
    mock_st.SentenceTransformer = MockSentenceTransformer
    sys.modules["sentence_transformers"] = mock_st


# Import after test stubs are configured in sys.modules
from mo_vector_service import MOVectorEngine
from app import app, get_mo_engine
import app as app_module


# ---------------------------------------------------------------------------
# Test Data Fixtures
# ---------------------------------------------------------------------------
MOCK_CASES = [
    {
        "case_id": "CASE-SNATCH-001",
        "narrative": "Two male suspects riding a black motorcycle intercepted a pedestrian woman in Indiranagar and snatched her gold chain at high speed before fleeing towards Old Airport Road.",
        "metadata": {
            "crime_type": "Chain Snatching",
            "vehicle": "motorcycle",
            "weapon": "none",
            "locality": "Indiranagar",
        },
    },
    {
        "case_id": "CASE-CYBER-002",
        "narrative": "Victim received an unsolicited SMS stating bank account was frozen and clicked on a phishing link. Fake login portal captured credentials, resulting in unauthorized transfer of 85,000 INR.",
        "metadata": {
            "crime_type": "Cyber Crime",
            "sub_category": "Phishing Fraud",
            "financial_loss": 85000,
            "locality": "Whitefield",
        },
    },
    {
        "case_id": "CASE-BURGLARY-003",
        "narrative": "Residential burglary occurred at an unoccupied independent house. Suspects broke open the rear window grille with an iron crowbar and looted diamond jewelry and cash from bedroom wardrobe safe.",
        "metadata": {
            "crime_type": "Burglary",
            "entry_point": "window grille",
            "property_type": "residential bungalow",
            "locality": "Jayanagar",
        },
    },
]


@pytest.fixture
def mo_engine(tmp_path):
    """
    Fixture providing an isolated MOVectorEngine instance for each test.
    """
    test_db_dir = str(tmp_path / "chroma_test_db")
    engine = MOVectorEngine(persist_directory=test_db_dir)
    return engine


@pytest.fixture
def populated_engine(mo_engine):
    """
    Fixture providing an MOVectorEngine populated with the 3 mock crime narratives.
    """
    for case in MOCK_CASES:
        mo_engine.add_case_narrative(
            case_id=case["case_id"],
            narrative_text=case["narrative"],
            metadata_dict=case["metadata"],
        )
    return mo_engine


@pytest.fixture
def flask_test_client(populated_engine):
    """
    Flask test client configured to use the populated_engine for /api/search-mo.
    """
    # Point the global _mo_engine in app to our populated test engine
    app_module._mo_engine = populated_engine
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------
def test_add_three_mock_case_narratives(mo_engine):
    """
    Test 1: Verify adding 3 distinct mock case narratives
    (two-wheeler snatching, cyber phishing fraud, residential burglary).
    """
    assert mo_engine.count() == 0

    for case in MOCK_CASES:
        mo_engine.add_case_narrative(
            case_id=case["case_id"],
            narrative_text=case["narrative"],
            metadata_dict=case["metadata"],
        )

    # Assert total count of cases in vector store is exactly 3
    assert mo_engine.count() == 3

    # Assert all three cases can be retrieved by their IDs
    for case in MOCK_CASES:
        record = mo_engine.get_case(case["case_id"])
        assert record is not None
        assert case["case_id"] in record["ids"]


def test_query_stolen_gold_chain_returns_snatching_as_top_result(populated_engine):
    """
    Test 2: Query 'stolen gold chain on motorcycle' and assert that the
    chain snatching case narrative returns as the top result with a high similarity score.
    """
    query_text = "stolen gold chain on motorcycle"
    results = populated_engine.search_similar_cases(query_text=query_text, top_k=3)

    # Must return results
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"

    top_result = results[0]

    # 1. Assert top match is the snatching case
    assert top_result["case_id"] == "CASE-SNATCH-001", (
        f"Expected top match to be CASE-SNATCH-001, but got {top_result['case_id']}"
    )

    # 2. Assert snatching keywords exist in the matched narrative
    assert "motorcycle" in top_result["narrative"].lower()
    assert "gold chain" in top_result["narrative"].lower()

    # 3. Assert high similarity score
    assert top_result["similarity_score"] >= 0.70, (
        f"Expected similarity score >= 0.70, but got {top_result['similarity_score']}"
    )

    # 4. Assert top result score is strictly greater than the cyber fraud and burglary cases
    second_result = results[1]
    assert top_result["similarity_score"] > second_result["similarity_score"], (
        f"Top score ({top_result['similarity_score']}) should be higher than 2nd score ({second_result['similarity_score']})"
    )


def test_search_results_dict_structure(populated_engine):
    """
    Test 3A: Verify the dictionary structure of items returned by search_similar_cases.
    Each item must contain: case_id, narrative, similarity_score, and metadata.
    """
    results = populated_engine.search_similar_cases(query_text="stolen gold chain on motorcycle", top_k=3)

    assert isinstance(results, list)
    assert len(results) > 0

    expected_keys = {"case_id", "narrative", "similarity_score", "metadata"}

    for item in results:
        assert isinstance(item, dict)
        assert set(item.keys()) == expected_keys
        assert isinstance(item["case_id"], str)
        assert isinstance(item["narrative"], str)
        assert isinstance(item["similarity_score"], (float, int))
        assert 0.0 <= item["similarity_score"] <= 1.0
        assert isinstance(item["metadata"], dict)


def test_api_search_mo_endpoint_response_format(flask_test_client):
    """
    Test 3B: Verify that the /api/search-mo Flask endpoint returns JSON matching
    the expected API specification and contains the top matched snatching case.
    """
    payload = {
        "query": "stolen gold chain on motorcycle",
        "top_k": 3,
    }
    response = flask_test_client.post("/api/search-mo", json=payload)

    # 1. Assert HTTP Status
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.data}"

    data = response.get_json()
    assert isinstance(data, dict)

    # 2. Assert Top-Level API Envelope Keys
    expected_top_keys = {"status", "query", "top_k", "count", "results"}
    assert expected_top_keys.issubset(set(data.keys())), f"Missing keys in API response: {data.keys()}"

    assert data["status"] == "success"
    assert data["query"] == "stolen gold chain on motorcycle"
    assert data["top_k"] == 3
    assert data["count"] == 3
    assert isinstance(data["results"], list)

    # 3. Assert Top Matched Result in API Payload
    top_match = data["results"][0]
    assert top_match["case_id"] == "CASE-SNATCH-001"
    assert top_match["similarity_score"] >= 0.70
    assert "metadata" in top_match
    assert top_match["metadata"].get("crime_type") == "Chain Snatching"

    # 4. Assert Item Structure within results array
    expected_item_keys = {"case_id", "narrative", "similarity_score", "metadata"}
    for item in data["results"]:
        assert expected_item_keys.issubset(set(item.keys()))


def test_api_search_mo_empty_query_validation(flask_test_client):
    """
    Test 4: Verify that empty query strings or missing parameters return HTTP 400.
    """
    response = flask_test_client.post("/api/search-mo", json={"query": "   "})
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "required" in data["message"].lower()


# ---------------------------------------------------------------------------
# Direct Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING MO VECTOR ENGINE STANDALONE TEST SUITE")
    print("=" * 70)
    pytest_exit_code = pytest.main(["-v", __file__])
    sys.exit(pytest_exit_code)
