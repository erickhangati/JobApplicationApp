"""
users.py - Handles user registration and related operations in the FastAPI application.
"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Path
from starlette import status

from .auth import bcrypt_context, user_dependency
from models import UserRequest, Users, UserRequestBase, UserResponse
from database import db_dependency
from utils import create_response

# Create a router for user-related endpoints
router = APIRouter(tags=["users"])


@router.get("/users", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def read_users(
        db: db_dependency,
        user_request: user_dependency,
        first_name: Optional[str] = Query(None, min_length=3,
                                          description="Filter users by first name"),
        last_name: Optional[str] = Query(None, min_length=3,
                                         description="Filter users by last name"),
        page: int = Query(1, ge=1, description="Page number (starts at 1)"),
        page_size: int = Query(10, ge=1, le=100,
                               description="Number of users per page (max: 100)")
):
    """
    Retrieves a paginated list of users with optional filtering.

    This endpoint allows an admin user to retrieve users based on filters like first name and last name.
    Supports pagination for efficient data retrieval.

    Args:
        db (Session): Database session dependency.
        user_request (dict): The authenticated user's details.
        first_name (Optional[str]): Filter users by first name (case-insensitive).
        last_name (Optional[str]): Filter users by last name (case-insensitive).
        page (int): The page number for pagination (default is 1).
        page_size (int): The number of users per page (default is 10, max is 100).

    Returns:
        JSONResponse: A paginated response containing user details and metadata.

    Raises:
        HTTPException: If the requesting user is not found (404) or does not have admin privileges (403).
    """

    # Fetch the requesting user from the database
    requesting_user = db.query(Users).filter(Users.id == user_request.get('id')).first()

    # Validate user existence
    if not requesting_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Ensure only admins can retrieve users
    if requesting_user.role != 'ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    # Initialize query
    query = db.query(Users)

    # Apply filtering
    if first_name:
        query = query.filter(Users.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Users.last_name.ilike(f"%{last_name}%"))

    # Count total filtered users
    filtered_user_count = query.count()

    # Calculate pagination offset
    offset = (page - 1) * page_size

    # Fetch paginated users
    users = query.limit(page_size).offset(offset).all()

    # Count total users in the system
    total_users = db.query(Users).count()
    total_pages = (filtered_user_count + page_size - 1) // page_size  # Ceiling division

    # Prepare response data
    response_data = {
        "page": page,
        "page_size": page_size,
        "total_users": total_users,  # Total users in the system
        "filtered_user_count": filtered_user_count,  # Users matching filters
        "total_pages": total_pages,  # Number of pages based on filtered results
        "users": [UserResponse.model_validate(user).model_dump(mode="json") for user in
                  users]
    }

    # Return standardized JSON response
    return create_response(
        message="Users retrieved successfully",
        data=response_data,
        status_code=status.HTTP_200_OK
    )


@router.post(
    "/users",
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


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        db: db_dependency,
        user_request: user_dependency,
        user_id: int = Path(gt=0, description="User ID (must be greater than 0)")
):
    """
    Deletes a user from the database.

    Only an **ADMIN** can delete users, and a user **cannot delete themselves**.

    Args:
        db (Session): Database session dependency.
        user_request (dict): The authenticated user's data extracted from JWT.
        user_id (int): The ID of the user to be deleted.

    Raises:
        HTTPException (404): If the user does not exist.
        HTTPException (403): If the requester is not an admin or tries to delete
        another user.

    Returns:
        None: Successfully deletes the user and returns a 204 No Content response.
    """

    # Retrieve the user to be deleted from the database
    user = db.query(Users).filter(Users.id == user_id).first()

    # If the user does not exist, raise a 404 Not Found error
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Ensure the requester is an admin or is a user not trying to delete another user
    if user_request.get("role") != "ADMIN" or user_request.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    # Delete the user and commit the transaction
    db.delete(user)
    db.commit()

