"""
users.py - Handles user registration and related operations in the FastAPI application.
"""

from fastapi import APIRouter, HTTPException
from starlette import status

from .auth import bcrypt_context  # Import password hashing context
from models import UserRequest, Users, UserRequestBase  # Import models
from database import db_dependency  # Import database dependency
from utils import create_response  # Import response utility function

# Create a router for user-related endpoints
router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    response_model=UserRequestBase,
    status_code=status.HTTP_201_CREATED
)
async def create_user(db: db_dependency, request: UserRequest):
    """
    Registers a new user in the system.

    - Checks if the email or username is already registered.
    - Hashes the user's password before storing it.
    - Returns a success message with user details (excluding password).

    Args:
        db (Session): SQLAlchemy database session.
        request (UserRequest): Pydantic model containing user registration details.

    Returns:
        JSONResponse: Success message and registered user data.
    """

    # Check if the user already exists by email or username
    existing_user = db.query(Users).filter(
        (Users.email == request.email) | (Users.username == request.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered."
        )

    # Create a new user instance
    user = Users(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        username=request.username,
        hashed_password=bcrypt_context.hash(request.password),  # Hash password
        role=request.role,
    )

    # Add the user to the database
    db.add(user)
    db.commit()
    db.refresh(user)

    # Prepare response data (excluding password for security)
    user_data = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }

    # Return structured response using utility function
    return create_response(
        message="User successfully registered.",
        data=user_data,
        status_code=status.HTTP_201_CREATED,
        location=f"/users/{user.id}"
    )