from pydantic import ValidationError


class UnknownDocTypeError(Exception):
    def __init__(self, doc_type: str):
        self.doc_type = doc_type
        super().__init__(f"Unknown doc_type: {doc_type!r}")


class ExtractionFailedError(Exception):
    def __init__(self, doc_type: str, errors: ValidationError, attempt_count: int):
        self.doc_type = doc_type
        self.errors = errors
        self.attempt_count = attempt_count
        super().__init__(
            f"Extraction failed for doc_type {doc_type!r} after {attempt_count} attempt(s)"
        )


class LLMServiceError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        self.status_code = status_code
        super().__init__(message)


def serializable_errors(exc: ValidationError) -> list[dict]:
    """Extract JSON-safe fields from a ValidationError (drops non-serializable 'input'/'ctx')."""
    return [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
