from datetime import timedelta

from routers.auth import create_access_token


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
