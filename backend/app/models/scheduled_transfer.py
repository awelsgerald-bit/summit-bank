from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint

from app.database import Base


class ScheduledTransfer(Base):
    """A transfer the user has set up to happen later (once) or on repeat. Each time it comes
    due it creates the same PENDING transfer a hand-typed one would, so balance checks, fraud
    checks and admin approval all still apply."""

    __tablename__ = "scheduled_transfers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_account_number = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(255), nullable=True)
    frequency = Column(String(10), nullable=False)  # once, daily, weekly, monthly
    anchor_day = Column(Integer, nullable=False, default=1)  # day of month for "monthly" (Nigerian time)
    next_run_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(10), nullable=False, default="active")  # active, paused, completed, cancelled
    run_count = Column(Integer, nullable=False, default=0)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(10), nullable=True)  # created, failed
    last_error = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ScheduledTransferRun(Base):
    """One row per due time that was picked up. UNIQUE(schedule_id, due_at) means a due time can
    only ever be run once, even if two servers or two requests race for it."""

    __tablename__ = "scheduled_transfer_runs"
    __table_args__ = (UniqueConstraint("schedule_id", "due_at", name="uq_schedule_due_time"),)

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("scheduled_transfers.id"), nullable=False, index=True)
    due_at = Column(DateTime(timezone=True), nullable=False)
    outcome = Column(String(10), nullable=False, default="claimed")  # claimed, created, failed
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    detail = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
