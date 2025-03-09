"""
main.py - Entry point for the FastAPI application.

This file initializes the FastAPI app and includes various routers 
for handling authentication, admin operations, job postings, and user management.
"""

from fastapi import FastAPI

# Importing routers for different modules
from routers import auth, admin, jobs, users, profile

# Initialize FastAPI application
app = FastAPI(
    title="Job Application API",
    description="An API for managing job postings and applications.",
    version="1.0.0"
)

# Include routers for modularized functionality
app.include_router(auth.router)  # Authentication routes
app.include_router(admin.router)  # Admin-related routes
app.include_router(jobs.router)  # Job management routes
app.include_router(users.router)  # User management routes
app.include_router(profile.router)  # Profile management routes
