import pytest
from starlette import status

from models import Jobs
from .conftest import (test_job, test_user, test_applied_job, test_user_applied_job,
                       client, TestSessionLocal)
from .utils import access_token, job_sample


def test_read_jobs_response_format():
    """
    Test if the /jobs endpoint returns a JSONResponse.

    - Sends a request to the /jobs endpoint.
    - Asserts that the response has a valid JSON structure.
    - Checks for expected keys in the response.
    """
    response = client.get("/jobs")

    # Assert that the response has a valid JSON structure
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"

    # Check if the response contains expected keys
    json_data = response.json()
    assert "message" in json_data
    assert "data" in json_data
    assert "page" in json_data["data"]
    assert "page_size" in json_data["data"]
    assert "total_jobs" in json_data["data"]
    assert "filtered_jobs_count" in json_data["data"]
    assert "total_pages" in json_data["data"]
    assert "jobs" in json_data["data"]

    # Ensure that jobs is a list
    assert isinstance(json_data["data"]["jobs"], list)


@pytest.mark.parametrize("title,expected_count", [
    ("Test Job", 1),  # Exact match should return 1 result
    ("Nonexistent Title", 0),  # No matching job should return 0 results
])
def test_filter_jobs_by_title(test_job, title, expected_count):
    """
    Tests filtering jobs by title.

    - Sends a request with the `title` query parameter.
    - Checks if the response contains the expected number of results.
    """
    response = client.get(f"/jobs?title={title}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["filtered_jobs_count"] == expected_count


@pytest.mark.parametrize("location,expected_count", [
    ("Test Location", 1),  # Exact match should return 1 result
    ("Random Location", 0),  # No matching job should return 0 results
])
def test_filter_jobs_by_location(test_job, location, expected_count):
    """
    Tests filtering jobs by location.

    - Sends a request with the `location` query parameter.
    - Checks if the response contains the expected number of results.
    """
    response = client.get(f"/jobs?location={location}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["filtered_jobs_count"] == expected_count


@pytest.mark.parametrize("company,expected_count", [
    ("Test Company", 1),  # Exact match should return 1 result
    ("Unknown Company", 0),  # No matching job should return 0 results
])
def test_filter_jobs_by_company(test_job, company, expected_count):
    """
    Tests filtering jobs by company name.

    - Sends a request with the `company` query parameter.
    - Checks if the response contains the expected number of results.
    """
    response = client.get(f"/jobs?company={company}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["filtered_jobs_count"] == expected_count


@pytest.mark.parametrize("remote_allowed,expected_count", [
    (True, 1),  # Exact match should return 1 result
    (False, 0),  # No matching job should return 0 results
])
def test_filter_jobs_by_remote_allowed(test_job, remote_allowed, expected_count):
    """
    Tests filtering jobs by remote_allowed (True/False).

    - Sends a request with the `remote_allowed` query parameter.
    - Checks if the response contains the expected number of results.
    """
    response = client.get(f"/jobs?remote_allowed={remote_allowed}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["filtered_jobs_count"] == expected_count


@pytest.mark.parametrize("min_salary,expected_count", [
    (10000, 1),  # Exact match should return 1 result
    (15000, 0),  # No matching job should return 0 results
])
def test_filter_jobs_by_min_salary(test_job, min_salary, expected_count):
    """
    Tests filtering jobs by min_salary.

    - Sends a request with the `min_salary` query parameter.
    - Checks if the response contains the expected number of results.
    """
    response = client.get(f"/jobs?min_salary={min_salary}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["filtered_jobs_count"] == expected_count


@pytest.mark.parametrize("invalid_value", ["abc", "10.5", "one thousand", "", " "])
def test_filter_jobs_by_min_salary_invalid_value(invalid_value):
    """
    Tests handling of invalid min_salary values.

    - Sends requests with non-integer values for min_salary.
    - Expects a 422 validation error from FastAPI.
    """
    response = client.get(f"/jobs?min_salary={invalid_value}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("invalid_value", ["abc", "10.5", "one thousand", "", " "])
def test_filter_jobs_by_max_salary_invalid_value(invalid_value):
    """
    Tests handling of invalid min_salary values.

    - Sends requests with non-integer values for min_salary.
    - Expects a 422 validation error from FastAPI.
    """
    response = client.get(f"/jobs?max_salary={invalid_value}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_read_job(test_job):
    """
    Tests retrieving a single job by ID.

    - Sends a GET request for a job with the test_job's ID.
    - Asserts that the response status is 200 OK.
    - Verifies that the job details match the expected values.
    """

    # Use the actual test job ID to avoid hardcoding
    response = client.get(f"/jobs/{test_job.id}")

    # Ensure the request was successful
    assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}"

    # Extract response JSON
    response_data = response.json()

    # Assertions on the response structure
    assert response_data["message"] == "Job retrieved successfully", "Message mismatch"

    job_data = response_data["data"]
    assert job_data["id"] == test_job.id, "Job ID mismatch"
    assert job_data["title"] == test_job.title, "Title mismatch"
    assert job_data["company"] == test_job.company, "Company mismatch"
    assert job_data["location"] == test_job.location, "Location mismatch"
    assert job_data["min_salary"] == test_job.min_salary, "Min Salary mismatch"
    assert job_data["max_salary"] == test_job.max_salary, "Max Salary mismatch"
    assert (job_data["remote_allowed"]
            == test_job.remote_allowed), "Remote Allowed mismatch"


def test_read_job_dont_exist():
    """
    Tests retrieving a single job by non_existent ID.

    - Sends a GET request for a job with a non_existent ID.
    - Asserts that the response status is 404 OK.
    """

    # Use the actual test job ID to avoid hardcoding
    response = client.get(f"/jobs/999")

    # Ensure the request was successful
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected 404, got {response.status_code}"


def test_apply_job(test_applied_job, test_job, test_user):
    """
    Test case for applying to a job posting.

    This test sends a POST request to apply for a job and verifies that:
    1. The response status code is 201 (Created).
    2. The response message confirms successful job application.
    3. The returned user_id matches the expected test user.
    4. The returned job_id matches the expected test job.

    Args:
        test_applied_job: Fixture providing the applied job instance.
        test_job: Fixture providing the job instance to apply for.
        test_user: Fixture providing the user instance applying for the job.
    """
    # Send POST request to apply for the job
    response = client.post(f"/jobs/{test_job.id}/apply")

    # Extract JSON response data
    response_data = response.json()

    # Assert the response status code
    assert response.status_code == status.HTTP_201_CREATED, f"Expected 201, got {response.status_code}"

    # Validate response message
    assert response_data['message'] == "Job applied successfully", "Message mismatch"

    # Verify that the correct user and job IDs are returned
    assert response_data['data']["user_id"] == test_user.id, "User ID mismatch"
    assert response_data['data']["job_id"] == test_job.id, "Job ID mismatch"


def test_apply_job_nonexistent_job(test_applied_job, test_user):
    """
    Test applying for a nonexistent job.

    This test ensures that attempting to apply for a job that does not exist
    results in a 404 Not Found response.

    Args:
        test_applied_job: Fixture for an applied job (if needed for setup).
        test_user: Fixture representing the user applying for the job.

    Assertions:
        - The response status code should be 404 (Not Found).
    """

    # Attempt to apply for a nonexistent job (assuming job ID 1 does not exist)
    response = client.post("/jobs/1/apply")

    # Verify the response status code
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected status 404, but got {response.status_code}"


def test_apply_job_nonexistent_user(test_applied_job, test_job):
    """
    Test applying for a nonexistent user.

    This test ensures that attempting to apply for a job with non-existent user
    results in a 404 Not Found response.

    Args:
        test_applied_job: Fixture for an applied job (if needed for setup).
        test_job: Fixture representing the job being applied.

    Assertions:
        - The response status code should be 404 (Not Found).
    """

    # Attempt to apply for a nonexistent job (assuming job ID 1 does not exist)
    response = client.post(f"/jobs/{test_job.id}/apply")

    # Verify the response status code
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected status 404, but got {response.status_code}"


def test_read_user_applied_jobs(test_user_applied_job, test_user):
    _, token = access_token()

    response = client.get("/jobs/applied", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK, f"Expected 200 OK, but got {response.status_code}"

    json_data = response.json()
    assert "message" in json_data
    assert "data" in json_data
    assert "page" in json_data["data"]
    assert "page_size" in json_data["data"]
    assert "applied_jobs_count" in json_data["data"]
    assert "total_pages" in json_data["data"]
    assert "jobs" in json_data["data"]

    # Ensure that jobs is a list
    assert isinstance(json_data["data"]["jobs"], list)


def test_read_applied_jobs_user_dont_exist(test_user_applied_job):
    """
    Test retrieving applied jobs for a non-existent user.

    This test ensures that if an authenticated user who does not exist in the database
    tries to retrieve their applied jobs, the API responds with a 404 Not Found error.

    Args:
        test_user_applied_job: Fixture for setting up an applied job scenario.

    Assertions:
        - The response status code should be 404 (Not Found).
        - The error message should indicate that the user was not found.
    """

    # Generate an access token for authentication
    _, token = access_token()

    # Attempt to retrieve applied jobs for a nonexistent user
    response = client.get(
        "/jobs/applied",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify the response status code and error message
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected 404, but got {response.status_code}"
    assert response.json()["detail"] == "User not found", "Detail mismatch"


def test_create_job(test_job, test_user):
    """
    Test creating a new job listing.

    This test verifies that an authenticated user can successfully create a job
    and that the job is stored correctly in the database.

    Args:
        test_job: Fixture providing a sample job.
        test_user: Fixture providing a sample user.

    Assertions:
        - The response status code should be 201 (Created).
        - The response should contain a success message.
        - The created job should exist in the database with the correct title.
    """

    # Generate an access token for authentication
    _, token = access_token()

    # Prepare a sample job payload
    job = job_sample()

    # Send a POST request to create a new job
    response = client.post(
        "/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Verify the response status code and message
    assert response.status_code == status.HTTP_201_CREATED, \
        f"Expected 201, but got {response.status_code}"
    assert response.json()["message"] == "Job created successfully", "Message mismatch"
    assert "data" in response.json(), "Response does not contain job data"

    # Query the database to confirm job creation
    db = TestSessionLocal()
    created_job_id = response.json().get("data", {}).get("id")  # Dynamically get job ID
    created_job = db.query(Jobs).filter(Jobs.id == created_job_id).first()

    # Ensure the job was successfully created
    assert created_job is not None, "Job was not found in the database"
    assert created_job.title == job.get(
        "title"), "Job title does not match the request data"

    # Close the database session
    db.close()


def test_create_job_user_dont_exist(test_job):
    """
    Test creating a job when the user does not exist.

    This test ensures that attempting to create a job with an authenticated user
    who does not exist in the database results in a 404 Not Found error.

    Args:
        test_job: Fixture for a sample job (if needed for setup).

    Assertions:
        - The response status code should be 404 (Not Found).
        - The error message should indicate that the user was not found.
    """

    # Generate an access token for authentication
    _, token = access_token()

    # Create a sample job payload
    job = job_sample()

    # Attempt to create a job with a nonexistent user
    response = client.post(
        "/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Verify the response status code and error message
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected 404, but got {response.status_code}"
    assert response.json()["detail"] == "User not found", "Detail mismatch"


@pytest.mark.parametrize("test_user", ["USER"], indirect=True)
def test_create_job_user_not_admin(test_user):
    """
    Test that a non-admin user cannot create a job.

    This test ensures that when a user with the role "USER" attempts to create a job,
    the request is denied with a 403 Forbidden response.

    Args:
        test_user_role: Fixture that dynamically sets the user role.

    Assertions:
        - The response status code should be 403 (Forbidden).
        - The response should contain the correct error detail.
    """

    # Generate an access token for the non-admin user
    _, token = access_token()

    # Create a sample job payload
    job = job_sample()

    # Attempt to create a job
    response = client.post(
        "/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Validate the response
    assert response.status_code == status.HTTP_403_FORBIDDEN, \
        f"Expected 403, but got {response.status_code}"

    assert response.json()[
               "detail"] == "You do not have permission to perform this action", \
        "Detail mismatch"


def test_update_job(test_job, test_user):
    """
    Test updating an existing job listing.

    This test verifies that an authenticated admin user can successfully update
    an existing job listing using a PUT request.

    Args:
        test_job: Fixture providing a pre-existing job instance.
        test_user: Fixture providing an authenticated user instance.

    Assertions:
        - The response status code should be 204 (No Content), indicating a successful
        update.
    """

    # Generate an access token for authentication
    _, token = access_token()

    # Create a sample job update payload
    job = job_sample()

    # Send a PUT request to update the job
    response = client.put(
        f"/jobs/{test_job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Validate the response
    assert response.status_code == status.HTTP_204_NO_CONTENT, \
        f"Expected 204, but got {response.status_code}"


def test_update_job_user_not_found(test_job):
    """
    Test updating a job when the user does not exist.

    This test ensures that if a user who is not found in the database
    attempts to update a job, the API returns a 404 Not Found error.

    Args:
        test_job: A pytest fixture representing a pre-existing job.

    Assertions:
        - The response status code should be 404 (Not Found).
        - The response detail message should indicate "User not found".
    """

    # Generate an access token (this user does not exist in the DB)
    _, token = access_token()

    # Create a job payload using the job_sample utility function
    job = job_sample()

    # Send a PUT request to update the job
    response = client.put(
        f"/jobs/{test_job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Verify the response status code and error message
    assert response.status_code == status.HTTP_404_NOT_FOUND, f"Expected 404, but got {response.status_code}"
    assert response.json()["detail"] == "User not found", "Detail mismatch"


@pytest.mark.parametrize("test_user", ["USER"], indirect=True)
def test_update_job_user_not_admin(test_job, test_user):
    """
    Test updating a job as a non-admin user.

    This test verifies that if a user with a non-admin role (e.g., "USER")
    attempts to update a job, the API returns a 403 Forbidden error.

    Args:
        test_job: A pytest fixture representing a pre-existing job.
        test_user: A non-admin user fixture (set via parametrize).

    Assertions:
        - The response status code should be 403 (Forbidden).
        - The response detail message should indicate lack of permission.
    """

    # Generate an access token for the non-admin user
    _, token = access_token()

    # Create a job payload using the job_sample utility function
    job = job_sample()

    # Send a PUT request to update the job
    response = client.put(
        f"/jobs/{test_job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Verify the response status code and error message
    assert response.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403, but got {response.status_code}"
    assert response.json()[
               "detail"] == "You do not have permission to perform this action", "Detail mismatch"


def test_update_job_not_found(test_user):
    """
    Test updating a non-existent job.

    This test ensures that attempting to update a job with an ID that does not exist
    in the database results in a 404 Not Found response.

    Args:
        test_user: A pytest fixture representing a valid authenticated user.

    Assertions:
        - The response status code should be 404 (Not Found).
        - The response detail message should indicate that the job was not found.
    """

    # Generate an access token for the authenticated user
    _, token = access_token()

    # Create a job payload using the job_sample utility function
    job = job_sample()

    # Attempt to update a job with ID 1, assuming it does not exist
    response = client.put(
        "/jobs/1",
        headers={"Authorization": f"Bearer {token}"},
        json=job
    )

    # Verify that the response returns a 404 Not Found error
    assert response.status_code == status.HTTP_404_NOT_FOUND, f"Expected 404, but got {response.status_code}"
    assert response.json()["detail"] == "Job not found", "Detail mismatch"


def test_delete_job(test_job, test_user):
    """
    Test deleting a job listing.

    Ensures that an authenticated ADMIN user can successfully delete a job.
    The test sends a DELETE request to the `/jobs/{job_id}` endpoint and
    verifies that the response status code is 204 (No Content).

    Args:
        test_job (Jobs): A pytest fixture providing a pre-existing job object.
        test_user (Users): A pytest fixture providing a pre-existing admin user.

    Assertions:
        - The response status should be 204 (No Content).
        - The job should be removed from the database.
    """

    # Generate an access token for the test user
    _, token = access_token()

    # Send DELETE request to remove the job
    response = client.delete(
        f"/jobs/{test_job.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify the response status code is 204 No Content
    assert response.status_code == status.HTTP_204_NO_CONTENT, \
        f"Expected 204, but got {response.status_code}"

    # Verify the job has been removed from the database
    db = TestSessionLocal()
    deleted_job = db.query(Jobs).filter(Jobs.id == test_job.id).first()
    assert deleted_job is None, "Job was not successfully deleted"
    db.close()


def test_delete_job_user_not_found(test_job):
    """
    Test deleting a job when the user does not exist.

    This test ensures that if a user who is not present in the database
    attempts to delete a job, the API returns a 404 (Not Found) error.

    Args:
        test_job (Jobs): A pytest fixture providing a pre-existing job object.

    Assertions:
        - The response status should be 404 (Not Found).
        - The error message should indicate that the user was not found.
    """

    # Generate an access token for a non-existent user
    _, token = access_token()

    # Send DELETE request to attempt job deletion
    response = client.delete(
        f"/jobs/{test_job.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify response status is 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected 404, but got {response.status_code}"

    # Verify response detail message
    assert response.json()["detail"] == "User not found", "Detail mismatch"


@pytest.mark.parametrize("test_user", ["USER"], indirect=True)
def test_delete_job_user_not_admin(test_job, test_user):
    """
    Test deleting a job when the user is not an admin.

    This test ensures that if a regular user (non-admin) attempts to delete
    a job, the API returns a 403 (Forbidden) error.

    Args:
        test_job (Jobs): A pytest fixture providing a pre-existing job object.
        test_user (Users): A pytest fixture providing a non-admin user object.

    Assertions:
        - The response status should be 403 (Forbidden).
        - The error message should indicate that the user lacks permission.
    """

    # Generate an access token for a non-admin user
    _, token = access_token()

    # Send DELETE request to attempt job deletion
    response = client.delete(
        f"/jobs/{test_job.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify response status is 403 Forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN, \
        f"Expected 403, but got {response.status_code}"

    # Verify response detail message
    assert response.json()["detail"] == "You do not have permission to delete jobs", \
        "Detail mismatch"


def test_delete_job_not_found(test_user):
    """
    Test deleting a job that does not exist.

    This test ensures that attempting to delete a non-existent job returns
    a 404 (Not Found) response.

    Args:
        test_user (Users): A pytest fixture providing a pre-existing user object.

    Assertions:
        - The response status should be 404 (Not Found).
        - The error message should indicate that the job was not found.
    """

    # Generate an access token for the test user
    _, token = access_token()

    # Send DELETE request for a non-existent job ID (assuming ID 1 does not exist)
    response = client.delete(
        "/jobs/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify response status is 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Expected 404, but got {response.status_code}"

    # Verify response detail message
    assert response.json()["detail"] == "Job not found", "Detail mismatch"
