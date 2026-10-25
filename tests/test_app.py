
import pytest
from app import app, init_db, get_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_transactions.db"
    monkeypatch.setitem(app.config, "DATABASE", str(test_db))

    init_db()

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_dashboard_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Transaction Insights" in response.data


def test_add_transaction(client):
    response = client.post(
        "/transactions",
        data={
            "merchant": "Test Merchant",
            "amount": "250",
            "status": "Success",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with get_db() as conn:
        transaction = conn.execute(
            "SELECT * FROM transactions WHERE merchant = ?",
            ("Test Merchant",),
        ).fetchone()

    assert transaction is not None
    assert transaction["amount"] == 250
    assert transaction["status"] == "Success"


def test_reject_negative_amount(client):
    response = client.post(
        "/transactions",
        data={
            "merchant": "Invalid Merchant",
            "amount": "-100",
            "status": "Success",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with get_db() as conn:
        transaction = conn.execute(
            "SELECT * FROM transactions WHERE merchant = ?",
            ("Invalid Merchant",),
        ).fetchone()

    assert transaction is None


def test_reject_non_finite_amount(client):
    response = client.post(
        "/transactions",
        data={
            "merchant": "Invalid Merchant",
            "amount": "nan",
            "status": "Success",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with get_db() as conn:
        transaction = conn.execute(
            "SELECT * FROM transactions WHERE merchant = ?",
            ("Invalid Merchant",),
        ).fetchone()

    assert transaction is None


def test_csv_export(client):
    response = client.get("/export")

    assert response.status_code == 200
    assert "text/csv" in response.content_type
    assert "attachment" in response.headers.get(
        "Content-Disposition", ""
    )

    csv_data = response.get_data(as_text=True)

    assert "Merchant" in csv_data
    assert "Book Store" in csv_data


def test_merchant_search(client):
    response = client.get("/?search=Book")

    assert response.status_code == 200
    assert b"Book Store" in response.data
    assert b"Coffee House" not in response.data


def test_status_filter(client):
    response = client.get("/?status=Success")

    assert response.status_code == 200
    assert b"Book Store" in response.data


