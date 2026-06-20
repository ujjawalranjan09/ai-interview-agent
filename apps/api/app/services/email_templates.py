"""Email template engine — HTML email templates with variable injection."""



BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="{locale}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f7fb; }}
  .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
  .header {{ background: linear-gradient(135deg, #2563eb, #7c3aed); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
  .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
  .content {{ background: #ffffff; padding: 30px; border-radius: 0 0 12px 12px; }}
  .footer {{ text-align: center; padding: 20px; color: #94a3b8; font-size: 12px; }}
  .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; }}
  .score {{ font-size: 36px; font-weight: bold; color: #2563eb; text-align: center; }}
  .label {{ color: #64748b; font-size: 14px; }}
  .value {{ color: #1e293b; font-size: 16px; font-weight: 500; }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{heading}</h1>
    </div>
    <div class="content">
      {body}
    </div>
    <div class="footer">
      <p>{company_name} &mdash; AI Interview Agent</p>
      <p>{footer_text}</p>
    </div>
  </div>
</body>
</html>"""


TEMPLATES: dict[str, dict[str, str]] = {
    "interview_invitation": {
        "subject": "Interview Invitation from {company_name}",
        "body": """
<p>Hi <strong>{candidate_name}</strong>,</p>
<p>You have been invited to an interview with <strong>{company_name}</strong>.</p>
<p><strong>Interviewer:</strong> {interviewer_name}<br>
<strong>Duration:</strong> Approximately {duration} minutes</p>
<p>Click the button below to join your interview:</p>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">Join Interview</a>
</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
    "interview_reminder": {
        "subject": "Reminder: Interview Tomorrow with {company_name}",
        "body": """
<p>Hi <strong>{candidate_name}</strong>,</p>
<p>This is a friendly reminder that your interview with <strong>{company_name}</strong> is scheduled for <strong>{interview_date}</strong>.</p>
<p>Please ensure you have a quiet space and a working camera/microphone.</p>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">Join Interview</a>
</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
    "interview_completed": {
        "subject": "Interview Completed — {candidate_name} with {company_name}",
        "body": """
<p>Hi <strong>{interviewer_name}</strong>,</p>
<p>The interview with <strong>{candidate_name}</strong> has been completed.</p>
<table style="width: 100%; margin: 20px 0;">
  <tr><td class="label">Score</td><td class="value">{score}</td></tr>
  <tr><td class="label">Duration</td><td class="value">{duration} minutes</td></tr>
  <tr><td class="label">Questions</td><td class="value">{question_count}</td></tr>
</table>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">View Full Report</a>
</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
    "report_ready": {
        "subject": "Your Interview Report is Ready — {company_name}",
        "body": """
<p>Hi <strong>{candidate_name}</strong>,</p>
<p>Your interview report with <strong>{company_name}</strong> is now ready.</p>
<div class="score">{score}</div>
<p style="text-align: center; color: #64748b;">Overall Score</p>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">View Report</a>
</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
    "coaching_ready": {
        "subject": "Your Personalized Coaching Plan is Ready",
        "body": """
<p>Hi <strong>{candidate_name}</strong>,</p>
<p>Based on your interview performance, we have created a personalized coaching plan to help you improve.</p>
<p>The plan covers <strong>{areas_count} areas</strong> for improvement with specific recommendations and resources.</p>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">View Coaching Plan</a>
</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
    "welcome": {
        "subject": "Welcome to {company_name} — AI Interview Agent",
        "body": """
<p>Hi <strong>{candidate_name}</strong>,</p>
<p>Welcome to <strong>{company_name}</strong>! We're excited to have you on board.</p>
<p>You can now:</p>
<ul>
  <li>Complete your profile</li>
  <li>View and accept interview invitations</li>
  <li>Track your interview results and progress</li>
  <li>Access personalized coaching plans</li>
</ul>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">Get Started</a>
</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
    "password_reset": {
        "subject": "Password Reset Request — {company_name}",
        "body": """
<p>Hi <strong>{candidate_name}</strong>,</p>
<p>We received a request to reset your password for your <strong>{company_name}</strong> account.</p>
<p>Click the button below to set a new password. This link expires in 1 hour.</p>
<p style="text-align: center; margin: 30px 0;">
  <a href="{action_url}" class="button">Reset Password</a>
</p>
<p>If you didn't request this, you can safely ignore this email.</p>
<p>Best regards,<br>{company_name} Team</p>
""",
    },
}


def render_template(
    template_name: str,
    variables: dict[str, str],
    locale: str = "en",
) -> tuple[str, str, str]:
    """Render an email template. Returns (subject, html_body, text_body)."""
    template = TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")

    subject = template["subject"].format(**variables)
    body = template["body"].format(**variables)

    html = BASE_TEMPLATE.format(
        locale=locale,
        heading=subject,
        body=body,
        company_name=variables.get("company_name", "AI Interview Agent"),
        footer_text="This is an automated message. Please do not reply.",
    )

    import re
    text = re.sub(r"<[^>]+>", "", body)
    text = text.replace("&nbsp;", " ").strip()
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

    return subject, html, text


def list_templates() -> list[str]:
    """Return list of available template names."""
    return list(TEMPLATES.keys())
