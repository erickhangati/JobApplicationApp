from typing import List, Optional

from fastapi import APIRouter, Query
from starlette import status

from database import db_dependency
from models import Jobs, JobResponse
from utils import create_response

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=List[JobResponse], status_code=status.HTTP_200_OK)
async def read_jobs(
        db: db_dependency,
        title: Optional[str] = Query(None, min_length=3,
                                     description="Filter jobs by title"),
        company: Optional[str] = Query(None, min_length=3,
                                       description="Filter jobs by company"),
        location: Optional[str] = Query(None, min_length=3,
                                        description="Filter jobs by location"),
        min_salary: Optional[int] = Query(None, description="Minimum salary filter"),
        max_salary: Optional[int] = Query(None, description="Maximum salary filter"),
        remote_allowed: Optional[bool] = Query(
            None,
            description="Filter remote jobs (true/false)"),
        page: int = Query(1, ge=1, description="Page number (starts at 1)"),
        page_size: int = Query(10, ge=1, le=100,
                               description="Number of jobs per page (max: 100)")
):
    """
    Retrieves a paginated list of job listings based on filters.

    Args:
        db (Session): Database session dependency.
        title (Optional[str]): Filter jobs by title (case-insensitive).
        company (Optional[str]): Filter jobs by company.
        location (Optional[str]): Filter jobs by job location.
        min_salary (Optional[int]): Minimum salary filter.
        max_salary (Optional[int]): Maximum salary filter.
        remote_allowed (Optional[bool]): Boolean filter for remote jobs.
        page (int, optional): The page number (defaults to 1).
        page_size (int, optional): The number of jobs per page (defaults to 10, max 100).

    Returns:
        dict: A paginated response with job listings and metadata.
    """

    # Base query
    query = db.query(Jobs)

    # Apply filters
    if title:
        query = query.filter(Jobs.title.ilike(f"%{title}%"))  # Case-insensitive search
    if company:
        query = query.filter(Jobs.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(Jobs.location.ilike(f"%{location}%"))
    if min_salary is not None:
        query = query.filter(Jobs.min_salary >= min_salary)
    if max_salary is not None:
        query = query.filter(Jobs.max_salary <= max_salary)
    if remote_allowed is not None:
        query = query.filter(Jobs.remote_allowed == remote_allowed)

    # Count total jobs after applying filters
    filtered_jobs_count = query.count()

    # Calculate offset for pagination
    offset = (page - 1) * page_size

    # Fetch jobs with pagination
    jobs = query.limit(page_size).offset(offset).all()

    # Count total jobs in the database
    total_jobs = db.query(Jobs).count()
    total_pages = (filtered_jobs_count + page_size - 1) // page_size  # Ceiling division

    # Convert job objects into JSON-serializable format
    response_data = {
        "page": page,
        "page_size": page_size,
        "total_jobs": total_jobs,  # Total jobs in DB
        "filtered_jobs_count": filtered_jobs_count,  # Jobs that match search filters
        "total_pages": total_pages,  # Total pages after filtering
        "jobs": [JobResponse.model_validate(job).model_dump(mode="json") for job in jobs]
    }

    # Return standardized JSON response
    return create_response(
        message="Jobs retrieved successfully",
        data=response_data,
        status_code=status.HTTP_200_OK
    )
