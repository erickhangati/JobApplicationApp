import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from database import Base, get_db
from main import app
from models import Users, Jobs, AppliedJobs
from routers.auth import bcrypt_context, get_current_user

load_dotenv()

TEST_DB_URL = os.getenv("TEST_DB_URL")

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False},
                       poolclass=StaticPool)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {
        "id": 1,
        "username": "test_user",
        "role": "ADMIN"
    }


# @pytest.fixture
# def test_user():
#     user = Users(
#         first_name="Jane",
#         last_name="Doe",
#         email="janedoe@mail.com",
#         username="jane_doe",
#         hashed_password=bcrypt_context.hash("test1234"),
#         role="ADMIN"
#     )
#
#     db = TestSessionLocal()
#     db.add(user)
#     db.commit()
#
#     try:
#         yield user
#     finally:
#         with engine.connect() as connection:
#             connection.execute(text('DELETE FROM users'))
#             connection.commit()
#             db.close()

@pytest.fixture
def test_user(request):
    """
    Fixture to create a test user dynamically with a specified role.

    Args:
        request: A pytest request object to allow parameterization.

    Returns:
        Users: A user object for testing.
    """

    # Default to "USER" if no role is specified in the test function
    role = getattr(request, "param", "ADMIN")

    # Create a test user
    user = Users(
        first_name="Jane",
        last_name="Doe",
        email="janedoe@mail.com",
        username="jane_doe",
        hashed_password=bcrypt_context.hash("test1234"),
        role=role
    )

    db = TestSessionLocal()
    db.add(user)
    db.commit()

    try:
        yield user  # Provide user object for the test
    finally:
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM users'))  # Cleanup after test
            connection.commit()
            db.close()


@pytest.fixture
def test_job():
    job = Jobs(
        title="Test Job",
        description="Test job description",
        company="Test Company",
        location="Test Location",
        min_salary=10000,
        max_salary=50000,
        med_salary=25000,
        pay_period="Hourly",
        views=100,
        listed_time=datetime.now(timezone.utc),
        expiry=datetime.now(timezone.utc),
        remote_allowed=True,
        application_type="ComplexOnsiteApply",
        experience_level="Mid-Senior level",
        skills_desc="No Skills Description",
        sponsored=False,
        work_type="Full-time",
        currency="USD"
    )

    db = TestSessionLocal()
    db.add(job)
    db.commit()

    try:
        yield job
    finally:
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM jobs'))
            connection.commit()
            db.close()


@pytest.fixture
def test_applied_job():
    applied_job = AppliedJobs(
        user_id=2,
        job_id=1,
        applied_at=datetime.now(timezone.utc),
        application_status="Pending"
    )

    db = TestSessionLocal()
    db.add(applied_job)
    db.commit()

    try:
        yield applied_job
    finally:
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM applied_jobs'))
            connection.commit()
            db.close()


@pytest.fixture
def test_user_applied_job():
    applied_job = AppliedJobs(
        user_id=1,
        job_id=1,
        applied_at=datetime.now(timezone.utc),
        application_status="Pending"
    )

    db = TestSessionLocal()
    db.add(applied_job)
    db.commit()

    try:
        yield applied_job
    finally:
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM applied_jobs'))
            connection.commit()
            db.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)
