"""
email_sender.py
Builds and sends the email via SMTP, with explicit CC addresses attached
to every message.

Note on Gmail: you need an "App Password" (not your normal password) if
2FA is enabled — generate one at https://myaccount.google.com/apppasswords
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self, config: dict):
        email_cfg = config["email"]
        self.smtp_host = email_cfg["smtp_host"]
        self.smtp_port = email_cfg["smtp_port"]
        self.sender_email = email_cfg["sender_email"]
        self.sender_name = email_cfg["sender_name"]
        self.cc_emails = email_cfg["cc_emails"]
        self.subject_template = email_cfg["subject_template"]
        self.password = os.environ["EMAIL_APP_PASSWORD"]

        with open(email_cfg["template_file"], "r") as f:
            self.template = f.read()

    def build_message(self, to_email: str, hr_name: str, company_name: str,
                       personalized_summary: str) -> MIMEMultipart:
        subject = self.subject_template.format(company_name=company_name)
        body = self.template.format(
            hr_name=hr_name or "there",
            company_name=company_name,
            personalized_summary=personalized_summary,
            sender_name=self.sender_name,
        )

        msg = MIMEMultipart()
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = to_email
        msg["Cc"] = ", ".join(self.cc_emails)   # explicit CC, visible to all recipients
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        return msg

    def send(self, msg: MIMEMultipart, to_email: str):
        all_recipients = [to_email] + self.cc_emails
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, all_recipients, msg.as_string())