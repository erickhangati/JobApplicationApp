from datetime import timedelta

from starlette import status
from models import Users
from .conftest import client, TestSessionLocal, test_user
from routers.auth import bcrypt_context, create_access_token
from .utils import access_token


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
    assert response.json()["message"] == "User successfully registered"
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


def test_read_user(test_user):
    """
    Tests retrieving the authenticated user's profile.

    - Sends a valid JWT token in the Authorization header.
    - Asserts that the response status is 200 OK.
    - Checks that the response contains the correct user details.
    """

    # Generate access token for test user
    _, token = access_token()

    # Send request with Authorization header
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Extract user data from response
    response_data = response.json()["data"]

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_data["username"] == "jane_doe"
    assert response_data["email"] == "janedoe@mail.com"
    assert response_data["role"] == "ADMIN"
    assert response_data["first_name"] == "Jane"
    assert response_data["last_name"] == "Doe"


def test_read_user_not_found():
    """
    Test the /users/me endpoint when the user does not exist in the database.
    It should return a 404 NOT FOUND error.
    """

    # Simulate an authentication token for a non-existent user (ID = 9999)
    payload = {
        "id": 9999,
        "username": "ghost_user",
        "role": "USER"
    }

    # Generate JWT token for this non-existent user
    _, token = access_token()

    # Make request with Authorization header
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert that the response returns a 404 NOT FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"

