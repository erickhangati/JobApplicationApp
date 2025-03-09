from fastapi import APIRouter, HTTPException
from starlette import status

from database import db_dependency
from models import UserRequestBase, Users, ChangePasswordRequest
from routers.auth import user_dependency, bcrypt_context
from utils import create_response

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=UserRequestBase, status_code=status.HTTP_200_OK)
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


@router.put("/profile/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
        db: db_dependency,
        request: user_dependency,
        password_update: ChangePasswordRequest):
    """
    Updates the authenticated user's password.

    Args:
        db (Session): Database session dependency.
        request (dict): Dictionary containing authenticated user details from JWT token.
        password_update (ChangePasswordRequest): Pydantic model containing old and new password details.

    Returns:
        HTTP 204 No Content: If the password change is successful.

    Raises:
        HTTPException 404: If the user is not found.
        HTTPException 400: If the old password is incorrect or new passwords do not match.
    """

    # Retrieve the user from the database using the ID from the JWT token
    user = db.query(Users).filter(Users.id == request.get("id")).first()

    # Raise an error if the user is not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify if the provided old password is correct
    if not bcrypt_context.verify(password_update.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong old password"
        )

    # Ensure the new passwords match
    if password_update.new_password != password_update.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # Hash the new password and update the user's record
    user.hashed_password = bcrypt_context.hash(password_update.new_password)

    # Commit the changes to the database
    db.commit()
    db.refresh(user)  # Refresh user object after update


@router.put("/profile", status_code=status.HTTP_204_NO_CONTENT)
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
