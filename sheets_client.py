"""
sheets_client.py
Uses the SAME OAuth credentials as Gmail (one login covers both).
No service account key file needed.
"""

import os
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.readonly",
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
            creds = flow.run_local_server(port=0)  # opens browser once
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


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
        for key in ("status", "sent_at", "error_reason"):
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