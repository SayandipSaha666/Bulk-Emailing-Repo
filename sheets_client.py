"""
sheets_client.py
Uses OAuth (shared with Gmail) instead of a service account.
Handles all read/write interaction with the Google Sheet, plus grouping
rows into companies to handle merged Company Name cells and multiple
HR emails per row/group.
"""

import os
import re
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
TOKEN_FILE = "google_token.json"


def get_google_credentials(credentials_file: str):
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def split_emails(raw: str):
    """Splits a cell's email content on comma, semicolon, or newline."""
    if not raw:
        return []
    parts = re.split(r'[,;\n]+', raw)
    return [p.strip().strip('"').strip("'") for p in parts if p.strip()]


def group_rows_by_company(rows, cols):
    """
    Forward-fills company name for blank rows (merged cell behavior),
    and aggregates HR names/emails/status/summary across all rows
    belonging to the same company.
    """
    groups = []
    current = None

    for row in rows:
        raw_company = row.get(cols["company_name"], "").strip()

        if raw_company:
            current = {
                "company_name": raw_company,
                "row_numbers": [],
                "hr_names": [],
                "hr_emails": [],
                "status_values": [],
                "existing_summary": "",
            }
            groups.append(current)

        if current is None:
            continue

        current["row_numbers"].append(row["_row_number"])

        hr_name = row.get(cols["hr_name"], "").strip()
        if hr_name and hr_name not in current["hr_names"]:
            current["hr_names"].append(hr_name)

        raw_emails = row.get(cols["hr_email"], "")
        for email in split_emails(raw_emails):
            if email not in current["hr_emails"]:
                current["hr_emails"].append(email)

        current["status_values"].append(row.get(cols["status"], "").strip().lower())

        # Capture existing summary from whichever row actually has it non-empty
        existing = row.get(cols["personalized_summary"], "").strip()
        if existing and not current["existing_summary"]:
            current["existing_summary"] = existing

    return groups


class SheetsClient:
    def __init__(self, config: dict):
        sheet_cfg = config["google_sheets"]
        creds = get_google_credentials(config["gmail_history_check"]["credentials_file"])
        gc = gspread.authorize(creds)
        self.spreadsheet = gc.open_by_key(sheet_cfg["spreadsheet_id"])
        self.worksheet = self.spreadsheet.worksheet(sheet_cfg["worksheet_name"])
        self.columns = sheet_cfg["columns"]
        self._ensure_status_columns_exist()

    def _ensure_status_columns_exist(self):
        header = self.worksheet.row_values(1)
        updated = False
        for key in ("status", "sent_at", "error_reason", "personalized_summary"):
            col_name = self.columns[key]
            if col_name not in header:
                header.append(col_name)
                updated = True
        if updated:
            self.worksheet.update("A1", [header])
        self.header = header

    def get_rows(self):
        records = self.worksheet.get_all_records()
        rows = []
        for i, record in enumerate(records, start=2):
            record["_row_number"] = i
            rows.append(record)
        return rows

    def update_status(self, row_number: int, status: str, sent_at: str = "", error_reason: str = ""):
        status_col = self.header.index(self.columns["status"]) + 1
        self.worksheet.update_cell(row_number, status_col, status)
        if sent_at:
            sent_at_col = self.header.index(self.columns["sent_at"]) + 1
            self.worksheet.update_cell(row_number, sent_at_col, sent_at)
        error_col = self.header.index(self.columns["error_reason"]) + 1
        self.worksheet.update_cell(row_number, error_col, error_reason)

    def update_personalized_summary(self, row_number: int, summary: str):
        col = self.header.index(self.columns["personalized_summary"]) + 1
        self.worksheet.update_cell(row_number, col, summary)