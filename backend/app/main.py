import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.api import accounts, auth, admin, transactions, wallets, beneficiaries, loans, fixed_deposits, cards, kyc, payments, strowallet, admin_strowallet, statements, saved_payments, support, savings, scheduled_transfers, referrals, internal
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import Base, engine
from app import models  # noqa: F401

logger = logging.getLogger("summit_bank.scheduler")


def _scheduler_pass() -> None:
    from app.database import SessionLocal
    from app.services import scheduled_transfer_service

    db = SessionLocal()
    try:
        scheduled_transfer_service.run_due(db)
    finally:
        db.close()


async def _scheduler_loop() -> None:
    while True:
        await asyncio.sleep(60)
        try:
            await run_in_threadpool(_scheduler_pass)
        except Exception:
            logger.exception("Scheduled-transfer pass failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Due scheduled transfers are run every minute while the server is awake. Tests build their
    # client without lifespan, so no timer runs there.
    task = asyncio.create_task(_scheduler_loop()) if settings.scheduler_enabled else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Summit Bank API", version="0.1.0", lifespan=lifespan)

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
app.include_router(kyc.router)
app.include_router(payments.router)
app.include_router(strowallet.router)
app.include_router(admin_strowallet.router)
app.include_router(statements.router)
app.include_router(saved_payments.router)
app.include_router(support.router)
app.include_router(savings.router)
app.include_router(scheduled_transfers.router)
app.include_router(referrals.router)
app.include_router(internal.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}