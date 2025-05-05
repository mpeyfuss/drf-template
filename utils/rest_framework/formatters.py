from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse, ErrorType


class FilteredExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        # Let's not reveal stack trace details on 500s
        # https://github.com/ghazi-git/drf-standardized-errors/issues/42
        if error_response.type == ErrorType.SERVER_ERROR:
            return {
                "type": ErrorType.SERVER_ERROR,
                "errors": [
                    {
                        "code": "server_internal_error",
                        "detail": "Server error occurred.",
                        "attr": None,
                    }
                ],
            }
        else:
            return super().format_error_response(error_response)
