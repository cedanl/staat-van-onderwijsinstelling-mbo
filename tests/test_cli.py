import subprocess
import sys
from pathlib import Path

import staat_mbo
from staat_mbo import cli
from staat_mbo.cli import main
from staat_mbo.palet import thema_opties

APP = Path(cli.__file__).parent / "app" / "main.py"


def _vang_subprocess(monkeypatch):
    aanroepen = []

    def nep(cmd, **kwargs):
        aanroepen.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", nep)
    monkeypatch.setattr(cli, "_open_browser", lambda url: aanroepen.append(url))
    return aanroepen


def test_help_toont_commandos_zonder_r(capsys):
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0
    uit = capsys.readouterr().out
    for commando in ("samenvoegen", "staat", "dashboard"):
        assert commando in uit
    assert "Rscript" not in uit and " R)" not in uit and "1CHO" not in uit


def test_dashboard_start_streamlit(monkeypatch):
    aanroepen = _vang_subprocess(monkeypatch)
    assert main(["dashboard", "--poort", "8599", "--geen-browser"]) == 0
    ((cmd, kwargs),) = aanroepen
    assert cmd == [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP),
        "--server.port",
        "8599",
        "--server.headless",
        "true",
        *thema_opties(),
    ]
    assert "STAAT_MBO_INVOER" not in kwargs["env"]


def test_dashboard_met_invoer_zet_de_omgevingsvariabele(monkeypatch, tmp_path):
    aanroepen = _vang_subprocess(monkeypatch)
    main(["dashboard", "--geen-browser", "--invoer", str(tmp_path)])
    ((_cmd, kwargs),) = aanroepen
    assert kwargs["env"]["STAAT_MBO_INVOER"] == str(tmp_path)
    assert kwargs["env"]["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false"


def test_dashboard_opent_de_browser_tenzij_geen_browser(monkeypatch):
    aanroepen = _vang_subprocess(monkeypatch)
    main(["dashboard", "--poort", "8123"])
    assert "http://localhost:8123" in aanroepen
    aanroepen.clear()
    main(["dashboard", "--poort", "8123", "--geen-browser"])
    assert not any(isinstance(a, str) for a in aanroepen)


def test_streamlit_fout_geeft_exitcode_door(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 3)
    )
    assert main(["dashboard", "--geen-browser"]) == 3


def test_geen_r_of_1cho_in_de_broncode():
    bron = Path(staat_mbo.__file__).parent
    for pad in bron.rglob("*"):
        if pad.suffix in (".py", ".R") and pad.is_file():
            tekst = pad.read_text(encoding="utf-8")
            assert "Rscript" not in tekst, pad
            assert "staat1cho" not in tekst, pad
    assert not list(bron.rglob("*.R"))
