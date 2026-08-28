"""
email_sender.py
Builds and sends the email via the Gmail API (OAuth) as HTML,
supporting multiple TO recipients and explicit CC addresses.
"""

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build


class EmailSender:
    def __init__(self, config: dict, creds):
        email_cfg = config["email"]
        self.sender_email = email_cfg["sender_email"]
        self.sender_name = email_cfg["sender_name"]
        self.cc_emails = email_cfg["cc_emails"]
        self.subject_template = email_cfg["subject_template"]

        with open(email_cfg["template_file"], "r", encoding="utf-8") as f:
            self.template = f.read()

        # Gmail API service, built from the SAME creds used for Sheets
        self.service = build("gmail", "v1", credentials=creds)

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
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        return msg

    def send(self, msg: MIMEMultipart, to_emails: list):
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        body = {"raw": raw}
        self.service.users().messages().send(userId="me", body=body).execute()