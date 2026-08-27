"""
personalizer.py
Web-searches the company (via DuckDuckGo, no API key needed) and feeds the
snippets to Groq's LLM to produce a 2-line, email-ready summary:
  Line 1: what the company does
  Line 2: why our candidate pool is a good fit for them
"""

import os
from groq import Groq
from duckduckgo_search import DDGS


class Personalizer:
    def __init__(self, config: dict):
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = config["personalization"]["model"]
        self.max_tokens = config["personalization"]["max_tokens"]
        self.num_results = config["personalization"].get("web_search_results", 3)
        self.candidate_pitch = config["candidate_pitch"]["summary"].strip()

    def _web_search(self, company_name: str) -> str:
        """Fetches a few real snippets about the company from DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{company_name} company overview", max_results=self.num_results))
            if not results:
                return ""
            return "\n".join(f"- {r.get('title', '')}: {r.get('body', '')}" for r in results)
        except Exception as e:
            print(f"  [warn] Web search failed for {company_name}: {e}")
            return ""

    def generate_summary(self, company_name: str) -> str:
        search_context = self._web_search(company_name)

        prompt = f"""You are helping write a personalized cold outreach email to the HR team of "{company_name}".

Web search snippets about the company:
{search_context if search_context else "(no search results found — use general reasoning)"}

Context about the candidates we place:
{self.candidate_pitch}

Task: Write EXACTLY two short lines, plain text, no markdown, no bullet points:
Line 1: One sentence on what the company does, based on the snippets above.
Line 2: One sentence connecting our candidate pool's skills to this specific company's likely hiring needs.

Return ONLY those two lines, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content.strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            return "\n".join(lines[:2]) if lines else self._fallback(company_name)
        except Exception as e:
            print(f"  [warn] Groq personalization failed for {company_name}: {e}")
            return self._fallback(company_name)

    def _fallback(self, company_name: str) -> str:
        return (
            f"{company_name} is a company we'd love to learn more about.\n"
            f"We believe our candidate pool could be a strong match for your growing team."
        )