from app.main import app
from fastapi.testclient import TestClient
import io
import pytest

client=TestClient(app)

def test_running():
    # Ensure client is running
    response=client.get("/")
    assert response.status_code == 200

def test_valid_upload():
    # Test a valid file upload 
    csv_content = """transaction_id,user_id,product_id,timestamp,transaction_amount
T001,42,100,2024-01-01 10:00:00,99.99
T002,42,101,2024-01-02 11:00:00,150.50
T003,43,102,2024-01-03 12:00:00,200.00
"""
    files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["rows_processed"] == 3

def test_upload_invalid_extension():
    # Test non-CSV file is rejected
    files = {'file': ('test.txt', io.BytesIO(b'data'), 'text/plain')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


def test_upload_wrong_headers():
    # Test CSV with wrong headers is rejected
    csv_content = """wrong,headers,here
1,2,3
"""
    files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "Invalid columns." in response.json()["detail"]


def test_upload_empty_file():
    # Test empty CSV is rejected
    csv_content = ""
    files = {'file': ('empty.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400


def test_upload_null_values():
    # Test CSV with null values is rejected
    csv_content = """transaction_id,user_id,product_id,timestamp,transaction_amount
T001,42,100,2024-01-01 10:00:00,
T002,43,101,2024-01-02 11:00:00,150.50
"""
    files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "null" in response.json()["detail"].lower()


def test_upload_negative_amount():
    # Test negative amounts are rejected
    csv_content = """transaction_id,user_id,product_id,timestamp,transaction_amount
T001,42,100,2024-01-01 10:00:00,-50.00
"""
    files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "positive" in response.json()["detail"].lower()


def test_upload_zero_amount():
    # Test zero amounts are rejected
    csv_content = """transaction_id,user_id,product_id,timestamp,transaction_amount
T001,42,100,2024-01-01 10:00:00,0.00
"""
    files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400

@pytest.fixture
def upload_test_data():
    """Pytest fixture that sets up the same set of test data before each test it is passed to as a parameter.
       
       Clears any current data then uploads a predefined set of test data
    """
    client.delete("/clear")
    
    csv_content = """transaction_id,user_id,product_id,timestamp,transaction_amount
T001,42,100,2024-01-15 10:00:00,99.99
T002,42,101,2024-02-20 11:00:00,150.50
T003,42,102,2024-03-25 12:00:00,75.25
T004,43,103,2024-01-10 13:00:00,200.00
"""
    files = {'file': ('test.csv', io.BytesIO(csv_content.encode()), 'text/csv')}
    client.post("/upload", files=files)


def test_summary_valid_request(upload_test_data):
    # Test that summary returns correct statistics
    response = client.get("/summary/42?start_date=2024-01-01&end_date=2024-12-31")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 42
    assert data["transaction_count"] == 3
    assert data["max_amount"] == 150.50
    assert data["min_amount"] == 75.25
    assert data["mean_amount"] == 108.58


def test_summary_user_not_found(upload_test_data):
    # Test 404 is returned for non-existent user 
    response = client.get("/summary/99999?start_date=2024-01-01&end_date=2024-12-31")
    
    assert response.status_code == 404
    assert "no transactions found" in response.json()["detail"].lower()


def test_summary_no_transactions_in_range(upload_test_data):
    # Test 404 is returned when there are no transactions in date range
    response = client.get("/summary/42?start_date=2020-01-01&end_date=2020-12-31")
    
    assert response.status_code == 404


def test_summary_invalid_date_format():
    # Test 422 is returned for invalid date format
    response = client.get("/summary/42?start_date=01-01-2024&end_date=2024-12-31")
    
    assert response.status_code == 422


def test_summary_start_after_end(upload_test_data):
    # Test 400 is returned when start_date after end_date
    response = client.get("/summary/42?start_date=2024-12-31&end_date=2024-01-01")
    
    assert response.status_code == 400
    assert "after" in response.json()["detail"].lower()


def test_summary_negative_user_id():
    # Test that FastAPI validation rejects negative user_id
    response = client.get("/summary/-1?start_date=2024-01-01&end_date=2024-12-31")
    
    assert response.status_code == 422


def test_summary_single_transaction(upload_test_data):
    # Test edge case: user with exactly one transaction
    response = client.get("/summary/43?start_date=2024-01-01&end_date=2024-12-31")
    
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_count"] == 1
    assert data["max_amount"] == 200.00
    assert data["min_amount"] == 200.00
    assert data["mean_amount"] == 200.00
