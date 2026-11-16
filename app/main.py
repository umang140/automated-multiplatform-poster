import logging
from pathlib import Path

# Use system certificate store where available (useful on corporate Windows environments)
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import PostingService

# Configure standard application logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("automated_posting")

app = FastAPI(
    title="Automated Multi-Platform Posting",
    version="1.0.0",
    description="Publishes a validated short message across 9 integrated platforms via POST /posting.",
)


def get_posting_service() -> PostingService:
    """Dependency provider for PostingService to allow easy mocking in test suites."""
    return PostingService()


def _extract_validation_error(exc: RequestValidationError) -> str:
    """
    Extract a clean, user-friendly error message from Pydantic's validation details
    matching the practical test error specification.
    """
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", [])]
        msg = err.get("msg", "")
        err_type = err.get("type", "")

        # Missing required field
        if "message" in loc and err_type == "missing":
            return "message field is required."
        if err_type == "missing":
            return "message field is required."

        # Custom Pydantic validator errors
        if "Value error," in msg:
            return msg.split("Value error, ", 1)[-1].strip()

        # String length constraints
        if err_type in ("string_too_long", "value_error.any_str.max_length"):
            return "Message must not exceed 200 characters."

        # Fallback to direct message if provided
        if msg:
            return msg.replace("Value error, ", "").strip()

    return "Invalid input."


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Return HTTP 400 with the required failure format on validation errors."""
    error_msg = _extract_validation_error(exc)
    logger.warning("Validation rejected for %s: %s", request.url.path, error_msg)
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": error_msg, "results": []},
    )


@app.get("/", tags=["Health"])
def health_check():
    """Health endpoint providing quick links to documentation and the posting route."""
    return {
        "status": "ok",
        "service": "Automated Multi-Platform Posting",
        "docs": "/docs",
        "endpoint": "POST /posting",
    }


@app.post(
    "/posting",
    response_model=PostingResponse,
    summary="Publish message across all platforms",
    tags=["Posting"],
)
async def post_message(
    body: PostingRequest,
    service: PostingService = Depends(get_posting_service),
):
    """
    Validates message input (length <= 200 chars, exactly 1 CTA link)
    and dispatches concurrently to all 9 supported third-party platforms.
    """
    logger.info("Received posting request (message length: %d)", len(body.message))
    response = await service.post_message(body.message)
    logger.info("Posting finished: overall success=%s", response.success)
    return response
