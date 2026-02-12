"""
scoring.py – Qualification tracking and match-score computation.
"""

from enum import Enum
from config import (
    MANDATORY_QUALIFICATIONS,
    PREFERRED_QUALIFICATIONS,
    TOTAL_MANDATORY_POINTS,
    TOTAL_PREFERRED_POINTS,
    QUALIFICATION_THRESHOLD,
)


class Status(Enum):
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"
    PARTIAL = "Partial"


class QualificationTracker:
    """Tracks candidate qualification statuses and computes scores."""

    def __init__(self):
        self.mandatory = {}
        for q in MANDATORY_QUALIFICATIONS:
            self.mandatory[q["id"]] = {
                "label": q["label"],
                "status": Status.PENDING,
                "evidence": "",
                "weight": q["weight"],
            }

        self.preferred = {}
        for q in PREFERRED_QUALIFICATIONS:
            self.preferred[q["id"]] = {
                "label": q["label"],
                "status": Status.PENDING,
                "evidence": "",
                "weight": q["weight"],
                "detail_score": 0.0,  # 0.0 to 1.0 based on depth of answer
            }

    # ── Updates ─────────────────────────────────────────────────────────

    def update_mandatory(self, qual_id: str, passed: bool, evidence: str = ""):
        """Update a mandatory qualification result."""
        if qual_id in self.mandatory:
            self.mandatory[qual_id]["status"] = Status.PASS if passed else Status.FAIL
            self.mandatory[qual_id]["evidence"] = evidence

    def update_preferred(
        self, qual_id: str, detail_score: float, evidence: str = ""
    ):
        """
        Update a preferred qualification.
        detail_score: 0.0 (no relevant experience) to 1.0 (excellent, detailed answer).
        """
        if qual_id in self.preferred:
            self.preferred[qual_id]["detail_score"] = min(max(detail_score, 0.0), 1.0)
            if detail_score >= 0.7:
                self.preferred[qual_id]["status"] = Status.PASS
            elif detail_score >= 0.3:
                self.preferred[qual_id]["status"] = Status.PARTIAL
            else:
                self.preferred[qual_id]["status"] = Status.FAIL
            self.preferred[qual_id]["evidence"] = evidence

    # ── Scoring ─────────────────────────────────────────────────────────

    def get_mandatory_score(self) -> int:
        score = 0
        for q in self.mandatory.values():
            if q["status"] == Status.PASS:
                score += q["weight"]
        return score

    def get_preferred_score(self) -> float:
        score = 0.0
        for q in self.preferred.values():
            score += q["weight"] * q["detail_score"]
        return round(score, 1)

    def get_total_score(self) -> int:
        return round(self.get_mandatory_score() + self.get_preferred_score())

    def is_disqualified(self) -> bool:
        """True if ANY mandatory qualification has FAILED."""
        return any(
            q["status"] == Status.FAIL for q in self.mandatory.values()
        )

    def all_mandatory_assessed(self) -> bool:
        """True if no mandatory qualifications are PENDING."""
        return all(
            q["status"] != Status.PENDING for q in self.mandatory.values()
        )

    def all_preferred_assessed(self) -> bool:
        """True if no preferred qualifications are PENDING."""
        return all(
            q["status"] != Status.PENDING for q in self.preferred.values()
        )

    # ── Reporting ───────────────────────────────────────────────────────

    def get_decision(self) -> str:
        if self.is_disqualified():
            return "Not Qualified"
        if self.get_total_score() >= QUALIFICATION_THRESHOLD:
            return "Qualified"
        return "Not Qualified"

    def generate_breakdown(self) -> dict:
        """Structured breakdown of all qualifications."""
        return {
            "mandatory": {
                qid: {
                    "label": q["label"],
                    "status": q["status"].value,
                    "evidence": q["evidence"],
                }
                for qid, q in self.mandatory.items()
            },
            "preferred": {
                qid: {
                    "label": q["label"],
                    "status": q["status"].value,
                    "score": round(q["detail_score"] * q["weight"], 1),
                    "evidence": q["evidence"],
                }
                for qid, q in self.preferred.items()
            },
            "mandatory_score": self.get_mandatory_score(),
            "preferred_score": self.get_preferred_score(),
            "total_score": self.get_total_score(),
            "decision": self.get_decision(),
        }

    def generate_summary(self) -> str:
        """Recruiter-friendly summary string."""
        breakdown = self.generate_breakdown()
        lines = []
        lines.append("=" * 50)
        lines.append("  CANDIDATE ASSESSMENT SUMMARY")
        lines.append("=" * 50)
        lines.append("")

        lines.append("MANDATORY QUALIFICATIONS:")
        for qid, q in breakdown["mandatory"].items():
            icon = "✅" if q["status"] == "Pass" else "❌"
            lines.append(f"  {icon} {q['label']}: {q['status']}")
            if q["evidence"]:
                lines.append(f"     → {q['evidence']}")
        lines.append(f"  Mandatory Score: {breakdown['mandatory_score']}/{TOTAL_MANDATORY_POINTS}")
        lines.append("")

        lines.append("PREFERRED QUALIFICATIONS:")
        for qid, q in breakdown["preferred"].items():
            if q["status"] == "Pass":
                icon = "✅"
            elif q["status"] == "Partial":
                icon = "🟡"
            else:
                icon = "⬜"
            lines.append(f"  {icon} {q['label']}: {q['status']} ({q['score']} pts)")
            if q["evidence"]:
                lines.append(f"     → {q['evidence']}")
        lines.append(f"  Preferred Score: {breakdown['preferred_score']}/{TOTAL_PREFERRED_POINTS}")
        lines.append("")

        lines.append(f"TOTAL SCORE: {breakdown['total_score']}/100")
        lines.append(f"DECISION: {breakdown['decision']}")
        lines.append("=" * 50)

        return "\n".join(lines)
