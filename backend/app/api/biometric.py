from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import webauthn_service

router = APIRouter(prefix="/biometric", tags=["Fingerprint / Face ID"])


class RegisterBody(BaseModel):
    password: str
    credential_id: str = Field(min_length=16, max_length=512)
    public_key: str = Field(min_length=20, max_length=2000)
    algorithm: int
    client_data_json: str = Field(min_length=10, max_length=4000)
    label: Optional[str] = Field(default=None, max_length=60)


class LoginBody(BaseModel):
    credential_id: str = Field(min_length=16, max_length=512)
    client_data_json: str = Field(min_length=10, max_length=4000)
    authenticator_data: str = Field(min_length=20, max_length=2000)
    signature: str = Field(min_length=8, max_length=2000)


def _view(cred) -> dict:
    return {
        "id": cred.id,
        "label": cred.label,
        "created_at": cred.created_at.isoformat() if cred.created_at else None,
        "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
    }


@router.post("/login/challenge")
def login_challenge():
    return {"challenge": webauthn_service.make_challenge("login", 0)}


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = webauthn_service.finish_login(db, body.credential_id, body.client_data_json,
                                         body.authenticator_data, body.signature)
    return {"access_token": create_access_token(data={"sub": str(user.id)}), "token_type": "bearer"}


@router.post("/register/challenge")
def register_challenge(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return webauthn_service.begin_registration(db, current_user)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterBody, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cred = webauthn_service.finish_registration(
        db, current_user, body.password, body.credential_id, body.public_key, body.algorithm,
        body.client_data_json, body.label,
    )
    return _view(cred)


@router.get("/credentials")
def credentials(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_view(c) for c in webauthn_service.list_credentials(db, current_user)]


@router.delete("/credentials/{credential_pk}")
def remove(credential_pk: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    webauthn_service.remove_credential(db, current_user, credential_pk)
    return {"removed": True}
