from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class HitlDecision:
    requires_approval: bool
    reason: str
    proposed_task: Optional[str] = None


_ACTION_PATTERNS = [
    # 명시적으로 "명령"을 내리라고 하는 경우
    r"(로봇|기기|장치).{0,20}(에게|에)\s*.+?(명령|지시)\s*(하|내리)",
    # 사용자가 로봇에게 말하라는 인용/발화 지시
    r"(로봇|아담|이브|애플).{0,20}(에게|에)\s*[\"“].+?[\"”]\s*(라고|이라)\s*(말하|명령하|지시하)",
    # 한국어 명령형/요청형(문서 매뉴얼 톤)
    r"(하십시오|하시오|하세요)\b",
    r"(실행해|켜줘|꺼줘|눌러|열어|닫아|재부팅|리부팅|초기화)\b",
    # troubleshooting/진단을 실제 수행하라는 경우
    r"(진단|테스트|캘리브레이션|핑\s*테스트|POST).{0,10}(실행|수행)\b",
]

_ACTION_RE = re.compile(
    "|".join(f"(?:{p})" for p in _ACTION_PATTERNS), re.IGNORECASE | re.DOTALL)


def decide_hitl(response_text: str) -> HitlDecision:
    """
    에이전트 응답이 '로봇/장치에 대한 실제 행동'을 유발하는지 간단히 판별합니다.
    - requires_approval=True 이면 Human-in-the-Loop 승인 이후에만 다음 단계(실행/전달)를 진행해야 합니다.
    """
    text = (response_text or "").strip()
    if not text:
        return HitlDecision(False, reason="empty_response")

    if _ACTION_RE.search(text):
        # 제안 task는 일단 전체 응답을 그대로 보관 (노트북에서 승인 UI/로직에 활용)
        return HitlDecision(
            True,
            reason="actionable_robot_command_detected",
            proposed_task=text,
        )

    return HitlDecision(False, reason="no_actionable_command_detected")
