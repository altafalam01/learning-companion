from fastapi.testclient import TestClient

from learning_companion.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_models_lists_one_model():
    assert len(client.get("/v1/models").json()["data"]) == 1
