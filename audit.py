#!/usr/bin/env python3
"""Read-only phrase audit of four fixed Jito docs; matches do not prove bugs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


PAGES = (
    ("unstaking_overview", "https://www.jito.network/docs/jitosol/get-started/unstaking-jitosol-flow/unstaking-overview/"),
    ("general_faqs", "https://www.jito.network/docs/jitosol/faqs/general-faqs/"),
    ("technical_faqs", "https://www.jito.network/docs/jitosol/faqs/technical-faqs/"),
    ("glossary", "https://www.jito.network/docs/jitosol/resources/jitosol-glossary/"),
)
MAX_BYTES = 2 * 1024 * 1024
TERMS = {
    "Jupiter": r"\bJupiter\b",
    "DFlow": r"\bDFlow\b",
    "0.1%": r"(?<![\d.])0\.1\s*%",
    "4%": r"(?<![\d.])4\s*%",
    "10 bps": r"\b10\s*bps\b",
    "epoch": r"\bepochs?\b",
    "deactivate": r"\bdeactivat(?:e|ion|ed|ing)\b",
    "withdraw": r"\bwithdraw(?:al|als|able|n|s|ing)?\b",
    "2 days": r"\b2\s+days\b",
    "2-3 days": r"\b2\s*[-–—]\s*3\s+days\b",
    "rewards": r"\brewards?\b",
    "validator commissions": r"\bvalidator\s+commissions?\b",
}


class VisibleTextParser(HTMLParser):
    """Extract static main/article/body text, explicitly labeling any fallback."""

    EXCLUDED = {"script", "style", "noscript", "template", "nav", "aside", "footer", "header", "head"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.title_parts = []
        self.main_parts = []
        self.article_parts = []
        self.body_parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = dict(attrs)
        if tag not in self.VOID:
            self.stack.append((tag, attrs.get("role", "").lower() == "main"))

    def handle_startendtag(self, tag, attrs):
        if tag.lower() not in self.VOID:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag.lower():
                del self.stack[index:]
                break

    def handle_data(self, data):
        tags = {item[0] for item in self.stack}
        if "title" in tags:
            self.title_parts.append(data)
        if tags & self.EXCLUDED:
            return
        if "main" in tags or any(item[1] for item in self.stack):
            self.main_parts.append(data)
        if "article" in tags:
            self.article_parts.append(data)
        if "body" in tags:
            self.body_parts.append(data)

    @staticmethod
    def normalize(parts):
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    def result(self):
        title = self.normalize(self.title_parts)
        for scope, parts in (("main", self.main_parts), ("article_fallback", self.article_parts), ("body_fallback", self.body_parts)):
            content = self.normalize(parts)
            if content:
                return title, content, scope
        return title, "", "no_static_content"


def extract(html):
    parser = VisibleTextParser()
    parser.feed(html)
    parser.close()
    return parser.result()


def count_terms(content):
    return {label: len(re.findall(pattern, content, flags=re.IGNORECASE)) for label, pattern in TERMS.items()}


class RefuseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def inspect_page(opener, page_id, url, timeout):
    result = {
        "id": page_id,
        "url": url,
        "http_status": None,
        "title": None,
        "extraction_scope": None,
        "text_characters": 0,
        "text_sha256": None,
        "phrase_counts": None,
        "error": None,
    }
    request = Request(url, headers={"User-Agent": "JitoDocsQA/1.0 (read-only public documentation review)", "Accept": "text/html", "Accept-Encoding": "identity"}, method="GET")
    try:
        with opener.open(request, timeout=timeout) as response:
            result["http_status"] = response.status
            content_type = response.headers.get_content_type()
            if content_type not in ("text/html", "application/xhtml+xml"):
                raise ValueError("Unexpected content type: " + content_type)
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("Response exceeds the 2 MiB limit; not parsed")
            charset = response.headers.get_content_charset() or "utf-8"
            title, content, scope = extract(raw.decode(charset, errors="replace"))
            result.update(title=title, extraction_scope=scope, text_characters=len(content), text_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(), phrase_counts=count_terms(content))
            if not content:
                result["error"] = "No static main/article/body content was extracted"
    except HTTPError as error:
        result["http_status"] = error.code
        result["error"] = "HTTP " + str(error.code) + ("; redirect refused" if 300 <= error.code < 400 else "")
        error.close()
    except (URLError, TimeoutError, OSError, ValueError, LookupError) as error:
        result["error"] = str(error)
    return result


class ParserTests(unittest.TestCase):
    def test_main_and_title_exclude_navigation_and_scripts(self):
        html = '<html><head><title>Jito &amp; Docs</title><script>Jupiter</script></head><body><nav>Jupiter</nav><main><h1>Fees</h1><p>0.1% &amp; rewards</p><script>DFlow</script><aside>4%</aside><footer>Jupiter</footer></main></body></html>'
        title, content, scope = extract(html)
        self.assertEqual(title, "Jito & Docs")
        self.assertEqual(scope, "main")
        self.assertEqual(content, "Fees 0.1% & rewards")

    def test_article_and_body_fallback_are_labeled(self):
        self.assertEqual(extract('<body>Outside<article>Useful<br>content</article></body>')[1:], ("Useful content", "article_fallback"))
        self.assertEqual(extract('<body><nav>Menu</nav><p>Body text</p></body>')[1:], ("Body text", "body_fallback"))

    def test_role_main_and_void_elements(self):
        self.assertEqual(extract('<body>Outside<div role="main">One<img src="x">Two<input>Three</div></body>')[1:], ("One Two Three", "main"))

    def test_counts_are_case_insensitive_and_numeric_specific(self):
        counts = count_terms("JUPITER Jupiter DFlow 0.1% 10bps 4% 14% 0.4% 2–3 days deactivate deactivation rewards")
        self.assertEqual(counts["Jupiter"], 2)
        self.assertEqual(counts["DFlow"], 1)
        self.assertEqual(counts["4%"], 1)
        self.assertEqual(counts["10 bps"], 1)
        self.assertEqual(counts["2-3 days"], 1)
        self.assertEqual(counts["deactivate"], 2)

    def test_empty_page_has_no_fabricated_content(self):
        self.assertEqual(extract('<html><head><title>Empty</title></head><body><script>text</script></body></html>'), ("Empty", "", "no_static_content"))


def bounded_timeout(value):
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("timeout must be a number") from error
    if not 1 <= seconds <= 30:
        raise argparse.ArgumentTypeError("timeout must be between 1 and 30 seconds")
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("audit-results.json"), help="JSON destination; parent directory must already exist")
    parser.add_argument("--timeout", type=bounded_timeout, default=15.0, help="per-request socket timeout in seconds (1-30; default 15)")
    parser.add_argument("--self-test", action="store_true", help="run offline parser checks only; no HTTP requests or output file")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ParserTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.output.parent.is_dir():
        parser.error("output parent directory does not exist")
    opener = build_opener(RefuseRedirects())
    report = {
        "audit": "jito-docs-static-phrase-audit",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Four fixed public documentation URLs, sequential read-only GETs; no cookies, credentials, retries, or redirects",
        "limitation": "Keyword matches cannot prove a bug, current UI or fee configuration, transaction behavior, or payment eligibility.",
        "timeout_seconds": args.timeout,
        "max_response_bytes": MAX_BYTES,
        "pages": [],
    }
    for page_id, url in PAGES:
        page = inspect_page(opener, page_id, url, args.timeout)
        report["pages"].append(page)
        summary = page["error"] or (str(page["text_characters"]) + " characters; " + page["extraction_scope"])
        print(str(page["http_status"]) + " " + url + " | " + summary, flush=True)
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["successful_pages"] = sum(page["error"] is None for page in report["pages"])
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved " + str(args.output.resolve()))
    return 0 if report["successful_pages"] == len(PAGES) else 1


if __name__ == "__main__":
    sys.exit(main())
