from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.qa import answer_question

app = FastAPI(title="Infra Pilot")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class AskRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/ask")
def api_ask(payload: AskRequest):
    return answer_question(payload.question)
