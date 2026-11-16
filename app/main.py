import truststore

truststore.inject_into_ssl()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import PostingService

app = FastAPI(
    title="Automated Multi-Platform Posting",
    version="1.0.0",
    description="POST /posting publishes one short message to multiple platforms.",
)
service = PostingService()


def _validation_message(exc: RequestValidationError) -> str:
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", [])]
        msg = err.get("msg", "")
        err_type = err.get("type", "")

        if "message" not in loc and err_type == "missing":
            return "message field is required."
        if err_type == "missing":
            return "message field is required."
        if "Value error," in msg:
            return msg.split("Value error, ", 1)[-1]
        if err_type in ("string_too_long", "value_error.any_str.max_length"):
            return "Message must not exceed 200 characters."
        if msg:
            return msg.replace("Value error, ", "")
    return "Invalid input."


@app.exception_handler(RequestValidationError)
async def on_validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": _validation_message(exc), "results": []},
    )


@app.get("/")
def home():
    return {"status": "ok", "docs": "/docs", "posting": "POST /posting"}


@app.post("/posting", response_model=PostingResponse)
async def posting(body: PostingRequest):
    return await service.post_message(body.message)
