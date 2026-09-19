import json
import sqlite3
from datetime import datetime
from app.domain.models import CodeSubmission, Finding, ReviewResult, Severity



class ReviewRepository:
    def __init__(self,conn:sqlite3.Connection):
        self.conn = conn

    
    def save(self,result:ReviewResult) -> None:
        self.conn.execute(
            """
            INSERT INTO reviews(id,filename,language,code,score,summary_json,findings_json,created_at)
            VALUES(?,?,?,?,?,?,?,?)
            """, 
            (
                result.id,
                result.submission.filename,
                result.submission.language,
                result.submission.code,
                result.score,
                json.dumps(result.summary),
                json.dumps([f.to_dict() for f in result.findings]),
                result.created_at.isoformat(),
            )
        )

        self.conn.commit()

    def get(self,review_id:str) -> ReviewResult | None:
        row = self.conn.execute(
            "SELECT * FROM reviews WHERE id=?",(review_id,)
        ).fetchone()
        return self._row_to_result(row) if row else None

    def list_recent(self, limit: int = 20) -> list[ReviewResult]:
        rows = self.conn.execute(
            "SELECT * FROM reviews ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_result(r) for r in rows]

    @staticmethod
    def _row_to_result(row: sqlite3.Row) -> ReviewResult:
        submission = CodeSubmission(
            code=row["code"], filename=row["filename"], language=row["language"],
        )
        findings = [
            Finding(
                analyzer=f["analyzer"], severity=Severity(f["severity"]),
                category=f["category"], message=f["message"],
                line=f["line"], suggestion=f.get("suggestion"),
            )
            for f in json.loads(row["findings_json"])
        ]
        result = ReviewResult(
            submission=submission, findings=findings, score=row["score"],
            summary=json.loads(row["summary_json"]),
        )
        result.id = row["id"]
        result.created_at = datetime.fromisoformat(row["created_at"])
        return result