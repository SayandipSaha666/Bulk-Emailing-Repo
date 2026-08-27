"""
main.py
Read sheet -> group merged-cell companies -> skip Sent -> skip if already
contacted via Gmail -> reuse or generate personalized summary -> send ->
log -> update sheet -> print detailed summary.
"""

import argparse
import sys
import time
import yaml
from datetime import datetime
from dotenv import load_dotenv

from sheets_client import SheetsClient, group_rows_by_company
from personalizer import Personalizer
from email_sender import EmailSender
from gmail_checker import GmailHistoryChecker


def load_config(path="config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:   # add encoding here too
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

    groups = group_rows_by_company(rows, cols)
    log(f"Grouped into {len(groups)} companies.")

    sent_list, not_sent_list, error_list = [], [], []

    for group in groups:
        company_name = group["company_name"]
        row_numbers = group["row_numbers"]
        first_row = row_numbers[0]
        hr_name = group["hr_names"][0] if group["hr_names"] else ""
        all_emails = group["hr_emails"]

        if any(s == "sent" for s in group["status_values"]):
            not_sent_list.append((company_name, ", ".join(all_emails), "Already marked Sent"))
            continue

        if not all_emails:
            reason = "No valid HR email found for this company"
            log(f"[SKIP] {company_name}: {reason}")
            for rn in row_numbers:
                sheets.update_status(rn, "Not Sent", error_reason=reason)
            not_sent_list.append((company_name, "(none)", reason))
            continue

        remaining_emails = [e for e in all_emails if not gmail_checker.has_prior_contact(e)]

        if not remaining_emails:
            reason = "All recipients already contacted previously"
            log(f"[SKIP] {company_name}: {reason}")
            for rn in row_numbers:
                sheets.update_status(rn, "Not Sent", error_reason=reason)
            not_sent_list.append((company_name, ", ".join(all_emails), reason))
            continue

        try:
            # ---- Reuse-or-generate summary logic ----
            if group["existing_summary"]:
                log(f"Using existing summary for '{company_name}' (skipping LLM call).")
                summary = group["existing_summary"]
            else:
                log(f"No summary found — researching '{company_name}'...")
                summary = personalizer.generate_summary(company_name)
                if not args.dry_run:
                    sheets.update_personalized_summary(first_row, summary)

            if args.dry_run:
                print(f"\n--- DRY RUN PREVIEW ---\nTo: {remaining_emails}\nCompany: {company_name}\nSummary:\n{summary}\n")
                continue

            msg = sender.build_message(remaining_emails, hr_name, company_name, summary)
            sender.send(msg, remaining_emails)

            sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"Mail sent to {', '.join(remaining_emails)} at {sent_at}")

            for rn in row_numbers:
                sheets.update_status(rn, "Sent", sent_at=sent_at)
            sent_list.append((company_name, ", ".join(remaining_emails)))

            time.sleep(config["email"]["delay_between_emails_sec"])

        except Exception as e:
            reason = str(e)
            log(f"[ERROR] {company_name}: {reason}")
            for rn in row_numbers:
                sheets.update_status(rn, "Error", error_reason=reason)
            error_list.append((company_name, ", ".join(all_emails), reason))

    log("=" * 60)
    log(f"RUN SUMMARY — Total companies: {len(groups)}")
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