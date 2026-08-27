# Graph Report - Emailing  (2026-08-27)

## Corpus Check
- Corpus is ~1,653 words - fits in a single context window. You may not need a graph.

## Summary
- 57 nodes · 80 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 86% EXTRACTED · 12% INFERRED · 1% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9

## God Nodes (most connected - your core abstractions)
1. `Python dependencies` - 11 edges
2. `Bulk HR Outreach Automation` - 8 edges
3. `main()` - 7 edges
4. `Personalizer` - 7 edges
5. `SheetsClient` - 7 edges
6. `EmailSender` - 6 edges
7. `GmailHistoryChecker` - 5 edges
8. `Design notes` - 5 edges
9. `get_google_credentials()` - 4 edges
10. `JGEC Campus Recruitment Email Template` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Anthropic API key required` --semantically_similar_to--> `groq 0.11.0`  [AMBIGUOUS] [semantically similar]
  readme.md → requirements.txt
- `Bulk HR Outreach Automation` --implements--> `httpx 0.27.2`  [INFERRED]
  readme.md → requirements.txt
- `Bulk HR Outreach Automation` --implements--> `duckduckgo-search 6.2.13`  [INFERRED]
  readme.md → requirements.txt
- `Bulk HR Outreach Automation` --implements--> `PyYAML 6.0.2`  [INFERRED]
  readme.md → requirements.txt
- `{personalized_summary} placeholder` --rationale_for--> `Bulk HR Outreach Automation`  [INFERRED]
  templates/email_template.txt → readme.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **HR Outreach Pipeline** — readme_bulk_hr_outreach_automation, templates_email_template, readme_sheet_format, readme_rate_limiting, readme_idempotent_design, readme_personalization_fallback, readme_compliance [INFERRED 0.85]
- **Google Sheets dependency stack** — requirements_gspread, requirements_google_auth, requirements_google_auth_oauthlib, requirements_google_auth_httplib2, requirements_google_api_python_client [INFERRED 0.95]

## Communities (10 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.32
Nodes (3): Personalizer, personalizer.py Web-searches the company (via DuckDuckGo, no API key needed)…, Fetches a few real snippets about the company from DuckDuckGo.

### Community 1 - "Community 1"
Cohesion: 0.33
Nodes (3): EmailSender, email_sender.py Builds and sends the email via SMTP, with explicit CC addresses…, MIMEMultipart

### Community 2 - "Community 2"
Cohesion: 0.38
Nodes (3): GmailHistoryChecker, get_google_credentials(), sheets_client.py Uses the SAME OAuth credentials as Gmail (one login covers…

### Community 3 - "Community 3"
Cohesion: 0.29
Nodes (7): Anthropic API key required, Python dependencies, google-api-python-client 2.140.0, google-auth-httplib2 0.2.0, google-auth-oauthlib 1.2.1, groq 0.11.0, httpx 0.27.2

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (7): Bulk HR Outreach Automation, duckduckgo-search 6.2.13, PyYAML 6.0.2, {company_name} placeholder, JGEC Campus Recruitment Email Template, {personalized_summary} placeholder, {sender_name} placeholder

### Community 5 - "Community 5"
Cohesion: 0.60
Nodes (4): load_config(), log(), main(), main.py Read sheet -> skip Sent -> skip if already contacted via Gmail ->…

### Community 6 - "Community 6"
Cohesion: 0.50
Nodes (5): Compliance: SPF/DKIM, CAN-SPAM/GDPR, Design notes, Idempotent: status written per row, Personalization fallback on failure, Rate limiting via delay_between_emails_sec

### Community 8 - "Community 8"
Cohesion: 0.50
Nodes (4): Google Sheets integration setup, Sheet format expected, google-auth 2.32.0, gspread 6.1.2

## Ambiguous Edges - Review These
- `groq 0.11.0` → `Anthropic API key required`  [AMBIGUOUS]
  readme.md · relation: semantically_similar_to

## Knowledge Gaps
- **6 isolated node(s):** `google-auth-oauthlib 1.2.1`, `google-auth-httplib2 0.2.0`, `google-api-python-client 2.140.0`, `{company_name} placeholder`, `{sender_name} placeholder` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `groq 0.11.0` and `Anthropic API key required`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `Python dependencies` connect `Community 3` to `Community 8`, `Community 9`, `Community 4`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `Bulk HR Outreach Automation` connect `Community 4` to `Community 8`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `Personalizer` connect `Community 0` to `Community 5`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Bulk HR Outreach Automation` (e.g. with `duckduckgo-search 6.2.13` and `httpx 0.27.2`) actually correct?**
  _`Bulk HR Outreach Automation` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `google-auth-oauthlib 1.2.1`, `google-auth-httplib2 0.2.0`, `google-api-python-client 2.140.0` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._