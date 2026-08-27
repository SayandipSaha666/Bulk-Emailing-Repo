"""
main.py
Read sheet -> skip Sent -> skip if already contacted via Gmail ->
personalize -> send -> log -> update sheet -> print detailed summary.
"""

import argparse
import sys
import time
import yaml
from datetime import datetime
from dotenv import load_dotenv

from sheets_client import SheetsClient
from personalizer import Personalizer
from email_sender import EmailSender
from gmail_checker import GmailHistoryChecker


def load_config(path="config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    config = load_config()
    cols = config["google_sheets"]["columns"]

    log("Connecting to Google Sheet...")
    sheets = SheetsClient(config)

    log("Connecting to Gmail (checking for prior-contact history)...")
    gmail_checker = GmailHistoryChecker(config)

    log("Initializing personalization agent...")
    personalizer = Personalizer(config)

    if not args.dry_run:
        sender = EmailSender(config)

    rows = sheets.get_rows()
    log(f"Loaded {len(rows)} rows from sheet.")

    sent_list, not_sent_list, error_list = [], [], []

    for row in rows:
        company_name = row.get(cols["company_name"], "").strip()
        hr_name = row.get(cols["hr_name"], "").strip()
        hr_email = row.get(cols["hr_email"], "").strip()
        current_status = row.get(cols["status"], "").strip().lower()
        row_number = row["_row_number"]

        if current_status == "sent":
            not_sent_list.append((company_name, hr_email, "Already marked Sent in sheet"))
            continue

        if not hr_email or not company_name:
            reason = "Missing company name or HR email"
            log(f"[SKIP] Row {row_number}: {reason}")
            if not args.dry_run:
                sheets.update_status(row_number, "Not Sent", error_reason=reason)
            not_sent_list.append((company_name or "(unknown)", hr_email or "(unknown)", reason))
            continue

        if gmail_checker.has_prior_contact(hr_email):
            reason = "Already contacted previously (found in Sent Mail To/Cc)"
            log(f"[SKIP] {hr_email}: {reason}")
            if not args.dry_run:
                sheets.update_status(row_number, "Not Sent", error_reason=reason)
            not_sent_list.append((company_name, hr_email, reason))
            continue

        try:
            log(f"Researching '{company_name}' for personalization...")
            summary = personalizer.generate_summary(company_name)

            if args.dry_run:
                print(f"\n--- DRY RUN PREVIEW ---\nTo: {hr_email}\nCompany: {company_name}\nSummary:\n{summary}\n")
                continue

            msg = sender.build_message(hr_email, hr_name, company_name, summary)
            sender.send(msg, hr_email)

            sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"Mail sent to {hr_email} at {sent_at}")

            sheets.update_status(row_number, "Sent", sent_at=sent_at)
            sent_list.append((company_name, hr_email))

            time.sleep(config["email"]["delay_between_emails_sec"])

        except Exception as e:
            reason = str(e)
            log(f"[ERROR] Row {row_number} ({hr_email}): {reason}")
            if not args.dry_run:
                sheets.update_status(row_number, "Error", error_reason=reason)
            error_list.append((company_name, hr_email, reason))

    # ---------------- Final summary ----------------
    log("=" * 60)
    log(f"RUN SUMMARY — Total rows: {len(rows)}")
    log(f"✅ Sent: {len(sent_list)}")
    for c, e in sent_list:
        print(f"     - {c} <{e}>")

    log(f"⏭️  Not Sent (skipped): {len(not_sent_list)}")
    for c, e, reason in not_sent_list:
        print(f"     - {c} <{e}> — {reason}")

    log(f"❌ Error: {len(error_list)}")
    for c, e, reason in error_list:
        print(f"     - {c} <{e}> — {reason}")
    log("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Progress already written to sheet is preserved.")
        sys.exit(1)