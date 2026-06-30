from apg_automation.main import build_parser, parse_property_names


def test_cli_parser_accepts_local_folder_flag():
    args = build_parser().parse_args(
        ["--local-folder", "Novaliches, 440 Bagbag", "--dry-run"]
    )

    assert args.local_folder == "Novaliches, 440 Bagbag"


def test_cli_parser_accepts_demo_flag():
    args = build_parser().parse_args(["--serve", "--demo"])

    assert args.demo


def test_parse_property_names_uses_local_folder_name_when_properties_are_empty():
    args = build_parser().parse_args(["--local-folder", "Novaliches, 440 Bagbag"])

    assert parse_property_names(args) == ["Novaliches, 440 Bagbag"]
