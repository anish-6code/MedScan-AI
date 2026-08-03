"""
app/services/notifications.py

Module 10: Outbound notifications for critical alerts.
Supports SMS via Twilio and email via AWS SES.
Both are gracefully stubbed when env vars are not configured.
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── Twilio SMS ────────────────────────────────────────────────────────────────

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
DOCTOR_PHONE       = os.environ.get("DOCTOR_PHONE_NUMBER", "")


def send_sms_alert(alert: dict[str, Any]) -> bool:
    """
    Send SMS via Twilio for critical alerts.
    Returns True if sent, False if stubbed or failed.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, DOCTOR_PHONE]):
        logger.info("[SMS STUB] Twilio not configured — would have sent: %s", alert.get("message"))
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        body = (
            f"🚨 MedScan CRITICAL ALERT\n"
            f"Patient: {alert.get('patient_id', '?')[:8]}\n"
            f"Vital: {alert.get('vital_sign')} = {alert.get('value')}\n"
            f"{alert.get('message', '')}"
        )
        client.messages.create(body=body, from_=TWILIO_FROM_NUMBER, to=DOCTOR_PHONE)
        logger.info("[SMS] Sent critical alert to %s", DOCTOR_PHONE)
        return True
    except Exception as exc:
        logger.error("[SMS] Failed to send: %s", exc)
        return False


# ── AWS SES Email ─────────────────────────────────────────────────────────────

SES_REGION         = os.environ.get("SES_REGION", "ap-south-1")
SES_FROM_EMAIL     = os.environ.get("SES_FROM_EMAIL", "")
DOCTOR_EMAIL       = os.environ.get("DOCTOR_EMAIL", "")


def send_email_alert(alert: dict[str, Any]) -> bool:
    """
    Send email via AWS SES for critical alerts.
    Returns True if sent, False if stubbed or failed.
    """
    if not all([SES_FROM_EMAIL, DOCTOR_EMAIL]):
        logger.info("[EMAIL STUB] SES not configured — would have emailed: %s", alert.get("message"))
        return False
    try:
        import boto3
        ses = boto3.client("ses", region_name=SES_REGION)
        subject = f"[MedScan CRITICAL] {alert.get('vital_sign')} alert — patient {str(alert.get('patient_id', '?'))[:8]}"
        html = f"""
        <h2 style=\"color:red\">⚠ Critical Alert</h2>
        <p><b>Patient:</b> {alert.get('patient_id')}</p>
        <p><b>Vital Sign:</b> {alert.get('vital_sign')}</p>
        <p><b>Value:</b> {alert.get('value')}</p>
        <p><b>Severity:</b> {alert.get('severity')}</p>
        <p><b>Message:</b> {alert.get('message')}</p>
        <hr><p>MedScan AI Platform — Automated Alert</p>
        """
        ses.send_email(
            Source=SES_FROM_EMAIL,
            Destination={"ToAddresses": [DOCTOR_EMAIL]},
            Message={
                "Subject": {"Data": subject},
                "Body":    {"Html": {"Data": html}},
            },
        )
        logger.info("[EMAIL] Sent critical alert to %s", DOCTOR_EMAIL)
        return True
    except Exception as exc:
        logger.error("[EMAIL] Failed to send: %s", exc)
        return False


# ── Dispatcher ────────────────────────────────────────────────────────────────

def dispatch_critical_alert(alert: dict[str, Any]) -> None:
    """
    Called when a critical alert is created.
    Tries SMS first, then email — logs warnings but never raises.
    """
    if alert.get("severity") != "critical":
        return
    sms_sent   = send_sms_alert(alert)
    email_sent = send_email_alert(alert)
    if not sms_sent and not email_sent:
        logger.warning("[NOTIFY] No notification channel configured for critical alert %s", alert.get("id"))
