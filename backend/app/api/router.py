"""Top-level API router registration."""

from fastapi import APIRouter

from app.api.routes import lectures, quiz_sessions, users


api_router = APIRouter()
api_router.include_router(lectures.router, tags=["lectures"])
api_router.include_router(quiz_sessions.router, tags=["quiz-sessions"])
api_router.include_router(users.router, tags=["users"])
