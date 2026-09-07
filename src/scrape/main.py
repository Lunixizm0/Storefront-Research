import argparse
import json
import os
import sys
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from urllib.parse import urlparse

from scrape.dataset import ProductDataset
from scrape.debug import debug, error, info, set_debug, warn
from scrape.utils.hepsiburada import (
    extract_product_dataset as extract_hepsiburada_dataset,
)
from scrape.utils.hepsiburada import (
    get_raw_html as get_hepsiburada_html,
)
from scrape.utils.trendyol import extract_product_dataset, get_raw_html, parse_html


class _Tee:
    def __init__(self, terminal, file):
        self.terminal = terminal
        self.file = file

    def write(self, text: str) -> int:
        self.terminal.write(text)
        self.file.write(text)
        return len(text)

    def flush(self) -> None:
        self.terminal.flush()
        self.file.flush()


def detect_provider(url: str) -> str:
    hostname = urlparse(url).netloc.lower()
    if "www.trendyol.com" == hostname:
        info("provider.detected", provider="trendyol", hostname=hostname)
        return "trendyol"
    if "www.hepsiburada.com" == hostname:
        info("provider.detected", provider="hepsiburada", hostname=hostname)
        return "hepsiburada"
    error("provider.unsupported", hostname=hostname, url=url)
    raise ValueError(f"Unsupported site: {url}")


def scrape_trendyol(url: str) -> dict:
    info("scrape.start", provider="trendyol", url=url)
    response = get_raw_html(url)
    debug("page.status", provider="trendyol", status=response.status_code)
    if response.status_code != 200:
        raise RuntimeError(f"Trendyol request failed: {response.status_code}")

    soup = parse_html(response.content)
    dataset = extract_product_dataset(soup)
    if dataset is None:
        raise RuntimeError(f"Trendyol product data not found: {url}")

    payload = (
        dataset.to_dict()
        if isinstance(dataset, ProductDataset)
        else json.loads(json.dumps(dataset, ensure_ascii=False))
    )
    info(
        "scrape.complete",
        provider="trendyol",
        populated_fields=sum(value is not None for value in payload.values()),
    )
    return payload


def scrape_hepsiburada(url: str) -> dict:
    info("scrape.start", provider="hepsiburada", url=url)
    response = get_hepsiburada_html(url)
    debug("page.status", provider="hepsiburada", status=response.status_code)
    if response.status_code != 200:
        raise RuntimeError(f"Hepsiburada request failed: {response.status_code}")

    soup = parse_html(response.content)
    dataset = extract_hepsiburada_dataset(soup)
    if dataset is None:
        raise RuntimeError(f"Hepsiburada product data not found: {url}")

    payload = (
        dataset.to_dict()
        if isinstance(dataset, ProductDataset)
        else json.loads(json.dumps(dataset, ensure_ascii=False))
    )
    info(
        "scrape.complete",
        provider="hepsiburada",
        populated_fields=sum(value is not None for value in payload.values()),
    )
    return payload


def _dispatch(url: str) -> dict:
    provider = detect_provider(url)
    info("dispatch", provider=provider)
    if provider == "trendyol":
        return scrape_trendyol(url)
    if provider == "hepsiburada":
        return scrape_hepsiburada(url)
    raise ValueError(f"Unsupported provider: {provider}")


def main() -> None:
    parser = argparse.ArgumentParser(description="URL-based product scraper CLI")
    parser.add_argument("url", help="Product URL to scrape")
    parser.add_argument(
        "--debug", action="store_true", help="Show scraper diagnostics on stderr"
    )
    parser.add_argument(
        "--http-body",
        action="store_true",
        help="Include complete HTTP response bodies in debug output (requires --debug)",
    )
    parser.add_argument("--out", type=Path, help="Write the final JSON to this file")
    parser.add_argument(
        "--out-std",
        type=Path,
        help="Also write everything shown in the terminal to this log file",
    )
    parser.add_argument(
        "--no-output", action="store_true", help="Do not print the final JSON result"
    )
    args = parser.parse_args()
    if args.http_body and not args.debug:
        parser.error("--http-body requires --debug")
    with ExitStack() as stack:
        if args.out_std:
            log_file = stack.enter_context(args.out_std.open("w", encoding="utf-8"))
            stack.enter_context(redirect_stdout(_Tee(sys.stdout, log_file)))
            stack.enter_context(redirect_stderr(_Tee(sys.stderr, log_file)))

        set_debug(args.debug, http_body=args.http_body)
        info(
            "cli.start",
            url=args.url,
            no_output=args.no_output,
            http_body=args.http_body,
            out=str(args.out) if args.out else None,
            out_std=str(args.out_std) if args.out_std else None,
        )

        try:
            if args.no_output:
                with (
                    open(os.devnull, "w", encoding="utf-8") as null_output,
                    redirect_stdout(null_output),
                ):
                    payload = _dispatch(args.url)
            else:
                payload = _dispatch(args.url)
            output = json.dumps(payload, ensure_ascii=False, indent=2)
            if args.out:
                args.out.write_text(f"{output}\n", encoding="utf-8")
                info(
                    "output.file_written",
                    path=str(args.out),
                    bytes=len(output.encode("utf-8")),
                )
            if not args.no_output:
                print(output)
            info(
                "cli.complete",
                stdout_written=not args.no_output,
                dataset_file_written=args.out is not None,
                terminal_log_written=args.out_std is not None,
            )
        except Exception as exc:
            error("cli.error", error=f"{type(exc).__name__}: {exc}")
            raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
