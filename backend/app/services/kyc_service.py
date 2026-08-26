from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.kyc import KYCSubmission
from app.models.user import User
from app.services import email_service

VALID_ID_TYPES = {"passport", "national_id", "drivers_license"}


def submit_kyc(db: Session, user: User, data: dict) -> KYCSubmission:
    if data["id_type"] not in VALID_ID_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"id_type must be one of {VALID_ID_TYPES}")

    existing_pending = (
        db.query(KYCSubmission)
        .filter(KYCSubmission.user_id == user.id, KYCSubmission.status == "pending")
        .first()
    )
    if existing_pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a pending KYC submission")

    submission = KYCSubmission(user_id=user.id, **data, status="pending")
    db.add(submission)
    user.kyc_status = "pending"
    db.commit()
    db.refresh(submission)
    return submission


def get_my_kyc(db: Session, user: User) -> list[KYCSubmission]:
    return db.query(KYCSubmission).filter(KYCSubmission.user_id == user.id).order_by(KYCSubmission.created_at.desc()).all()


def list_pending_kyc(db: Session) -> list[KYCSubmission]:
    return db.query(KYCSubmission).filter(KYCSubmission.status == "pending").order_by(KYCSubmission.created_at.asc()).all()


def approve_kyc(db: Session, submission_id: int) -> KYCSubmission:
    submission = db.query(KYCSubmission).filter(KYCSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC submission not found")
    if submission.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Submission is already {submission.status}")

    user = db.query(User).filter(User.id == submission.user_id).first()

    submission.status = "approved"
    submission.reviewed_at = datetime.now(timezone.utc)
    user.kyc_status = "verified"
    db.commit()
    db.refresh(submission)

    email_service.send_kyc_approved_email(user.email, user.full_name)
    return submission


def reject_kyc(db: Session, submission_id: int, reason: str | None) -> KYCSubmission:
    submission = db.query(KYCSubmission).filter(KYCSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC submission not found")
    if submission.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Submission is already {submission.status}")

    user = db.query(User).filter(User.id == submission.user_id).first()

    submission.status = "rejected"
    submission.rejection_reason = reason
    submission.reviewed_at = datetime.now(timezone.utc)
    user.kyc_status = "unverified"
    db.commit()
    db.refresh(submission)

    email_service.send_kyc_rejected_email(user.email, user.full_name, reason)
    return submission