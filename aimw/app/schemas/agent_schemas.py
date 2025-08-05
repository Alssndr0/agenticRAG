from typing import List, Optional

from typing_extensions import TypedDict


class CheckResult(TypedDict):
    check_name: str
    passed: bool
    explanation: str


class AgentState(TypedDict):
    document: str
    comparison_document: Optional[str] = ""
    pending_checks: List[str] = []
    current_check: Optional[str] = ""
    check_results: List[CheckResult] = []
    question: Optional[str] = ""
    answer: Optional[str] = ""
