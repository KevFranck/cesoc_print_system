from __future__ import annotations

from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail)


class ValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)
