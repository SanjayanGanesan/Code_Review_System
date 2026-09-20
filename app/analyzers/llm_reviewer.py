import json
import os
from app.analyzers.base import Analyzer
from app.domain.models import CodeSubmission, Finding, Severity


MAX_LINES_FOR_LLM = 400

SYSTEM_PROMPT = """You are a senior software engineer performing a code review.
Review the given code for: logic bugs, edge cases, poor naming, bad
abstractions, missing error handling, and design smells. Do NOT repeat
generic style nitpicks (line length, docstrings) - a separate linter
already handles those.

Respond with ONLY a JSON array (no markdown fences, no prose) of objects
shaped exactly like:
[{"severity": "critical|high|medium|low|info",
  "category": "bug|design|readability|performance",
  "line": <int or null>,
  "message": "<one or two sentence explanation>",
  "suggestion": "<concrete fix, or null>"}]

If the code has no issues worth raising, respond with []."""


_SEVERITY_MAP = {s.value: s for s in Severity}


class LLMReviewAnalyzer(Analyzer):
    name = 'llm-semantic'

    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")


    def analyze(self, submission: CodeSubmission) -> list[Finding]:
        if not self.api_key:
            return [Finding(
                analyzer=self.name, severity=Severity.INFO, category="config",
                message="LLM review skipped: no GROQ_API_KEY set.",
            )]
        if len(submission.lines) > MAX_LINES_FOR_LLM:
            return [Finding(
                analyzer=self.name, severity=Severity.INFO, category="config",
                message=f"File has {len(submission.lines)} lines; LLM review "
                        f"skipped above {MAX_LINES_FOR_LLM} to control cost/latency. "
                        f"Split the file or review it in chunks.",
            )]


        try:
            raw = self._call_model(submission)
            return self._parse_response(raw)
        except Exception as e:
            return [Finding(
                analyzer=self.name, severity=Severity.INFO, category="config",
                message=f"LLM review failed: {e}",
            )]

    def _call_model(self, submission: CodeSubmission) -> str:

        from groq import Groq

        client = Groq(api_key=self.api_key)
        numbered = "\n".join(
            f"{i+1:>4}  {line}" for i, line in enumerate(submission.lines)
        )
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Language: {submission.language}\n\n```\n{numbered}\n```"},
            ],
        )
        return response.choices[0].message.content

    def _parse_response(self, raw: str) -> list[Finding]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[raw.find("["):]
        items = json.loads(raw) if raw else []

        findings = []
        for item in items:
            severity = _SEVERITY_MAP.get(str(item.get("severity", "info")).lower(), Severity.INFO)
            findings.append(Finding(
                analyzer=self.name,
                severity=severity,
                category=item.get("category", "design"),
                message=item.get("message", "").strip(),
                line=item.get("line"),
                suggestion=item.get("suggestion"),
            ))
        return findings