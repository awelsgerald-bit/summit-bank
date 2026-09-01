import httpx

from app.core.config import settings

RESEND_URL = "https://api.resend.com/emails"
FROM_ADDRESS = "Summit Bank <onboarding@resend.dev>"


def send_email(to_email: str, subject: str, html_body: str) -> None:
    """
    Sends an email via Resend. Fails silently (logs, doesn't raise) so a broken
    email send never blocks a real banking action like KYC approval — the
    email is a notification, not a requirement for the underlying operation.
    """
    try:
        response = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": FROM_ADDRESS,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            },
            timeout=10.0,
        )
        response.raise_for_status()
    except (httpx.HTTPError, KeyError) as e:
        print(f"Email send failed to {to_email}: {e}")


def send_kyc_approved_email(to_email: str, full_name: str) -> None:
    send_email(
        to_email,
        "Your Summit Bank KYC verification is approved",
        f"""
        <div style="font-family: sans-serif; padding: 24px;">
            <h2>Hi {full_name},</h2>
            <p>Your identity verification has been approved. Your account now has full access to all Summit Bank features.</p>
            <p>— Summit Bank</p>
        </div>
        """,
    )


def send_kyc_rejected_email(to_email: str, full_name: str, reason: str | None) -> None:
    reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
    send_email(
        to_email,
        "Your Summit Bank KYC verification needs attention",
        f"""
        <div style="font-family: sans-serif; padding: 24px;">
            <h2>Hi {full_name},</h2>
            <p>We weren't able to approve your identity verification submission.</p>
            {reason_html}
            <p>Please review and resubmit your details.</p>
            <p>— Summit Bank</p>
        </div>
        """,
    )
    
def send_fraud_alert_email(to_email: str, transaction_id: int, transaction_type: str, amount, reasons: list[str]) -> None:
    reasons_html = "".join(f"<li>{r}</li>" for r in reasons)
    send_email(
        to_email,
        f"⚠ Flagged transaction #{transaction_id} needs review",
        f"""
        <div style="font-family: sans-serif; padding: 24px;">
            <h2>A transaction was flagged for review</h2>
            <p><strong>Transaction:</strong> #{transaction_id} — {transaction_type} — ${amount}</p>
            <p><strong>Reasons:</strong></p>
            <ul>{reasons_html}</ul>
            <p>Review it in the Admin Panel's Flagged queue.</p>
        </div>
        """,
    )