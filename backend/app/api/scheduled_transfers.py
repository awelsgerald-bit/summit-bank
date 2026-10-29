from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_pin_set_and_valid
from app.models.user import User
from app.schemas.round3b import RunResponse, ScheduleCreate, ScheduleResponse
from app.services import lookup_service, scheduled_transfer_service

router = APIRouter(prefix="/scheduled-transfers", tags=["Scheduled transfers"])


def _present(db: Session, sched) -> dict:
    owner = db.query(User).filter(User.account_number == sched.recipient_account_number).first()
    return {
        "id": sched.id,
        "recipient_account_number": sched.recipient_account_number,
        "recipient_name": lookup_service.mask_name(owner.full_name) if owner else "Unknown account",
        "amount": sched.amount,
        "description": sched.description,
        "frequency": sched.frequency,
        "next_run_at": sched.next_run_at,
        "end_at": sched.end_at,
        "status": sched.status,
        "run_count": sched.run_count,
        "last_run_at": sched.last_run_at,
        "last_status": sched.last_status,
        "last_error": sched.last_error,
    }


@router.get("", response_model=list[ScheduleResponse])
def list_schedules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_present(db, s) for s in scheduled_transfer_service.list_mine(db, current_user)]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    current_user: User = Depends(require_pin_set_and_valid),
    db: Session = Depends(get_db),
):
    sched = scheduled_transfer_service.create(
        db, current_user, payload.recipient_account_number, payload.amount, payload.description,
        payload.frequency, payload.first_run_at, payload.end_at,
    )
    return _present(db, sched)


@router.post("/{schedule_id}/pause", response_model=ScheduleResponse)
def pause_schedule(schedule_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _present(db, scheduled_transfer_service.pause(db, current_user, schedule_id))


@router.post("/{schedule_id}/resume", response_model=ScheduleResponse)
def resume_schedule(
    schedule_id: int,
    current_user: User = Depends(require_pin_set_and_valid),  # resuming re-authorises, so it needs the PIN
    db: Session = Depends(get_db),
):
    return _present(db, scheduled_transfer_service.resume(db, current_user, schedule_id))


@router.post("/{schedule_id}/cancel", response_model=ScheduleResponse)
def cancel_schedule(schedule_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _present(db, scheduled_transfer_service.cancel(db, current_user, schedule_id))


@router.get("/{schedule_id}/runs", response_model=list[RunResponse])
def schedule_runs(schedule_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return scheduled_transfer_service.list_runs(db, current_user, schedule_id)
