from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Query, Path, HTTPException
from starlette import status

from database import db_dependency
from models import Jobs, JobResponse, Users, AppliedJobResponse, AppliedJobs
from routers.auth import user_dependency
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


@router.get("/jobs/{job_id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
async def read_job(
        db: db_dependency,
        job_id: int = Path(gt=0, description="Job ID (must be greater than 0)")):
    """
    Retrieves a specific job by its ID.

    Args:
        db (Session): Database session dependency.
        job_id (int): ID of the job to retrieve.

    Returns:
        JobResponse: Job details.

    Raises:
        HTTPException: If the job does not exist.
    """

    # Fetch the job from the database
    job = db.query(Jobs).filter(Jobs.id == job_id).first()

    # Handle job not found
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Convert SQLAlchemy object to Pydantic response model
    job_data = JobResponse.model_validate(job)

    # Return standardized JSON response
    return create_response(
        message="Job retrieved successfully",
        data=job_data.model_dump(mode="json"),  # Ensure JSON serialization
        status_code=status.HTTP_200_OK
    )


@router.post("/jobs/{job_id}/apply",
             response_model=AppliedJobResponse,
             status_code=status.HTTP_201_CREATED)
async def create_job_application(
        db: db_dependency,
        user_request: user_dependency,
        job_id: int = Path(gt=0, description="Job ID (must be greater than 0)")):
    """
    Allows a user to apply for a job.

    Args:
        db (Session): Database session dependency.
        user_request (dict): The authenticated user making the request.
        job_id (int): The ID of the job being applied to.

    Returns:
        JSONResponse: A standardized response containing the application details.

    Raises:
        HTTPException: If the job or user does not exist, or if the user has already applied.
    """

    # Fetch the job by ID
    job = db.query(Jobs).filter(Jobs.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Validate user ID
    user_id = user_request.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user credentials"
        )

    # Fetch the user from the database
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    # Check if the user has already applied for the job
    existing_application = db.query(AppliedJobs).filter(
        AppliedJobs.user_id == user.id,
        AppliedJobs.job_id == job.id
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied for this job"
        )

    # Create a new job application
    applied_job = AppliedJobs(
        user_id=user.id,
        job_id=job.id,
        applied_at=datetime.now(timezone.utc),
        application_status="Pending"
    )

    # Add and commit changes to the database
    db.add(applied_job)
    db.commit()
    db.refresh(applied_job)

    # Convert SQLAlchemy object to Pydantic response model
    applied_job_data = AppliedJobResponse.model_validate(applied_job,
                                                         from_attributes=True)

    # Return structured response
    return create_response(
        message="Job applied successfully",
        data=applied_job_data.model_dump(mode="json"),
        status_code=status.HTTP_201_CREATED
    )
