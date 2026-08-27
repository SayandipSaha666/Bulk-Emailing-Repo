"""
personalizer.py
When personalization.enabled is True: web-searches the company via
DuckDuckGo and asks Groq to write a 2-sentence personalized summary.
When False (current default): skips all of that and just returns the
static_summary from config — no API calls, no delay, no dependency risk.
"""

import os
from groq import Groq
from duckduckgo_search import DDGS


class Personalizer:
    def __init__(self, config: dict):
        p_cfg = config["personalization"]
        self.enabled = p_cfg.get("enabled", True)
        self.static_summary = p_cfg.get("static_summary", "").strip()

        if self.enabled:
            self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
            self.model = p_cfg["model"]
            self.max_tokens = p_cfg["max_tokens"]
            self.num_results = p_cfg.get("web_search_results", 3)
            self.candidate_pitch = config["candidate_pitch"]["summary"].strip()

    def _web_search(self, company_name: str) -> str:
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
        if not self.enabled:
            return self.static_summary or self._fallback(company_name)

        search_context = self._web_search(company_name)
        prompt = f"""You are helping write a personalized paragraph for a campus recruitment invitation email to "{company_name}".

Web search snippets about the company:
{search_context if search_context else "(no search results found — use general reasoning)"}

Background on our students:
{self.candidate_pitch}

Task: Write EXACTLY two short sentences, plain text, no markdown, no bullet points:
Sentence 1: What "{company_name}" does.
Sentence 2: How our students can meaningfully contribute to "{company_name}" specifically.

Return ONLY those two sentences, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content.strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            return " ".join(lines[:2]) if lines else self._fallback(company_name)
        except Exception as e:
            print(f"  [warn] Groq personalization failed for {company_name}: {e}")
            return self._fallback(company_name)

    def _fallback(self, company_name: str) -> str:
        return (
            f"{company_name} is a company we'd love to learn more about. "
            f"We believe our students' technical foundation could be a strong match for your growing team."
        )