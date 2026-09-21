from fastapi import FastAPI
from pydantic import BaseModel

from app.agent import ask_agent
from app.repository.database import initialize_database


app = FastAPI(
    title="College Academic Assistant Agent"
)


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.get("/")
def root():
    return {
        "message": "College Academic Assistant Agent is running"
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):

    answer = ask_agent(request.query)

    return {
        "answer": answer
    }