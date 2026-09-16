from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime, timezone


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def weight(self) -> int:
        weights = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 12,
            Severity.MEDIUM: 5,
            Severity.LOW: 2,
            Severity.INFO: 0,
        }
        return weights.get(self, 0)

    @property
    def rank(self) -> int:
        return list(Severity).index(self)


# Define DataClass for Code Submission

@dataclass
class CodeSubmission :
    code: str
    filename: str = "submission.py"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    language: str = "python"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def lines(self) -> list[str]:
      return self.code.splitlines()


# Definig DataClass for Analyzer

@dataclass
class Finding:
    analyzer: str
    severity: Severity
    category: str
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

    
    def dedup_key(self) -> tuple:
        return (self.line,self.category,self.message.strip().lower()[:80])
    
    def to_dict(self) -> dict:
        return {
            "analyzer": self.analyzer,
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "line": self.line,
            "suggestion": self.suggestion
        }
   

# Defining ReviewResults 

@dataclass
class ReviewResult: 
    submission: CodeSubmission
    findings: list[Finding]
    score: int
    summary: dict[str, int]
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


    def to_dict(self) -> dict:
        return{
            "id": self.id,
            "filename": self.submission.filename,
            "language": self.submission.language,
            "score": self.score,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
            "created_at": self.created_at.isoformat()
        }


   
