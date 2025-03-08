import os
from datetime import timedelta, datetime, timezone

import pytest
from fastapi import HTTPException
from jose import jwt  # JWT encoding/decoding library
from dotenv import load_dotenv
from starlette import status

from routers.auth import create_access_token, get_current_user
from .conftest import test_user, client
from .utils import access_token

# Load environment variables
load_dotenv()

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv('SECRET_KEY')  # Ensure this is set in .env
ALGORITHM = 'HS256'  # Hashing algorithm used for JWT


def test_create_access_token():
    """
    Unit test for the `create_access_token` function.

    This test verifies that:
    1. The access token is generated successfully.
    2. The token contains the correct payload (user ID, role, username).
    3. The expiration time is correctly set in the future.
    4. The token can be successfully decoded with the correct secret key.

    Assertions:
        - The generated token should not be None.
        - Decoded token should contain expected user data.
        - Expiration timestamp should be in the future.
    """

    # Generate an access token
    payload, token = access_token()

    # Ensure the token is generated
    assert token is not None

    # Decode the generated token
    decoded_access_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    # Validate decoded token data
    assert decoded_access_token["id"] == payload["id"]
    assert decoded_access_token["role"] == payload["role"]
    assert decoded_access_token["sub"] == payload["username"]

    # Validate expiration timestamp
    exp_time = datetime.fromtimestamp(decoded_access_token["exp"], timezone.utc)
    assert exp_time > datetime.now(timezone.utc)  # Token should not be expired


@pytest.mark.asyncio
async def test_get_current_user(test_user):
    """
    Test retrieving the authenticated user's details.

    Steps:
    1. Generate a valid JWT token for the test user.
    2. Call `get_current_user()` with the token.
    3. Assert that the returned user data matches the expected payload.

    Expected Outcome:
    - The user is successfully authenticated.
    - The function returns the correct user details.
    """
    payload, token = access_token()
    user = await get_current_user(token)

    assert user is not None  # Ensure user is returned
    assert user["id"] == payload["id"]
    assert user["username"] == payload["username"]
    assert user["role"] == payload["role"]


@pytest.mark.asyncio
async def test_get_current_user_not_exist():
    """
    Test handling of an invalid JWT token where 'id' and 'username' are missing.

    Steps:
    1. Generate a token with missing user ID and username.
    2. Call `get_current_user()` with the token.
    3. Assert that an HTTP 401 Unauthorized exception is raised.

    Expected Outcome:
    - The function raises an HTTPException with status 401.
    - The error message should be 'Could not validate credentials'.
    """
    payload = {
        "username": None,  # Simulating a missing username
        "id": None,  # Simulating a missing user ID
        "role": "ADMIN",
        "expire": timedelta(hours=1),  # Expiration time (1 hour)
    }

    # Generate an invalid access token
    token = create_access_token(
        user_id=payload["id"],  # type: ignore
        username=payload["username"],  # type: ignore
        user_role=payload["role"],
        expire=payload["expire"]
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token)

    # Assertions for HTTP 401 Unauthorized
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"


def test_user_login(test_user):
    """
    Test successful user login.

    Given a registered user with a known username and password,
    when they attempt to log in,
    then they should receive a valid access token.

    Args:
        test_user (Users): A test user fixture from conftest.py.

    Assertions:
        - Response status code should be 201 (Created).
        - Response should contain an "access_token".
        - Token type should be "bearer".
    """

    form_data = {
        "username": "jane_doe",
        "password": "test1234",  # Correct password
    }

    response = client.post("/auth/login", data=form_data)  # Send form-encoded data

    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_user_login_user_does_not_exist():
    """
    Test login attempt with a non-existent user.

    Given an unregistered username,
    when a user attempts to log in,
    then they should receive a 404 Not Found error.

    Assertions:
        - Response status code should be 404 (Not Found).
    """

    form_data = {
        "username": "nonexistent_user",  # User does not exist
        "password": "test1234",
    }

    response = client.post("/auth/login", data=form_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_login_incorrect_password(test_user):
    """
    Test login attempt with an incorrect password.

    Given a registered user with an incorrect password,
    when they attempt to log in,
    then they should receive a 401 Unauthorized error.

    Args:
        test_user (Users): A test user fixture from conftest.py.

    Assertions:
        - Response status code should be 401 (Unauthorized).
    """

    form_data = {
        "username": "jane_doe",
        "password": "wrong_password",  # Incorrect password
    }

    response = client.post("/auth/login", data=form_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
