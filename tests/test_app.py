import sys
import os
import io
import pytest
from flask import Flask, render_template,session, request, redirect, url_for, flash,Blueprint

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, security_questions
from home import get_db 
from admin import validate_image_files

class MockFile:
    def __init__(self, filename, mime_type):
        self.filename = filename
        self.mime_type = mime_type
        self.stream = io.BytesIO(b"fake content") 
        

@pytest.fixture
def client():
    app.config['TESTING'] = True  
    with app.test_client() as client:
        yield client 

def test_app_health(client):
    response = client.get('/')
    assert response.status_code == 302
    assert response.location.endswith('/login')

def test_get_db(client):
    with app.app_context():  
        db, cursor = get_db()  
        assert db is not None 
        assert cursor is not None  

def test_validate_image_files_invalid():
    invalid_files = [MockFile('document.txt', 'text/plain')]
    valid, error = validate_image_files(invalid_files)
    assert valid is False
    assert error == "Invalid file type for image 'document.txt'. Allowed types are .jpg, .jpeg, .png, .gif, .bmp"

def test_access_control_restricted_pages(client):
    # Test access to gallery without login
    response = client.get('/gallery')
    assert response.status_code == 200
    assert b'<h1>You are not authorized</h1>' in response.data
    assert b'<meta http-equiv="refresh" content="5; url=' in response.data
    assert b'Redirecting in <span id="countdown">5</span>' in response.data

    # Test access to room gallery without login
    response = client.get('/gallery')
    assert response.status_code == 200
    assert b'<h1>You are not authorized</h1>' in response.data
    assert b'<meta http-equiv="refresh" content="5; url=' in response.data

    # Test access to adminpage without login
    response = client.get('/adminpage')
    assert response.status_code == 200
    assert b'<h1>You are not authorized</h1>' in response.data
    assert b'<meta http-equiv="refresh" content="5; url=' in response.data


