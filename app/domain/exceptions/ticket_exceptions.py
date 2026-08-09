from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class TicketNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.TICKET_NOT_FOUND, status_code=404, detail=detail
        )


class TicketClosedException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.TICKET_CLOSED, status_code=409, detail=detail
        )


class TicketAccessDeniedException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.TICKET_ACCESS_DENIED, status_code=403, detail=detail
        )
