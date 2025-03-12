from datetime import timedelta, datetime, timezone

from routers.auth import create_access_token, bcrypt_context


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
    now = datetime.now(timezone.utc)
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
        "listed_time": now.isoformat(),
        "expiry": (now + timedelta(days=30)).isoformat(),
        "remote_allowed": True,
        "application_type": "ComplexOnsiteApply",
        "experience_level": "Mid-Senior level",
        "skills_desc": "No Skills Description",
        "sponsored": False,
        "work_type": "Full-time",
        "currency": "USD"
    }


def access_token(user_id: int = 1):
    payload = {
        "username": "jane_doe",
        "id": user_id,
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
