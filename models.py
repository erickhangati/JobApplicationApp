"""
models.py - Defines SQLAlchemy models and Pydantic schemas for a job application system.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLAlchemyEnum
)

from database import Base


# ==========================
# ENUMS
# ==========================

class UserRole(str, Enum):
    """Defines user roles in the system."""
    USER = "USER"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"


# ==========================
# DATABASE MODELS
# ==========================

class Jobs(Base):
    """Represents job postings in the system."""

    __tablename__ = 'jobs'
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Column(Integer, primary_key=True)
    title: str = Column(String, nullable=False)  # Job title
    description: str = Column(String, nullable=False)  # Job description
    company: str = Column(String, nullable=True)  # Company name
    location: str = Column(String, nullable=False)  # Job location
    min_salary: int = Column(Integer, nullable=False)  # Minimum salary
    max_salary: int = Column(Integer, nullable=True)  # Maximum salary
    med_salary: int = Column(Integer, nullable=True)  # Median salary
    pay_period: str = Column(String,
                             nullable=True)  # Payment frequency (e.g., Hourly, Monthly)
    views: int = Column(Integer, nullable=False, default=0)  # Number of job views
    listed_time: datetime = Column(DateTime, nullable=True, default=lambda: datetime.now(
        timezone.utc))  # Listing date
    expiry: datetime = Column(DateTime, nullable=True)  # Job expiry date
    remote_allowed: bool = Column(Boolean, nullable=True)  # Remote work eligibility
    application_type: str = Column(String, nullable=True)  # Type of application process
    experience_level: str = Column(String, nullable=True)  # Required experience level
    skills_desc: str = Column(String, nullable=False)  # Skills required
    sponsored: bool = Column(Boolean,
                             nullable=True)  # Whether the job is a sponsored listing
    work_type: str = Column(String,
                            nullable=True)  # Type of employment (Full-time, Part-time, etc.)
    currency: str = Column(String, nullable=True)  # Currency of salary payment

    # Relationship with applications
    applicants = relationship("AppliedJobs", back_populates="job",
                              cascade="all, delete-orphan")


class Users(Base):
    """Represents registered users in the system."""

    __tablename__ = 'users'

    id: Optional[int] = Column(Integer, primary_key=True)
    first_name: str = Column(String, nullable=False)  # First name of the user
    last_name: str = Column(String, nullable=False)  # Last name of the user
    username: str = Column(String, unique=True, nullable=False)  # Unique username
    email: str = Column(String, unique=True, nullable=False)  # Unique email address
    hashed_password: str = Column(String,
                                  nullable=False)  # Hashed password for authentication
    role: UserRole = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER,
                            nullable=False)  # User role

    # Relationship with job applications
    applied_jobs = relationship("AppliedJobs", back_populates="user",
                                cascade="all, delete-orphan")


class AppliedJobs(Base):
    """Represents job applications submitted by users."""

    __tablename__ = 'applied_jobs'

    id: Optional[int] = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"),
                          nullable=False)  # Applicant user ID
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False,
                    index=True)  # Job ID
    applied_at = Column(DateTime, nullable=False, default=lambda: datetime.now(
        timezone.utc))  # Application timestamp
    application_status = Column(String, nullable=False,
                                default="Pending")  # Status of the application

    # Relationships
    user = relationship("Users", back_populates="applied_jobs")
    job = relationship("Jobs", back_populates="applicants")


# ==========================
# Pydantic REQUEST MODELS
# ==========================

class JobRequest(BaseModel):
    """Schema for job creation requests."""

    title: str = Field(min_length=3, description='Job title')
    description: str = Field(min_length=3, description='Job description')
    company: str = Field(min_length=3, description='Company name')
    location: str = Field(min_length=3, description='Location')
    min_salary: int = Field(gt=0, description='Minimum salary')
    max_salary: int = Field(gt=0, description='Maximum salary')
    med_salary: int = Field(gt=0, description='Median salary')
    pay_period: str = Field(min_length=3, description='Payment period')
    views: int = Field(gt=0, description='Views')
    listed_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                  description='Listed date')
    expiry: datetime = Field(description='Expiry date')
    remote_allowed: bool = Field(description='Remote allowed')
    application_type: str = Field(min_length=3, description='Application type')
    experience_level: str = Field(min_length=3, description='Experience level')
    skills_desc: str = Field(min_length=3, description='Skills description')
    sponsored: bool = Field(description='Sponsored')
    work_type: str = Field(min_length=3, description='Work type')
    currency: str = Field(min_length=3, description='Currency')

    model_config = {
        "json_schema_extra": {
            "example": {
                'title': 'Software Engineer',
                'description': 'Develop and maintain software applications.',
                'company': 'TechCorp',
                'location': 'Remote',
                'min_salary': 50000,
                'max_salary': 120000,
                'med_salary': 80000,
                'pay_period': 'Monthly',
                'views': 0,
                'listed_time': datetime.now(timezone.utc),
                'expiry': datetime.now(timezone.utc),
                'remote_allowed': True,
                'application_type': 'Online',
                'experience_level': 'Mid-Level',
                'skills_desc': 'Python, FastAPI, SQLAlchemy',
                'sponsored': False,
                'work_type': 'FULL_TIME',
                'currency': 'USD',
            }
        }
    }


class UserRequestBase(BaseModel):
    """Base schema for user-related requests."""

    first_name: str = Field(min_length=3, description='First name')
    last_name: str = Field(min_length=3, description='Last name')
    username: str = Field(min_length=3, description='Username')
    email: str = Field(min_length=3, description='Email')
    role: str = Field(min_length=3, description='Role')


class UserRequest(UserRequestBase):
    """Schema for user registration requests."""

    password: str = Field(min_length=3, description='Password')

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "Alice",
                "last_name": "Smith",
                "username": "alicesmith",
                "email": "alice@example.com",
                "password": "test1234",
                "role": "USER"
            }
        }
    }


class AppliedJobsRequest(BaseModel):
    """Schema for applying to a job."""

    user_id: int = Field(gt=0, description="ID of the user applying")
    job_id: int = Field(gt=0, description="ID of the job being applied for")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "job_id": 10
            }
        }
    }
