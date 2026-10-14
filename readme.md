# JGEC Bulk HR Outreach Mailer

A Python automation tool for the **Training & Placement Cell, Jalpaiguri Government Engineering College (JGEC)**. It sends personalized campus-recruitment invitation emails to HR contacts at scale.

**What it does**

- Reads company / HR contact data from a **Google Sheet** (via `gspread`)
- Checks **Gmail history** so the same company is never emailed twice
- Builds personalized **HTML emails** (AI personalization via Groq is optional)
- Sends through the **Gmail API** (OAuth 2.0, not SMTP)
- Writes the send status back to the sheet
- Caches AI summaries in a `Personalized Summary` column to avoid repeat API calls

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure](#2-project-structure)
3. [Install Python Dependencies](#3-install-python-dependencies)
4. [Google Cloud Setup (get `gmail_credentials.json`)](#4-google-cloud-setup-get-gmail_credentialsjson)
5. [Generate `google_token.json`](#5-generate-google_tokenjson)
6. [Prepare the Google Sheet](#6-prepare-the-google-sheet)
7. [Configure `config.yaml`](#7-configure-configyaml)
8. [Optional: Groq AI Personalization](#8-optional-groq-ai-personalization)
9. [Run the Script](#9-run-the-script)
10. [Testing vs Production OAuth Mode (7-day token expiry)](#10-testing-vs-production-oauth-mode-7-day-token-expiry)
11. [Troubleshooting](#11-troubleshooting)
12. [Security Notes](#12-security-notes)

---

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| Python **3.10+** | Check with `python --version` |
| A Google account | The Gmail account the emails will be sent **from** |
| Access to the Google Sheet | The same account must be able to open/edit the sheet |
| A Google Cloud project | Free; no billing needed for these APIs at this scale |
| (Optional) Groq API key | Only if you enable AI personalization |
| An internet connection that can reach `*.googleapis.com` | See [Troubleshooting](#11-troubleshooting) for campus firewall issues |

---

## 2. Project Structure

Your folder should look roughly like this (file names may vary slightly in your copy):

```
Emailing/
├── main.py                    # Entry point
├── config.yaml                # Feature toggles & settings
├── requirements.txt           # Python dependencies
├── gmail_credentials.json     # Downloaded from Google Cloud (Step 4)  ← SECRET
├── google_token.json          # Auto-generated on first run (Step 5)   ← SECRET
├── .gitignore
└── README.md
```

---

## 3. Install Python Dependencies

### 3.1 Open a terminal in the project folder

**Windows (PowerShell / CMD):**

```powershell
cd C:\Users\<your-user>\Desktop\CODING\Personal\Emailing
```

**macOS / Linux:**

```bash
cd ~/path/to/Emailing
```

### 3.2 Create and activate a virtual environment (recommended)

**Windows:**

```powershell
python -m venv venv
venv\Scripts\activate
```

> If PowerShell blocks activation, run once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your prompt.

### 3.3 Install the requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 What `requirements.txt` should contain

If you don't have the file yet, create it with:

```txt
google-api-python-client
google-auth
google-auth-httplib2
google-auth-oauthlib
gspread
PyYAML
groq
httpx==0.27.2
duckduckgo-search
```

> ⚠️ **Keep `httpx==0.27.2` pinned.** Newer versions of `httpx` removed the `proxies` argument, which makes the `groq` library crash with a `TypeError`.

### 3.5 Verify the install

```bash
python -c "import gspread, googleapiclient, google_auth_oauthlib, yaml; print('All good')"
```

---

## 4. Google Cloud Setup (get `gmail_credentials.json`)

`gmail_credentials.json` is the **OAuth client file** that identifies your app to Google. You download it once from the Google Cloud Console.

> **Why OAuth and not a service account?**
> Many organizations (including this one) enforce the policy `iam.disableServiceAccountKeyCreation`, so service-account JSON keys can't be created. The **OAuth Desktop-app flow** is the supported path for both Gmail and Sheets here. Also, plain SMTP password login no longer works with Gmail.

### Step 4.1 – Create (or select) a Google Cloud project

1. Go to **https://console.cloud.google.com/** and sign in with the Gmail account you'll send from.
2. Click the **project picker** (top bar, next to the Google Cloud logo).
3. Click **New Project**.
4. Enter a name, e.g. `jgec-placement-mailer`. Leave Organization/Location as default.
5. Click **Create**, then make sure the new project is selected in the picker.

### Step 4.2 – Enable the required APIs

1. Open the left menu → **APIs & Services → Library**.
2. Search for each of the following, open it, and click **Enable**:
   - **Gmail API**
   - **Google Sheets API**
   - **Google Drive API** (`gspread` uses it to open sheets by name)

Verify under **APIs & Services → Enabled APIs & services** that all three appear.

### Step 4.3 – Configure the OAuth consent screen (Google Auth Platform)

Google recently moved this into the **Google Auth Platform** section. Menu names may differ slightly, but the flow is the same.

1. Go to **APIs & Services → OAuth consent screen** (or directly **Google Auth Platform**).
2. If you see **Get started**, click it and fill in:
   - **App name:** e.g. `JGEC Placement Mailer`
   - **User support email:** your email
   - **Audience / User type:** choose **External** (use **Internal** only if you're on a Google Workspace org and everyone is inside it)
   - **Contact information:** your email
3. Agree to the user data policy and click **Create**.

### Step 4.4 – Add yourself as a Test user

While the app is in **Testing** mode, only listed test users can sign in.

1. Open **Audience** (or the *Test users* section of the consent screen).
2. Under **Test users**, click **+ Add users**.
3. Add the Gmail address you'll authorize with → **Save**.

> If you skip this, login fails with **Error 403: access_denied**.

### Step 4.5 – Add the scopes (Data Access)

1. Open **Data Access** (or *Scopes* in the older UI) → **Add or remove scopes**.
2. Add the scopes your code uses. Typically:

   | Scope | Purpose |
   |---|---|
   | `https://www.googleapis.com/auth/gmail.send` | Send emails |
   | `https://www.googleapis.com/auth/gmail.readonly` | Check history to avoid duplicates |
   | `https://www.googleapis.com/auth/spreadsheets` | Read/write the Google Sheet |
   | `https://www.googleapis.com/auth/drive.readonly` | Let `gspread` find the sheet (if your code uses it) |

3. Click **Update → Save**.

> ✅ **The scopes here should match the `SCOPES` list in your Python code.** If they differ, the token won't have the permissions the code requests.

### Step 4.6 – Create the OAuth client and download `gmail_credentials.json`

1. Go to **APIs & Services → Credentials** (or **Google Auth Platform → Clients**).
2. Click **+ Create Credentials → OAuth client ID** (or **+ Create client**).
3. **Application type:** choose **Desktop app** ← important; other types will not work with the local-browser flow.
4. **Name:** e.g. `Mailer Desktop Client` → **Create**.
5. A dialog appears with the Client ID and Secret. Click **Download JSON**.
6. **Rename** the downloaded file (it will be called something like `client_secret_XXXX.apps.googleusercontent.com.json`) to:

   ```
   gmail_credentials.json
   ```
7. Move it into the project root folder (next to `main.py`).

You now have **`gmail_credentials.json`** ✅

---

## 5. Generate `google_token.json`

`google_token.json` stores **your personal authorization** (access + refresh token). You never download it from GCP — it's **created automatically** the first time the script runs the OAuth flow.

### Step 5.1 – Make sure no old token exists

If a `google_token.json` already exists (from older scopes or an expired login), delete it:

```bash
# Windows
del google_token.json
# macOS / Linux
rm google_token.json
```

### Step 5.2 – Run the script

```bash
python main.py
```

(Use whatever your entry file is called.)

### Step 5.3 – Complete the browser login

1. Your **default browser opens** automatically with a Google sign-in page.
2. Choose the Gmail account you added as a **Test user**.
3. You will see a warning: **"Google hasn't verified this app."**
   This is normal for apps in Testing mode. Click **Advanced → Go to <App name> (unsafe)**.
4. Review the permissions and tick **all** requested checkboxes (Gmail send/read, Sheets, etc.).
5. Click **Continue / Allow**.
6. The browser shows *"The authentication flow has completed."* You can close the tab.

### Step 5.4 – Confirm the token was created

A new file **`google_token.json`** now appears in the project folder. Future runs reuse it silently and refresh it automatically.

> 🔁 **Any time you change `SCOPES` in the code, delete `google_token.json` and repeat this section** so Google asks for fresh consent with the new scopes.

### If the browser doesn't open (remote machine / headless)

Run the script on a machine with a browser to generate the token, then copy `google_token.json` to the target machine.

---

## 6. Prepare the Google Sheet

1. Create or open the Google Sheet that holds the company/HR data, using the **same Google account**.
2. Note the **sheet name / URL / ID** (the long ID in the URL between `/d/` and `/edit`).
3. Make sure the header row matches what the code expects. Typical columns:

   | Company | HR Name | HR Email | Status | Personalized Summary |
   |---|---|---|---|---|

   > Column names must match your code/`config.yaml` exactly (check spelling and spaces).

**Data-handling features already supported**

- Multiple emails in one cell separated by commas, semicolons, or new lines
- Merged cells for companies with several HR rows

---

## 7. Configure `config.yaml`

Open `config.yaml` and fill in your values. Example (adapt keys to your actual file):

```yaml
sheet:
  name: "Placement HR Contacts"      # or spreadsheet ID / URL
  worksheet: "Sheet1"

email:
  subject: "Campus Recruitment Invitation – JGEC"
  sender_name: "Training & Placement Cell, JGEC"

personalization:
  enabled: false        # true = use Groq AI; false = use static summaries
```

---

## 8. Optional: Groq AI Personalization

Skip this if `personalization.enabled: false`.

1. Create a free account at **https://console.groq.com/** and generate an **API key** under *API Keys*.
2. Provide the key to the script the way your code expects it, for example as an environment variable:

   **Windows (PowerShell):**
   ```powershell
   setx GROQ_API_KEY "your_key_here"
   ```
   **macOS / Linux:**
   ```bash
   export GROQ_API_KEY="your_key_here"
   ```
   (Open a **new** terminal after `setx`.)
3. Set `personalization.enabled: true` in `config.yaml`.

The script uses the Groq model `llama-3.3-70b-versatile` and DuckDuckGo search for company context. Generated summaries are cached in the sheet's **Personalized Summary** column so each company is only processed once.

---

## 9. Run the Script

```bash
# activate the venv first
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

python main.py
```

**Recommended first run:** test with just 1–2 rows (for example, your own email address) before sending to real HR contacts.

Daily Gmail sending limits apply (about **500 emails/day** for regular @gmail.com accounts, about **2,000/day** for Workspace). Send in batches if your list is large.

---

## 10. Testing vs Production OAuth Mode (7-day token expiry)

While the OAuth app's **Publishing status = Testing**, Google **expires the refresh token after 7 days**. You'll then see `invalid_grant` / `Token has been expired or revoked`, and must delete `google_token.json` and log in again.

**To stop the weekly expiry, publish the app to Production:**

1. Go to **Google Auth Platform → Audience**.
2. Click **Publish app** → confirm.
3. Google may require **Branding** details before publishing, such as:
   - App home page URL
   - Privacy policy URL
   - Authorized domain(s)

   A simple placeholder page on **Google Sites** or **GitHub Pages** (home + privacy policy) is enough for personal/internal use.
4. After publishing, the app will show an **"unverified app"** screen at login. For your own use you can still click **Advanced → Go to app (unsafe)**. (Full verification is only needed if you want to serve the public.)
5. **Delete `google_token.json` and re-authorize once** after switching to Production so you get a long-lived refresh token.

---

## 11. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `getaddrinfo failed` / `[Errno 11001]` when refreshing the token | Campus network/firewall blocks `*.googleapis.com` / `oauth2.googleapis.com` DNS | Test on a **mobile hotspot**. If it works, ask IT to whitelist `*.googleapis.com`, or run the script from another network |
| `Error 403: access_denied` at login | Your email isn't a **Test user** | Add it under *Audience → Test users* (Step 4.4) |
| `invalid_grant` / token expired or revoked | 7-day Testing expiry, password change, or revoked access | Delete `google_token.json` and re-run (and publish to Production, Section 10) |
| `insufficient authentication scopes` (403) | Token was created before scopes changed | Delete `google_token.json`, re-run, and tick **all** permission checkboxes |
| `FileNotFoundError: gmail_credentials.json` | File missing or misnamed | Re-download from GCP, rename exactly, place in project root |
| `redirect_uri_mismatch` | OAuth client isn't type **Desktop app** | Create a new **Desktop app** client (Step 4.6) |
| `Cannot create service account key` / `iam.disableServiceAccountKeyCreation` | Org policy blocks keys | Use the OAuth Desktop flow in this README (don't use service accounts) |
| `Gmail API has not been used in project … / is disabled` | API not enabled | Enable Gmail, Sheets, Drive APIs (Step 4.2) |
| `TypeError: ... unexpected keyword argument 'proxies'` | Incompatible `httpx` with `groq` | `pip install httpx==0.27.2` |
| Garbled characters (mojibake) in emails or files | Windows default encoding | Make sure all `open()` calls use `encoding="utf-8"` and `MIMEText(..., "html", "utf-8")` |
| `SpreadsheetNotFound` | Wrong sheet name/ID, or sheet not accessible by the authorized account | Check the name/ID in `config.yaml` and the sharing settings |
| `IndentationError` / missing method after editing | Partial code paste | Replace the **whole file** instead of pasting snippets |
| Browser doesn't open for login | Headless/remote machine | Generate the token on a normal PC and copy `google_token.json` |

---

## 12. Security Notes

- **Never commit or share** `gmail_credentials.json` or `google_token.json`. Anyone with them can act as your Gmail account.
- Add these to `.gitignore`:

  ```gitignore
  gmail_credentials.json
  google_token.json
  .env
  venv/
  __pycache__/
  ```
- If a secret is ever leaked: GCP Console → **Credentials** → delete/regenerate the client, and revoke access at **https://myaccount.google.com/permissions**, then delete `google_token.json`.
- Send only to contacts who are appropriate for placement outreach, and follow your institution's communication policies.

---

## Quick-Start Cheat Sheet

```text
1.  python -m venv venv  &&  venv\Scripts\activate
2.  pip install -r requirements.txt            (keep httpx==0.27.2)
3.  GCP Console → new project → enable Gmail, Sheets, Drive APIs
4.  OAuth consent screen → External → add yourself as Test user → add scopes
5.  Credentials → Create OAuth client → Desktop app → Download JSON
6.  Rename to gmail_credentials.json → place in project root
7.  python main.py → log in in browser → google_token.json is created
8.  Fill config.yaml, prepare the Google Sheet, test with 1–2 rows
9.  Publish the app to Production to avoid the 7-day token expiry
```