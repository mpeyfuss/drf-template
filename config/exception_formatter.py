from drf_standardized_errors.formatter import (
    ExceptionFormatter as BaseExceptionFormatter,
)
from drf_standardized_errors.types import SERVER_ERROR
from drf_standardized_errors.types import ErrorResponse


class ExceptionFormatter(BaseExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        if error_response.type == SERVER_ERROR:
            return {
                "type": SERVER_ERROR,
                "errors": [
                    {
                        "code": "error",
                        "detail": "A server error occurred.",
                        "attr": None,
                    },
                ],
            }
        return super().format_error_response(error_response)
