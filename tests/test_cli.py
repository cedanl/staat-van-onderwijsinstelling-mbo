from staat_mbo.cli import main


def test_help_toont_commandos(capsys):
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0
    uit = capsys.readouterr().out
    for commando in ("samenvoegen", "staat", "dashboard"):
        assert commando in uit
