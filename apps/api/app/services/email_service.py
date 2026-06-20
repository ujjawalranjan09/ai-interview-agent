import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.services.email_templates import render_template

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT, timeout=10) as server:
            if settings.EMAIL_SMTP_USER:
                server.starttls()
                server.login(settings.EMAIL_SMTP_USER, settings.EMAIL_SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [to], msg.as_string())
        return True
    except Exception as e:
        logger.warning(f"Failed to send email: {e}")
        return False


def send_interview_completion_email(
    candidate_email: str, candidate_name: str, interview_id: str, score: float
) -> bool:
    html = f"""<html><body>
    <h2>Interview Complete</h2>
    <p>Dear {candidate_name},</p>
    <p>Your interview has been completed. Your overall score: <strong>{score:.1f}</strong>.</p>
    <p>You can view your detailed report by logging into your account.</p>
    <p>Best regards,<br/>AI Interview Agent Team</p>
    </body></html>"""
    return send_email(candidate_email, "Your Interview is Complete", html)


def send_share_link_email(
    candidate_email: str, candidate_name: str, share_url: str, interviewer_name: str
) -> bool:
    html = f"""<html><body>
    <h2>You're Invited to an Interview</h2>
    <p>Dear {candidate_name},</p>
    <p>{interviewer_name} has invited you to complete an interview.</p>
    <p>Click the link below to begin:</p>
    <p><a href="{share_url}">{share_url}</a></p>
    <p>This link is unique to you and does not require login.</p>
    <p>Best regards,<br/>AI Interview Agent Team</p>
    </body></html>"""
    return send_email(candidate_email, "Interview Invitation", html)


def send_templated_email(
    to_email: str,
    template_name: str,
    variables: dict[str, str],
    locale: str = "en",
) -> bool:
    subject, html_body, text_body = render_template(template_name, variables, locale)
    return send_email(to_email, subject, html_body)


def send_interview_invitation(
    to_email: str,
    candidate_name: str,
    interviewer_name: str,
    action_url: str,
    company_name: str = "AI Interview Agent",
    duration: int = 60,
    locale: str = "en",
) -> bool:
    return send_templated_email(
        to_email,
        "interview_invitation",
        {
            "candidate_name": candidate_name,
            "interviewer_name": interviewer_name,
            "action_url": action_url,
            "company_name": company_name,
            "duration": str(duration),
        },
        locale,
    )


def send_interview_reminder(
    to_email: str,
    candidate_name: str,
    interview_date: str,
    action_url: str,
    company_name: str = "AI Interview Agent",
    locale: str = "en",
) -> bool:
    return send_templated_email(
        to_email,
        "interview_reminder",
        {
            "candidate_name": candidate_name,
            "interview_date": interview_date,
            "action_url": action_url,
            "company_name": company_name,
        },
        locale,
    )


def send_report_ready(
    to_email: str,
    candidate_name: str,
    score: float,
    action_url: str,
    company_name: str = "AI Interview Agent",
    locale: str = "en",
) -> bool:
    return send_templated_email(
        to_email,
        "report_ready",
        {
            "candidate_name": candidate_name,
            "score": f"{score:.1f}",
            "action_url": action_url,
            "company_name": company_name,
        },
        locale,
    )


def send_welcome_email(
    to_email: str,
    candidate_name: str,
    action_url: str,
    company_name: str = "AI Interview Agent",
    locale: str = "en",
) -> bool:
    return send_templated_email(
        to_email,
        "welcome",
        {
            "candidate_name": candidate_name,
            "action_url": action_url,
            "company_name": company_name,
        },
        locale,
    )
