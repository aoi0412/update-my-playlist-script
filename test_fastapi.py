from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
response = client.get("/api/settings/cookies/status")
print(f"Status defined in app: {response.status_code}")
print(response.json())
