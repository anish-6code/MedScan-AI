from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies import get_current_doctor
from app.models.user import User
from app.routers import auth
from app.schemas.user import UserRead

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Medical platform API — Module 1: Auth foundation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)


# ── Core endpoints ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"], summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/auth/me", tags=["auth"], response_model=UserRead, summary="Get current doctor profile")
def me(current_user: User = Depends(get_current_doctor)):
    return current_user
