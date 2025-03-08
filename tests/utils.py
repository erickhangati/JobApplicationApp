from datetime import timedelta

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
