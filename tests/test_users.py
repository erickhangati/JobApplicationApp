import pytest
from starlette import status
from models import Users
from .conftest import client, TestSessionLocal, test_user
from routers.auth import bcrypt_context
from .utils import user_sample, access_token


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
    user = user_sample()

    # Send a POST request to create the user
    response = client.post('/users', json=user)

    # Assertions for response validation
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "User successfully registered"
    assert "data" in response.json()

    # Validate that the user exists in the database
    db = TestSessionLocal()
    created_user = db.query(Users).filter_by(username="john_doe").first()
    assert created_user is not None
    assert created_user.first_name == "John"
    db.close()


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
        "email": "janedoe@mail.com",
        "username": "jane_doe",
        "password": bcrypt_context.hash("test1234"),
        "role": "USER"
    }

    # Send a POST request to register the user
    response = client.post('/users', json=user)

    # Assertions for response validation
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_users(test_user):
    """
    Test retrieving a paginated list of users.

    Ensures that an authenticated admin user can successfully retrieve a list of users.
    Validates the response structure, status code, and success message.

    Args:
        test_user: A pytest fixture providing a pre-existing authenticated user.

    Assertions:
        - The response status code should be 200 (OK).
        - The response should contain a success message.
        - The response should include a "data" field with user details.
    """

    # Generate an access token for the test user
    _, token = access_token()

    # Send GET request to retrieve users with authorization token
    response = client.get('/users', headers={'Authorization': f'Bearer {token}'})

    # Validate response status
    assert response.status_code == status.HTTP_200_OK, f"Expected 200, but got {response.status_code}"

    # Validate success message
    assert response.json()[
               "message"] == "Users retrieved successfully", "Message mismatch"

    # Ensure response contains the expected data field
    assert "data" in response.json(), "Missing 'data' field in response"


def test_users_not_user():
    """
    Test retrieving users when the requester does not exist in the database.

    Ensures that if an authenticated token is used but the associated user does not exist,
    the API correctly returns a 404 Not Found error.

    Assertions:
        - The response status code should be 404 (Not Found).
        - The response should contain the appropriate error detail message.
    """

    # Generate an access token for a non-existent user
    _, token = access_token()

    # Attempt to retrieve users with an invalid or missing user entry
    response = client.get('/users', headers={'Authorization': f'Bearer {token}'})

    # Validate response status
    assert response.status_code == status.HTTP_404_NOT_FOUND, f"Expected 404, but got {response.status_code}"

    # Validate error message
    assert response.json() == {"detail": "User not found"}, "Unexpected response detail"


@pytest.mark.parametrize("test_user", ["USER"], indirect=True)
def test_users_not_admin(test_user):
    """
    Test case for restricting non-admin users from retrieving the user list.

    Ensures that an authenticated **non-admin** user receives a **403 Forbidden** response
    when attempting to access the `/users` endpoint.

    Args:
        test_user: A pytest fixture providing a non-admin user.

    Assertions:
        - The response status code should be **403 Forbidden**.
    """

    # Generate an access token for the non-admin user
    _, token = access_token()

    # Attempt to fetch users with a non-admin token
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify that the request is forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN, \
        f"Expected 403, but got {response.status_code}"

    # Validate error message
    assert response.json() == {
        "detail": "You do not have permission to perform this action"}, \
        "Unexpected response detail"


def test_delete_user(test_user):
    """
    Test case for deleting a user.

    Ensures that an authenticated **admin user** can successfully delete a user
    and that the user is removed from the database.

    Args:
        test_user: A pytest fixture providing a pre-existing user.

    Assertions:
        - The response status code should be **204 No Content**.
        - The user should no longer exist in the database after deletion.
    """

    # Generate an access token for the admin user
    _, token = access_token()

    # Send DELETE request to remove the user
    response = client.delete(
        f"/users/{test_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert that the request was successful
    assert response.status_code == status.HTTP_204_NO_CONTENT, \
        f"Expected 204, but got {response.status_code}"

    # Verify that the user no longer exists in the database
    db = TestSessionLocal()
    user = db.query(Users).filter(Users.id == test_user.id).first()
    assert user is None, "User was deleted successfully"


def test_delete_user_not_user():
    """
    Test case for deleting a non-existent user.

    Ensures that attempting to delete a user that does not exist results
    in a **404 Not Found** response.

    Assertions:
        - The response status code should be **404 Not Found**.
        - The response should contain the appropriate error message.
    """

    # Generate an access token for authentication
    _, token = access_token()

    # Send DELETE request to attempt removing a non-existent user (ID: 1)
    response = client.delete(
        "/users/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert that the response status code is 404
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected 404, but got {response.status_code}"

    # Assert that the response detail message matches the expected output
    assert response.json() == {"detail": "User not found"}, "Unexpected response detail"
