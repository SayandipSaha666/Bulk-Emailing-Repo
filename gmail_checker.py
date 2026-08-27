from googleapiclient.discovery import build
from sheets_client import get_google_credentials


class GmailHistoryChecker:
    def __init__(self, config: dict):
        gmail_cfg = config["gmail_history_check"]
        self.enabled = gmail_cfg.get("enabled", False)
        self.my_email = config["email"]["sender_email"]
        self._cache = {}
        if not self.enabled:
            return

        creds = get_google_credentials(gmail_cfg["credentials_file"])
        self.service = build("gmail", "v1", credentials=creds)

    def has_prior_contact(self, hr_email: str) -> bool:
        if not self.enabled:
            return False
        if hr_email in self._cache:
            return self._cache[hr_email]

        query = f"(to:{hr_email} OR cc:{hr_email}) (from:{self.my_email} OR cc:{self.my_email})"
        try:
            result = self.service.users().messages().list(userId="me", q=query, maxResults=1).execute()
            found = bool(result.get("messages"))
        except Exception as e:
            print(f"  [warn] Gmail history check failed for {hr_email}: {e}")
            found = False

        self._cache[hr_email] = found
        return found