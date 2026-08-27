"""
email_sender.py
Builds and sends the email via SMTP as HTML (for bold/highlighted text),
supporting multiple TO recipients and explicit CC addresses.
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

        with open(email_cfg["template_file"], "r", encoding="utf-8") as f:
            self.template = f.read()

    def build_message(self, to_emails: list, hr_name: str, company_name: str,
                       personalized_summary: str) -> MIMEMultipart:
        subject = self.subject_template.format(company_name=company_name)
        html_body = self.template.format(
            hr_name=hr_name or "there",
            company_name=company_name,
            personalized_summary=personalized_summary,
            sender_name=self.sender_name,
        )

        msg = MIMEMultipart()
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = ", ".join(to_emails)
        msg["Cc"] = ", ".join(self.cc_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))   # "html" instead of "plain"
        return msg

    def send(self, msg: MIMEMultipart, to_emails: list):
        all_recipients = to_emails + self.cc_emails
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, all_recipients, msg.as_string())