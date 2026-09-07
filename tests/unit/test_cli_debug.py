import importlib
import json

import pytest

main = importlib.import_module("scrape.main")
from scrape.debug import request_get, set_debug


def test_debug_and_no_output_show_only_debug(monkeypatch, capsys):
    monkeypatch.setattr(main, "_dispatch", lambda url: {"url": url, "name": "test"})
    monkeypatch.setattr(
        "sys.argv", ["scrape", "--debug", "--no-output", "https://example.test/product"]
    )

    main.main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[INFO ] cli.start" in captured.err
    assert "[INFO ] cli.complete" in captured.err


def test_debug_keeps_final_json_on_stdout(monkeypatch, capsys):
    monkeypatch.setattr(main, "_dispatch", lambda url: {"url": url})
    monkeypatch.setattr(
        "sys.argv", ["scrape", "--debug", "https://example.test/product"]
    )

    main.main()

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"url": "https://example.test/product"}
    assert "[INFO ] cli.start" in captured.err


def test_http_body_requires_debug(monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["scrape", "--http-body", "https://example.test/product"]
    )

    with pytest.raises(SystemExit, match="2"):
        main.main()


def test_http_body_is_written_to_stderr(capsys):
    class Response:
        status_code = 200
        content = b'{"answer": 42}'
        text = '{"answer": 42}'

    class Requests:
        @staticmethod
        def get(url, **kwargs):
            return Response()

    set_debug(True, http_body=True)
    request_get(Requests(), "https://example.test/api")
    set_debug(False)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[http.body]" in captured.err
    assert '"answer": 42' in captured.err


def test_out_writes_json_to_file_and_stdout(monkeypatch, capsys, tmp_path):
    destination = tmp_path / "product.json"
    monkeypatch.setattr(main, "_dispatch", lambda url: {"url": url})
    monkeypatch.setattr(
        "sys.argv",
        ["scrape", "--out", str(destination), "https://example.test/product"],
    )

    main.main()

    assert json.loads(capsys.readouterr().out) == {
        "url": "https://example.test/product"
    }
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "url": "https://example.test/product"
    }


def test_out_std_tees_terminal_output_to_file(monkeypatch, capsys, tmp_path):
    destination = tmp_path / "product.json"
    monkeypatch.setattr(main, "_dispatch", lambda url: {"url": url})
    monkeypatch.setattr(
        "sys.argv",
        [
            "scrape",
            "--out-std",
            str(destination),
            "https://example.test/product",
        ],
    )

    main.main()

    assert json.loads(capsys.readouterr().out) == {
        "url": "https://example.test/product"
    }
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "url": "https://example.test/product"
    }


def test_no_output_hides_stdout_but_still_writes_out_file(
    monkeypatch, capsys, tmp_path
):
    destination = tmp_path / "product.json"
    monkeypatch.setattr(main, "_dispatch", lambda url: {"url": url})
    monkeypatch.setattr(
        "sys.argv",
        [
            "scrape",
            "--debug",
            "--no-output",
            "--out",
            str(destination),
            "https://example.test/product",
        ],
    )

    main.main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[INFO ] output.file_written" in captured.err
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "url": "https://example.test/product"
    }


def test_out_std_captures_debug_but_no_output_hides_dataset(
    monkeypatch, capsys, tmp_path
):
    destination = tmp_path / "terminal.log"
    monkeypatch.setattr(main, "_dispatch", lambda url: {"url": url})
    monkeypatch.setattr(
        "sys.argv",
        [
            "scrape",
            "--debug",
            "--no-output",
            "--out-std",
            str(destination),
            "https://example.test/product",
        ],
    )

    main.main()

    captured = capsys.readouterr()
    log = destination.read_text(encoding="utf-8")
    assert captured.out == ""
    assert "[INFO ] cli.start" in captured.err
    assert "[INFO ] cli.start" in log
    assert '"url"' not in log
