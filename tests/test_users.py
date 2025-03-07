from starlette import status
from models import Users
from .conftest import client, TestSessionLocal, test_user
from routers.auth import bcrypt_context


def test_create_user(test_user):
    """
    Test the user registration endpoint.

    This test ensures that a new user can be successfully created
    and stored in the database.

    Steps:
    1. Define a new user payload.
    2. Send a POST request to register the user.
    3. Assert that the response status is 201 CREATED.
    4. Assert that the response contains a success message and user data.
    5. Query the database to verify that the user was stored correctly.
    """

    # New user payload
    user = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@mail.com",
        "username": "john_doe",
        "password": bcrypt_context.hash("test1234"),
        "role": "USER"
    }

    # Send a POST request to create the user
    response = client.post('/users/register', json=user)

    # Assertions for response validation
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "User successfully registered."
    assert "data" in response.json()

    # Validate that the user exists in the database
    db = TestSessionLocal()
    created_user = db.query(Users).filter_by(username="john_doe").first()
    assert created_user is not None
    assert created_user.first_name == "John"


def test_create_user_exists(test_user):
    """
    Test duplicate user registration.

    This test ensures that attempting to register with an already existing
    email or username results in a 400 BAD REQUEST error.

    Steps:
    1. Define a user payload where the email already exists in the database.
    2. Send a POST request to register the user.
    3. Assert that the response status is 400 BAD REQUEST.
    """

    # User payload with an already existing email
    user = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "janedoe@mail.com",  # Already exists
        "username": "jane_doe",
        "password": bcrypt_context.hash("test1234"),
        "role": "ADMIN"
    }

    # Send a POST request to register the user
    response = client.post('/users/register', json=user)

    # Assertions for response validation
    assert response.status_code == status.HTTP_400_BAD_REQUEST
