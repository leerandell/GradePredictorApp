import pytest
import json
import io
from website import create_app, db
from website.db_model import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory DB for tests
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create all tables
            # Check if user already exists to avoid duplicate error
            user = User.query.filter_by(email='testuser@example.com').first()
            if not user:
                # Add a test user
                user = User(email='testuser@example.com', name='Test User', password=generate_password_hash('testpassword'))
                db.session.add(user)
                db.session.commit()
        yield client

def login(client, email, password):
    return client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def test_predict(client):
    # Log in with a valid user
    login(client, 'testuser@example.com', 'testpassword')
    
    # Define test data
    data = {
        'attendance': 90.0,
        'previous_grades': 85.0,
        'financial_situation': 3.0,
        'learning_environment': 4.0,
        'grade_level': 5
    }

    # Send a POST request to the predict endpoint
    response = client.post('/predict', data=json.dumps(data), content_type='application/json')

    # Assert that the response status code is 200 OK
    assert response.status_code == 200

    # Parse JSON response
    response_data = json.loads(response.data)

    # Assert that the prediction is returned in the response
    assert 'prediction' in response_data
    assert 'student_id' in response_data

def test_upload_file(client):
    # Log in with a valid user
    login(client, 'testuser@example.com', 'testpassword')

    # Create a dummy CSV file to upload
    data = {
        'file': (io.BytesIO(b"attendance,financial_situation,learning_environment,grade_level,previous_grades\n90,3,4,5,85\n"), 'test.csv')
    }

    # Send POST request to upload the CSV file
    response = client.post('/upload', data=data, content_type='multipart/form-data')

    # Assert that the response redirects back to the home page
    assert response.status_code == 302
