import pytest

from apg_automation.config import load_config, validate_runtime_config
from apg_automation.main import build_parser


def test_load_config_reads_yaml_and_environment_overrides(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
ai:
  model: yaml-model
processing:
  min_images: 4
timezone: UTC
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_MODEL", "env-model")

    config = load_config(config_path)

    assert config.ai.model == "env-model"
    assert config.processing.min_images == 4
    assert config.timezone == "UTC"


def test_load_config_defaults_to_nvidia_nim_stepfun_flash(tmp_path):
    config = load_config(tmp_path / "missing.yaml")

    assert config.ai.provider == "nvidia-nim"
    assert config.ai.model == "stepfun-ai/step-3.7-flash"


def test_cli_parser_accepts_properties_file_flag():
    parser = build_parser()
    args = parser.parse_args(["--dry-run", "--properties-file", "properties.txt"])

    assert args.dry_run
    assert args.properties_file == "properties.txt"


def test_runtime_config_validation_requires_nvidia_key_for_caption_generation(monkeypatch):
    config = load_config("missing.yaml")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
        validate_runtime_config(config, dry_run=False)


def test_runtime_config_validation_allows_captionless_dry_run(monkeypatch):
    config = load_config("missing.yaml")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    validate_runtime_config(config, dry_run=True)
