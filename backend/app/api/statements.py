from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.statement import ReceiptResponse, StatementResponse
from app.services import statement_service

router = APIRouter(tags=["Statements"])


@router.get("/statements", response_model=StatementResponse)
def get_statement(
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return statement_service.build_statement(db, current_user, start, end)


@router.get("/statements/csv")
def download_statement_csv(
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = statement_service.build_statement(db, current_user, start, end)
    body = statement_service.statement_csv(current_user, statement)
    name = f"summit-statement-{start or 'start'}-to-{end or 'today'}.csv"
    return Response(
        content="﻿" + body,  # BOM so Excel shows ₦ and accents correctly
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.get("/transactions/{transaction_id}/receipt", response_model=ReceiptResponse)
def get_receipt(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return statement_service.build_receipt(db, current_user, transaction_id)
