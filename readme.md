# Bulk HR Outreach Automation

Reads companies from a Google Sheet, researches each one via web search,
writes a personalized 2-line pitch into an email template, sends the email
with explicit CC recipients, logs progress to the terminal, and writes the
send status back into the sheet.

## Sheet format expected

| Company Name | HR Name | HR Email | HR Contact Number | HR LinkedIn |
|---|---|---|---|---|

The script will automatically add `Status` and `Sent At` columns to the same
sheet if they don't already exist. Rows already marked `Sent` are skipped on
re-runs, so it's safe to interrupt and resume.

## Setup

1. Install dependencies: pip install -r requirements.txt
2. Google Sheets access: enable Sheets API, create a Service Account,
   download its JSON key as service_account.json, share the sheet with
   the service account's email as Editor, put the Spreadsheet ID in config.yaml.
3. Email (Gmail): enable 2FA, generate an App Password at
   https://myaccount.google.com/apppasswords
4. Anthropic API key: get one from https://console.anthropic.com
5. cp .env.example .env, then fill in real values
6. Configure config.yaml: spreadsheet ID, worksheet name, sender info,
   CC list, subject line, delay between sends, candidate pitch blurb.

## Running

python main.py --dry-run     # preview without sending
python main.py               # send for real

## Design notes

- Rate limiting via delay_between_emails_sec (Gmail caps ~500/day;
  use SendGrid/SES for higher volume).
- Idempotent: status written immediately per row, safe to re-run after a crash.
- Personalization has a fallback if web search/model call fails.
- Compliance: configure SPF/DKIM on your sending domain, follow
  CAN-SPAM/GDPR rules if scaling this up.