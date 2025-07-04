"""Agent responsible for communication-related tasks.

This module centralises routines for sending messages or e-mails.  A
lightweight Slack webhook integration is provided as an example for the
``send_message`` function and ``send_email`` includes both Outlook and
SMTP fallbacks.
"""

import os
import re

from logger import log


def send_message(destination: str, message: str, user: str = "") -> bool:
    """Send a message to a generic destination.

    ``destination`` may be a Slack webhook URL or any HTTP endpoint that
    accepts a JSON payload with a ``text`` field.  The function returns a
    boolean indicating success.

    Parameters
    ----------
    destination : str
        Endpoint where the message should be delivered.
    message : str
        Message content.
    user : str, optional
        Identifier of the user sending the message.
    """

    log(f"Sending to {destination}: {message}")

    try:
        import requests

        resp = requests.post(destination, json={"text": message}, timeout=10)
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}")
        log("Message sent successfully")
        return True
    except Exception as exc:  # pragma: no cover - network dependent
        log(f"Failed to send message: {exc}", "ERROR")
        return False


def send_email(to: str, subject: str, attachment: str, user: str = "") -> bool:
    """Send an email with an attachment.

    Attempts to use Outlook via ``win32com.client``. If Outlook is not
    available, falls back to a minimal SMTP example (Gmail). Environment
    variables ``GMAIL_USER`` and ``GMAIL_PASS`` should contain credentials for
    the SMTP fallback.

    Parameters
    ----------
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    attachment : str
        Path to a file that will be attached.
    user : str, optional
        Identifier for the user on whose behalf the email is sent.

    Returns
    -------
    bool
        ``True`` on success, ``False`` otherwise.
    """

    log(f"Preparing email to {to} with {attachment}")

    if not re.match(r"[^@]+@[^@]+\.[^@]+", to):
        log("Invalid recipient address", "ERROR")
        return False
    if attachment and not os.path.exists(attachment):
        log("Attachment not found", "ERROR")
        return False

    # Try Outlook first
    try:
        import win32com.client  # type: ignore

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.Subject = subject
        mail.Body = "Please see attached."
        if attachment and os.path.exists(attachment):
            mail.Attachments.Add(attachment)
        mail.Send()
        log("Email sent via Outlook")
        return True
    except Exception as exc:
        log(f"Outlook send failed: {exc}", "WARNING")

    # SMTP fallback
    try:
        import smtplib
        from email.message import EmailMessage

        smtp_user = os.environ.get("GMAIL_USER")
        password = os.environ.get("GMAIL_PASS")
        if not smtp_user or not password:
            raise RuntimeError("SMTP credentials not configured")

        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content("Please see attached.")

        if attachment and os.path.exists(attachment):
            with open(attachment, "rb") as f:
                data = f.read()
            msg.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=os.path.basename(attachment),
            )

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, password)
        server.send_message(msg)
        server.quit()
        log("Email sent via SMTP")
        return True
    except Exception as exc:
        log(f"SMTP send failed: {exc}", "ERROR")
        return False
