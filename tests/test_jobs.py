import pytest
from starlette import status

from .conftest import (test_job, test_user, test_applied_job, test_user_applied_job,
                       client)
from .utils import access_token


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


# def test_read_job(test_job):
#     response = client.get("/jobs/1")
#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["message"] == "Job retrieved successfully"
#     assert response.json()["data"]["title"] == "Test Job"


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
    _, token = access_token()

    response = client.get("/jobs/applied", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND, f"Expected 404 OK, but got {response.status_code}"
    assert response.json()["detail"] == "User not found", "Detail mismatch"
