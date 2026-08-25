from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import accounts, auth, admin, transactions, wallets, beneficiaries, loans, fixed_deposits, cards
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import Base, engine
from app import models  # noqa: F401

app = FastAPI(title="Summit Bank API", version="0.1.0")

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(admin.router)
app.include_router(wallets.router)
app.include_router(beneficiaries.router)
app.include_router(loans.router)
app.include_router(fixed_deposits.router)
app.include_router(cards.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}