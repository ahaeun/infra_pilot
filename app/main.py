from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.qa import answer_question

app = FastAPI(title="Infra Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
def api_ask(payload: AskRequest):
    return answer_question(payload.question)
