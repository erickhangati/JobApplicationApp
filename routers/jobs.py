from typing import List

from fastapi import APIRouter, Query
from starlette import status

from database import db_dependency
from models import Jobs, JobRequest, JobResponse
from utils import create_response

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobResponse], status_code=status.HTTP_200_OK)
async def read_jobs(
        db: db_dependency,
        page: int = Query(1, ge=1, description="Page number (starts at 1)"),
        page_size: int = Query(10, ge=1, le=100,
                               description="Number of jobs per page (max: 100)")
):
    """
    Retrieves a paginated list of job listings.

    Args:
        db (Session): Database session dependency.
        page (int, optional): The page number (defaults to 1).
        page_size (int, optional): The number of jobs per page (defaults to 10, max 100).

    Returns:
        dict: A paginated response with job listings and metadata.
    """

    # Calculate offset
    offset = (page - 1) * page_size

    # Fetch jobs with pagination
    jobs = db.query(Jobs).limit(page_size).offset(offset).all()

    # Count total jobs
    total_jobs = db.query(Jobs).count()
    total_pages = (total_jobs + page_size - 1) // page_size  # Ceiling division

    # Construct paginated response data
    response_data = {
        "page": page,  # Current page number
        "page_size": page_size,  # Number of jobs per page
        "total_jobs": total_jobs,  # Total number of job listings in the database
        "total_pages": total_pages,  # Total pages available based on page size
        "jobs": [JobResponse.model_validate(job).model_dump(mode="json") for job in jobs]
        # Convert job objects into JSON-serializable format (including datetime fields)
    }

    # Return standardized JSON response using utility function
    return create_response(
        message="Jobs retrieved successfully",  # Success message
        data=response_data,  # Paginated job listings
        status_code=status.HTTP_200_OK  # HTTP 200 OK response
    )
