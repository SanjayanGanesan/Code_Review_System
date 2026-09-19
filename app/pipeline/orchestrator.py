from app.analyzers.base import Analyzer
from app.domain.models import CodeSubmission, Finding, ReviewResult, Severity
from app.pipeline.aggregator import ResultAggregator
from app.storage.repository import ReviewRepository



class ReviewPipeline:
    def __init__ (self,analyzers: list[Analyzer],aggregator: ResultAggregator | None = None,repository: ReviewRepository | None = None):
        self.analyzers = analyzers
        self.aggregator = aggregator or ResultAggregator()
        self.repository = repository

    
    def run(self, submission: CodeSubmission) -> ReviewResult:
        raw_findings: list[Finding] = []
        for analyzer in self.analyzers:
            try:
                 raw_findings.extend(analyzer.analyze(submission))
            except Exception as e:
                 raw_findings.append(Finding(
                   analyzer=getattr(analyzer, "name", "unknown"),
                   severity=Severity.INFO, category="internal",
                    message=f"Analyzer crashed: {e}",
                 ))

        findings, score, summary = self.aggregator.aggregate(raw_findings)
        result = ReviewResult (submission = submission, findings = findings, score = score, summary = summary)

        if self.repository:
            self.repository.save(result)
        
        return result