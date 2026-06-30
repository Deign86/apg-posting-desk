from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .models import CaptionReview

EMOJI_PATTERN = re.compile(
    "["
    "\U0001f1e6-\U0001f1ff"
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\u2600-\u27bf"
    "]+",
    flags=re.UNICODE,
)


class AIClient(Protocol):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class CaptionRules:
    forbidden_phrases: tuple[str, ...] = ("least term", "negotiables", "negotioables")
    max_length: int = 2000


def contains_emojis(text: str) -> bool:
    return bool(EMOJI_PATTERN.search(text))


def validate_caption(
    caption: str,
    rules: CaptionRules | None = None,
) -> tuple[bool, list[str]]:
    active_rules = rules or CaptionRules()
    violations = []

    if contains_emojis(caption):
        violations.append("Contains emojis")

    for phrase in active_rules.forbidden_phrases:
        if phrase.lower() in caption.lower():
            violations.append(f"Contains forbidden phrase: '{phrase}'")

    if len(caption) > active_rules.max_length:
        violations.append(f"Exceeds max length: {active_rules.max_length}")

    return len(violations) == 0, violations


def build_caption_prompt(caption_details: str, rules: CaptionRules) -> str:
    forbidden = ", ".join(f'"{phrase}"' for phrase in rules.forbidden_phrases)
    return f"""Create a professional Facebook post caption for this property listing.

Property Details:
{caption_details}

Requirements:
- Professional and informative tone
- NO emojis whatsoever
- DO NOT use phrases: {forbidden}
- Highlight key features and selling points
- Include relevant property details such as location, size, and price if mentioned
- Keep it concise but compelling, under {rules.max_length} characters

Generate the caption now:"""


class CaptionGenerator:
    def __init__(
        self,
        *,
        client: AIClient,
        max_retries: int = 3,
        rules: CaptionRules | None = None,
    ) -> None:
        self.client = client
        self.max_retries = max_retries
        self.rules = rules or CaptionRules()

    def generate(self, caption_details: str) -> CaptionReview:
        last_caption = ""
        all_violations: list[str] = []

        for _ in range(self.max_retries):
            last_caption = self.client.generate(
                build_caption_prompt(caption_details, self.rules)
            ).strip()
            valid, violations = validate_caption(last_caption, self.rules)
            if valid:
                return CaptionReview(text=last_caption)
            for violation in violations:
                if violation not in all_violations:
                    all_violations.append(violation)

        return CaptionReview(
            text=last_caption,
            violations=all_violations,
            requires_manual_review=True,
        )
