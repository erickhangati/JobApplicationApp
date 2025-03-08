"""
users.py - Handles user registration and related operations in the FastAPI application.
"""

from fastapi import APIRouter, HTTPException
from starlette import status

from .auth import bcrypt_context, user_dependency  # Import password hashing context
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

    Raises:
        HTTPException: If the user exists.
    """

    # Check if the user already exists by email or username
    existing_user = db.query(Users).filter(
        (Users.email == request.email) | (Users.username == request.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
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
        message="User successfully registered",
        data=user_data,
        status_code=status.HTTP_201_CREATED,
        location=f"/users/{user.id}"
    )


@router.get("/me", response_model=UserRequestBase, status_code=status.HTTP_200_OK)
async def read_user(db: db_dependency, request: user_dependency):
    """
    Retrieves the authenticated user's profile.

    Args:
        db (Session): Database session dependency.
        request (dict): Dictionary containing user details from JWT token.

    Returns:
        UserRequestBase: User profile data (excluding password).

    Raises:
        HTTPException: If the user is not found.

    Example:
        Request (Authenticated):
            GET /users/me

        Response:
            {
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "johndoe@email.com",
                "role": "USER"
            }
    """

    # Fetch the user from the database using the ID from the JWT token
    user = db.query(Users).filter(Users.id == request.get("id")).first()

    # Raise error if user is not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prepare structured response
    user_data = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }

    return create_response(
        message="User profile retrieved successfully",
        data=user_data,
        status_code=status.HTTP_200_OK
    )


@router.put("/me", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
        db: db_dependency,
        request: user_dependency,
        update: UserRequestBase
):
    """
    Updates the authenticated user's profile.

    Args:
        db (Session): SQLAlchemy database session dependency.
        request (dict): Dictionary containing user details from the JWT token.
        update (UserRequestBase): Pydantic model containing updated user details.

    Returns:
        None: Returns HTTP 204 No Content on success.

    Raises:
        HTTPException: If the user is not found.

    Example:
        Request:
            PUT /users/me
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "email": "janedoe@email.com",
                "role": "ADMIN"
            }

        Response:
            Status Code: 204 No Content
    """

    # Fetch the user from the database using the ID from the JWT token
    user = db.query(Users).filter(Users.id == request.get("id")).first()

    # Raise an error if the user does not exist
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update the user fields with the new values
    user.first_name = update.first_name
    user.last_name = update.last_name
    user.username = update.username
    user.email = update.email
    user.role = update.role

    # Commit changes to the database
    db.commit()
    db.refresh(user)
