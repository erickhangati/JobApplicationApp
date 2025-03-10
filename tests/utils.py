from datetime import timedelta, datetime, timezone

import pytest

from main import app
from routers.auth import create_access_token, bcrypt_context, user_dependency


def user_sample():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@mail.com",
        "username": "john_doe",
        "password": bcrypt_context.hash("test1234"),
        "role": "USER"
    }


def job_sample():
    return {
        "title": "Test Job",
        "description": "Test job description",
        "company": "Test Company",
        "location": "Test Location",
        "min_salary": 10000,
        "max_salary": 50000,
        "med_salary": 25000,
        "pay_period": "Hourly",
        "views": 100,
        "listed_time": datetime.now(timezone.utc),
        "expiry": datetime.now(timezone.utc),
        "remote_allowed": True,
        "application_type": "ComplexOnsiteApply",
        "experience_level": "Mid-Senior level",
        "skills_desc": "No Skills Description",
        "sponsored": False,
        "work_type": "Full-time",
        "currency": "USD"
    }


def access_token():
    payload = {
        "username": "jane_doe",
        "id": 1,
        "role": "ADMIN",
        "expire": timedelta(hours=1),  # Expiration time (1 hour)
    }

    # Generate an access token
    token = create_access_token(
        user_id=payload["id"],
        username=payload["username"],
        user_role=payload["role"],
        expire=payload["expire"]
    )

    return payload, token


@pytest.fixture
def override_invalid_user():
    """Fixture to override user_dependency with an invalid user."""
    app.dependency_overrides[user_dependency] = lambda: {}  # Return empty user

    yield  # This ensures the override is only active for the test

    app.dependency_overrides.pop(user_dependency, None)  # Restore original dependency
