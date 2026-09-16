from app.domain.models import Severity, Finding


class ResultAggregator:
    def aggregate(self, findings: list[Finding]) -> tuple[list[Finding], int, dict[str, int]]:
        deduped = self._dedupe(findings)
        deduped.sort(key=lambda f: (f.severity.rank, f.line or 0))
        score = self._score(deduped)
        summary = self._summary(deduped)
        return deduped, score, summary

    @staticmethod
    def _dedupe(findings: list[Finding]) -> list[Finding]:
        seen = set()
        result = []
        for f in findings:
            key = f.dedup_key()
            if key in seen:
                continue
            seen.add(key)
            result.append(f)
        return result

    @staticmethod
    def _score(findings: list[Finding]) -> int:
        penalty = sum(f.severity.weight for f in findings)
        return max(0, 100 - penalty)

    @staticmethod
    def _summary(findings: list[Finding]) -> dict[str, int]:
        summary = {s.value: 0 for s in Severity}
        for f in findings:
            summary[f.severity.value] += 1
        return summary