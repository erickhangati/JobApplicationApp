from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Query, Path, HTTPException
from starlette import status

from database import db_dependency
from models import Jobs, JobResponse, Users, AppliedJobResponse, AppliedJobs, JobRequest
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


@router.get("/jobs/applied", response_model=List[JobResponse],
            status_code=status.HTTP_200_OK)
async def read_applied_jobs(
        db: db_dependency,
        user: user_dependency,
        page: int = Query(1, ge=1, description="Page number (starts at 1)"),
        page_size: int = Query(10, ge=1, le=100,
                               description="Number of jobs per page (max: 100)")):
    user = db.query(Users).filter(Users.id == user.get('id')).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    offset = (page - 1) * page_size
    applied_jobs = db.query(AppliedJobs).filter(AppliedJobs.user_id == user.id).limit(
        page_size).offset(offset).all()

    applied_jobs_total = len(applied_jobs)
    total_pages = (applied_jobs_total + page_size - 1) // page_size

    response_data = {
        "page": page,
        "page_size": page_size,
        "applied_jobs_count": applied_jobs_total,  # Jobs that match search filters
        "total_pages": total_pages,  # Total pages after filtering
        "jobs": [AppliedJobResponse.model_validate(job).model_dump(mode="json") for job in
                 applied_jobs]
    }

    # Return standardized JSON response
    return create_response(
        message="Applied Jobs retrieved successfully" if applied_jobs_total > 0 else
        "No applied jobs found",
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


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
        db: db_dependency,
        user_request: user_dependency,
        job_request: JobRequest
):
    """
    Creates a new job posting.

    Args:
        db (Session): Database session dependency.
        user_request (dict): Dictionary containing authenticated user details from JWT token.
        job_request (JobRequest): Pydantic model containing job details.

    Returns:
        JSONResponse: Standardized response with job details and success message.

    Raises:
        HTTPException:
            - 404 NOT FOUND: If the authenticated user is not found.
            - 403 FORBIDDEN: If the user does not have admin privileges.
    """

    # Retrieve the user from the database
    user = db.query(Users).filter(Users.id == user_request.get("id")).first()

    # Check if the user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if the user has admin privileges
    if user.role != 'ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    # Create a new job instance using the validated request data
    job = Jobs(**job_request.model_dump())

    # Add and commit the job to the database
    db.add(job)
    db.commit()
    db.refresh(job)

    # Convert the SQLAlchemy object to a Pydantic model for response
    job_data = JobResponse.model_validate(job)

    # Return standardized JSON response
    return create_response(
        message="Job created successfully",
        data=job_data.model_dump(mode="json"),
        location=f"/jobs/{job.id}",
        status_code=status.HTTP_201_CREATED
    )


@router.put("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_job(
        db: db_dependency,
        user_request: user_dependency,
        job_request: JobRequest,
        job_id: int = Path(gt=0, description="Job ID (must be greater than 0)")
):
    """
    Updates an existing job listing.

    This route allows an admin user to update the details of an existing job listing.

    Args:
        db (Session): Database session dependency.
        user_request (dict): User details from JWT token.
        job_request (JobRequest): The updated job details.
        job_id (int): The ID of the job to be updated.

    Returns:
        None: Returns a 204 No Content response upon successful update.

    Raises:
        HTTPException: If the user is not found (404).
        HTTPException: If the user is not an admin (403).
        HTTPException: If the job is not found (404).
    """

    # Fetch the user making the request
    user = db.query(Users).filter(Users.id == user_request.get("id")).first()

    # Validate user existence
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Ensure the user has admin privileges
    if user.role != 'ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    # Fetch the job to be updated
    job = db.query(Jobs).filter(Jobs.id == job_id).first()

    # Validate job existence
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Update job fields dynamically
    job_data = job_request.model_dump()
    for key, value in job_data.items():
        setattr(job, key, value)

    # Commit changes to the database
    db.commit()
    db.refresh(job)
