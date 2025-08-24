"""
Custom exceptions for Beacon Commercial Register API
"""
from typing import Optional


class BeaconError(Exception):
    """Base exception for the application"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class ValidationError(BeaconError):
    """Data validation failed"""
    pass


class CompanyNotFound(BeaconError):
    """Company not found in database or external registry"""
    def __init__(self, uid: str):
        super().__init__(f"Company with UID {uid} not found", "COMPANY_NOT_FOUND")
        self.uid = uid


class DuplicateCompanyError(BeaconError):
    """Company already exists with same name and legal form"""
    def __init__(self, name: str, legal_form: str):
        super().__init__(
            f"Company '{name}' already exists with legal form '{legal_form}'",
            "DUPLICATE_COMPANY"
        )
        self.name = name
        self.legal_form = legal_form


class ExternalServiceError(BeaconError):
    """External service (registry API) is unavailable"""
    def __init__(self, service: str, details: Optional[str] = None):
        message = f"External service '{service}' is temporarily unavailable"
        if details:
            message += f": {details}"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service = service


class DatabaseError(BeaconError):
    """Database operation failed"""
    def __init__(self, operation: str, details: Optional[str] = None):
        message = f"Database operation '{operation}' failed"
        if details:
            message += f": {details}"
        super().__init__(message, "DATABASE_ERROR")
        self.operation = operation


class AuthenticationError(BeaconError):
    """Authentication failed"""
    def __init__(self, details: Optional[str] = None):
        message = "Authentication failed"
        if details:
            message += f": {details}"
        super().__init__(message, "AUTHENTICATION_ERROR")


class RateLimitError(BeaconError):
    """Rate limit exceeded"""
    def __init__(self, limit: str):
        super().__init__(f"Rate limit exceeded: {limit}", "RATE_LIMIT_EXCEEDED")
        self.limit = limit


class ServiceUnavailableError(BeaconError):
    """Service is temporarily unavailable"""
    def __init__(self, reason: Optional[str] = None):
        message = "Service temporarily unavailable"
        if reason:
            message += f": {reason}"
        super().__init__(message, "SERVICE_UNAVAILABLE")


class BadRequestError(BeaconError):
    """Bad request - client error"""
    def __init__(self, details: str):
        super().__init__(details, "BAD_REQUEST")


class InternalServerError(BeaconError):
    """Internal server error"""
    def __init__(self, details: Optional[str] = None):
        message = "Internal server error"
        if details:
            message += f": {details}"
        super().__init__(message, "INTERNAL_SERVER_ERROR")
