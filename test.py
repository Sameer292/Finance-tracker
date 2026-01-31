import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import db.models as models

# ---------- Setup a test database ----------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # simple SQLite for tests
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ---------- Global variables ----------
tokens = {}

# ---------- Auth tests ----------
def test_register_and_login():
    # Register
    response = client.post("/register", json={
        "name": "Test User",
        "email": "testuser@gmail.com",
        "password": "password123"
    })
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data

    # Login
    response = client.post("/login", json={
        "email": "testuser@gmail.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    tokens["access"] = data["access_token"]
    tokens["refresh"] = data["refresh_token"]
    assert "access_token" in data

# ---------- Transaction tests ----------
def test_transaction_crud():
    headers = {"Authorization": f"Bearer {tokens['access']}"}

    # Add a transaction
    response = client.post("/transactions", json={
        "transaction_type": "expense",
        "amount": 1000,
        "note": "Initial deposit",
        "category_id": None,
        "transaction_date": "2026-02-01"
    }, headers=headers)
    assert response.status_code == 201
    txn_id = response.json()["transaction_id"]

    # Get transaction
    response = client.get(f"/transactions/{txn_id}", headers=headers)
    assert response.status_code == 200

    # Update transaction
    response = client.put(f"/transactions/{txn_id}", json={
        "transaction_type": "income",
        "amount": 500,
        "note": "Bought snacks",
        "category_id": None,
        "transaction_date": "2026-02-01"
    }, headers=headers)
    assert response.status_code == 200

    # Delete transaction
    response = client.delete(f"/transactions/{txn_id}", headers=headers)
    assert response.status_code == 200

# ---------- Category tests ----------
def test_category_crud():
    headers = {"Authorization": f"Bearer {tokens['access']}"}

    # Add a category
    response = client.post("/categories", json={
        "name": "Food",
        "color": "#FF0000",
        "icon": "🍔"
    }, headers=headers)
    assert response.status_code == 201
    cat_id = response.json()["id"]

    # Get all categories
    response = client.get("/categories", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["categories"]) > 0

    # Get single category
    response = client.get(f"/category/{cat_id}", headers=headers)
    assert response.status_code == 200

    # Delete category
    response = client.delete(f"/category/{cat_id}", headers=headers)
    assert response.status_code == 200
