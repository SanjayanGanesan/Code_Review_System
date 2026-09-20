from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from app.analyzers.registry import build_analyzers
from app.domain.models import CodeSubmission
from app.pipeline.orchestrator import ReviewPipeline
from app.storage.db import get_connection, init_db
from app.storage.repository import ReviewRepository


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(title="AI Code Review System")
app.mount("/static",StaticFiles(directory=BASE_DIR/"static"),name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


init_db()
_conn = get_connection()
repository = ReviewRepository(_conn)


@app.get("/")
def dashboard(request: Request):
    reviews = repository.list_recent(limit=25)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "reviews": reviews}
    )

@app.post("/review")
def submit_review(
    request: Request,
    filename: str = Form("submission.py"),
    language: str = Form("python"),
    code: str = Form(...),
    use_llm: bool = Form(False),
):
    submission = CodeSubmission(code=code, filename=filename, language=language)
    analyzers = build_analyzers(include_llm=use_llm)
    pipeline = ReviewPipeline(analyzers=analyzers, repository=repository)
    result = pipeline.run(submission)
    return RedirectResponse(url=f"/reviews/{result.id}", status_code=303)

@app.get("/reviews/{review_id}")
def review_detail(request: Request, review_id: str):
    result = repository.get(review_id)
    if result is None:
        return templates.TemplateResponse(
            "not_found.html", {"request": request, "review_id": review_id}, status_code=404
        )
    return templates.TemplateResponse(
        "review_detail.html", {"request": request, "review": result}
    )