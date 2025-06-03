import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_budget_requires_login(client):
    resp = client.get('/budget')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

def test_invalid_login(client):
    resp = client.post('/login', data={'email': 'invalid@example.com', 'password': 'wrong'}, follow_redirects=True)
    assert b'Invalid email or password.' in resp.data
