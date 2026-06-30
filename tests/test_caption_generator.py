from apg_automation.caption_generator import CaptionGenerator, validate_caption


class FakeAIClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0)


def test_validate_caption_rejects_emojis_and_forbidden_phrases():
    valid, violations = validate_caption(
        "Bright condo with flexible terms. Negotiables may be discussed."
    )

    assert not valid
    assert "Contains forbidden phrase: 'negotiables'" in violations

    valid, violations = validate_caption("Spacious home near schools 😊")

    assert not valid
    assert "Contains emojis" in violations


def test_caption_generator_retries_until_caption_satisfies_rules():
    client = FakeAIClient(
        [
            "Great unit 😊",
            "Includes negotiables and parking",
            "Bright two-bedroom condo with parking and city access.",
        ]
    )
    generator = CaptionGenerator(client=client, max_retries=3)

    caption = generator.generate("Two-bedroom condo with parking.")

    assert caption == "Bright two-bedroom condo with parking and city access."
    assert len(client.prompts) == 3


def test_caption_generator_requires_manual_review_after_retry_limit():
    client = FakeAIClient(["Nice home 😊", "Still has negotiables"])
    generator = CaptionGenerator(client=client, max_retries=2)

    result = generator.generate("House and lot.")

    assert result.requires_manual_review
    assert "Contains emojis" in result.violations
