import os
from datetime import timedelta, datetime, timezone
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from starlette import status

from database import db_dependency
from models import Token, Users

SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
token_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]

router = APIRouter(prefix="/auth", tags=["auth"])


def create_access_token(user_id: int, username: str, user_role: str,
                        expire: timedelta) -> str:
    """
    Generates a JWT access token for authentication.

    Args:
        user_id (int): The unique identifier of the user.
        username (str): The username of the authenticated user.
        user_role (str): The role of the user (e.g., "USER", "ADMIN").
        expire (timedelta): The duration before the token expires.

    Returns:
        str: Encoded JWT access token.

    Example:
        >>> create_access_token(1, "johndoe", "USER", timedelta(hours=1))
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    Notes:
        - The token includes an expiration (`exp`) claim to prevent indefinite use.
        - Ensure `SECRET_KEY` is stored securely (e.g., environment variables).
    """

    # Set expiration time (UTC)
    expiration_time = datetime.now(timezone.utc) + expire

    # JWT payload with user info and expiration
    payload: Dict[str, str | int | datetime] = {
        "id": user_id,
        "sub": username,  # Subject (usually the username)
        "role": user_role,  # User role (for authorization)
        "exp": expiration_time  # Expiration timestamp
    }

    # Encode the token with the secret key and specified algorithm
    token: str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


@router.post("/login", response_model=Token, status_code=status.HTTP_201_CREATED)
async def create_token(db: db_dependency, user_request: token_dependency):
    """
    Authenticates a user and generates an access token.

    Args:
        db (Session): Database session dependency.
        user_request (UserLoginRequest): Pydantic model with username and password.

    Returns:
        dict: JSON response containing the access token and token type.

    Raises:
        HTTPException: If the user is not found or the password is incorrect.

    Example:
        Request:
            {
                "username": "johndoe",
                "password": "test1234"
            }

        Response:
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
    """

    # Fetch the user by username
    user = db.query(Users).filter(Users.username == user_request.username).first()

    # Check if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    # Verify password using bcrypt
    if not bcrypt_context.verify(user_request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect password")

    # Generate JWT access token with a 60-minute expiration
    token = create_access_token(user_id=user.id, username=user.username,
                                user_role=user.role, expire=timedelta(minutes=60))

    # Return access token
    return {"access_token": token, "token_type": "bearer"}
