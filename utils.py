from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

from starlette import status


def create_response(
        message: str,
        data: Optional[Any] = None,
        status_code: int = status.HTTP_200_OK,
        location: Optional[str] = None
) -> JSONResponse:
    """
    Constructs a standardized JSON response for API endpoints.

    Args:
        message (str): A brief message describing the response.
        data (Optional[Any]): The response data (default is None).
        status_code (int): The HTTP status code (default is 200).
        location (Optional[str]): A URL to be included in the 'Location' header
        (default is None).

    Returns:
        JSONResponse: A FastAPI JSON response with the provided message, data,
        and headers.
    """
    headers: Dict[str, str] = {}

    if location:
        headers["Location"] = location  # Add 'Location' header if provided

    return JSONResponse(
        content={"message": message, "data": data},
        status_code=status_code,
        headers=headers
    )
