# Storefront-Research - Turkish E-commerce Research

My research about most popular turkish e-commerce platforms. Bundled with a Python web scraper for extracting structured product data from Turkish e-commerce platforms currently **Trendyol**, **Hepsiburada** and **MediaMarkt Türkiye**.

## Overview

Given a product URL from sites, the tool fetches the HTML page, parses embedded structured data (JSON-LD, Redux store state, shared props, Apollo cache), uses **API integrations** to fetch richer product information via each platform's internal storefront APIs, and produces normalized JSON output containing product information.

## The Mindset

Anyone can crawl a page and read it. My question here is how the page was built - and that's what this is about. This is first and foremost a research project, not a polished product or a general-purpose data-mining tool. The emphasis is on understanding how large storefronts structure and expose their data - through embedded structured data (JSON-LD, Redux state), the DOM, and internal JSON APIs - and on documenting those findings in a readable, reusable form. The scraper code is a byproduct of that exploration: it exists to make the research tangible and repeatable. Readability, curiosity, and documentation are prioritized over scale or production robustness. Please check out `docs/wiki` directly or you can use Github Wiki's

## Features

- **Trendyol** (`utils/trendyol/`): extracts product data from JSON-LD, `__envoy__SHARED_PROPS`, and 18+ internal APIs
- **Hepsiburada** (`utils/hepsiburada/`): extracts from JSON-LD, Redux store (`reduxStore`), DOM and PDP APIs
- **MediaMarkt Türkiye** (`utils/mediamarkt/`): extracts from the embedded Apollo cache (`window.__PRELOADED_STATE__` - `apolloState`) plus GraphQL persisted queries
- **Unified CLI**: `scrape <product-url>` - auto-detects platform and dispatches to correct scraper
- **Structured output**: `ProductDataset` dataclass with 16 fields, JSON serialization
- **Description building**: fallback (API > cleaned JSON-LD / embedded state > attribute synthesis)
- **Turkish boilerplate filtering**: 35 common phrases filtered from descriptions

## Quick Start

```bash
# Install dependencies
uv sync

# Scrape a Trendyol product
uv run scrape "https://www.trendyol.com/brand/product-p-id"

# Scrape a Hepsiburada product
uv run scrape "https://www.hepsiburada.com/product-p-id"

# Scrape a MediaMarkt product
uv run scrape "https://www.mediamarkt.com.tr/tr/product/_product-1232522.html"

# Print operation steps to stderr
uv run scrape --debug "https://www.trendyol.com/brand/product-p-id"

# Hide the final JSON, show only debug lines
uv run scrape --debug --no-output "https://www.trendyol.com/brand/product-p-id"

# Hide the final JSON, show only debug lines, include API response bodies
uv run scrape --debug --no-output --http-body "https://www.trendyol.com/brand/product-p-id"

# Write the final JSON to both a file and the terminal
uv run scrape --out product.json "https://www.trendyol.com/brand/product-p-id"

# Write everything shown on the terminal (including debug) to a log file too
uv run scrape --debug --out-std scrape.log "https://www.trendyol.com/brand/product-p-id"
```

`--debug` writes network requests, HTTP statuses, HTML/JSON-LD parsing, dataset building, and API enrichments to stderr. The normal JSON result stays on stdout, so it remains compatible with output redirection. `--no-output` hides only the final JSON result.

`--out FILE` writes the final dataset JSON to both a file and stdout. `--out-std FILE` additionally writes everything that reaches the terminal (stdout, debug, and HTTP body) to a log file. `--no-output` hides the final JSON from stdout; if `--out` is given the JSON is still written to the file. If no output option is given, the result is written to stdout, consistent with prior behavior.

### See `docs/trendyol-example.json`, `docs/hepsiburada-example.json` and `docs/mediamarkt-example.json` for example output.

## Project Structure

```
src/scrape/
├── __init__.py          # CLI entry point (scrape command)
├── main.py              # URL detection, argparse CLI, dispatch logic
├── dataset.py           # ProductDataset dataclass
├── debug.py             # Leveled, colorized debug logging
└── utils/
    ├── trendyol/        # Trendyol scraper (modular)
    │   ├── __init__.py  # Public exports
    │   ├── __main__.py  # Module CLI for debugging
    │   ├── api.py       # Internal API client (18+ endpoints)
    │   ├── builders.py  # VAS, reviews, listing entry builders
    │   ├── common.py    # Shared constants, URL patterns
    │   ├── dataset.py   # Trendyol-specific dataset builders
    │   ├── http.py      # HTTP session, headers, cookies
    │   ├── parsing.py   # HTML/JSON-LD parsing
    │   └── shared_props.py # __envoy__SHARED_PROPS extraction
    ├── hepsiburada/     # Hepsiburada scraper (modular)
    │    ├── __init__.py  # Public exports
    │    ├── __main__.py  # Module CLI for debugging
    │    ├── api.py       # PDP storefront API client
    │    ├── builders.py  # VAS, description, generic builders
    │    ├── dataset.py   # Hepsiburada-specific dataset builders
    │    ├── http.py      # HTTP session, Akamai handling
    │    ├── parsing.py   # HTML/JSON-LD parsing
    │    └── redux.py     # reduxStore extraction (in __init__)
    └── mediamarkt/     # MediaMarkt scraper (modular)
        ├── __init__.py  # Public exports
        ├── __main__.py  # Module CLI for debugging
        ├── builders.py  # Category, price, VAS, custom_data builders
        ├── dataset.py   # MediaMarkt-specific dataset builder
        ├── graphql.py   # Persisted-query GraphQL client (media + loyalty)
        ├── http.py      # HTTP session, Cloudflare cookie warm-up
        └── parsing.py   # HTML / __PRELOADED_STATE__ / apolloState parsing
tests/
├── conftest.py              # Root conftest: markers, fixture helpers
├── helpers/
│   ├── __init__.py
│   ├── _live_helpers.py     # Live URL fetchers for integration parametrization
│   ├── trendyol_fixtures.py # Cached fixture loaders for Trendyol tests
│   ├── hepsiburada_fixtures.py # Cached fixture loaders for Hepsiburada tests
│   └── mediamarkt_fixtures.py  # Cached fixture loaders for MediaMarkt tests
├── fixtures/
│   ├── __init__.py
│   ├── capture_fixtures.py  # One-time script to capture live fixture data
│   ├── trendyol/            # HTML, API responses, expected outputs
│   │   ├── api/             # 18+ captured API responses
│   │   └── expected/        # Expected parsed outputs
│   ├── hepsiburada/         # HTML, redux store, API responses, expected outputs
│   │    ├── api/             # Captured API responses
│   │    └── expected/        # Expected parsed outputs
│   └── mediamarkt/          # HTML, Apollo state, GraphQL responses, expected outputs
├── unit/
│   ├── __init__.py
│   ├── trendyol/
│   │   ├── __init__.py
│   │   ├── test_parsing.py      # HTML parsing, product data, price extraction
│   │   ├── test_shared_props.py # Shared props, category path, custom data
│   │   ├── test_builders.py     # VAS flattening, reviews, listing entry
│   │   ├── test_dataset.py      # ProductDataset JSON serialization
│   │   └── test_helpers.py      # Helper functions (monkeypatched)
│   ├── hepsiburada/
│   │   ├── __init__.py
│   │   ├── test_parsing.py      # HTML parsing, product data, price
│   │   ├── test_redux.py        # Redux store extraction
│   │   ├── test_builders.py     # VAS building, description, generic check
│   │   └── test_product_ctx.py  # Product context, category, availability
│   ├── mediamarkt/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Sets SCRAPE_MEDIAMARKT_GRAPHQL=0 for hermetic tests
│   │   ├── test_parsing.py      # apolloState parsing, availability, breadcrumbs
│   │   └── test_dataset.py      # Full dataset build from cached fixtures
│   ├── test_cli_debug.py        # CLI debug/stdout/stderr behavior
│   └── test_installments.py     # Trendyol installment plan field names
└── integration/
    ├── __init__.py
    ├── conftest.py              # Parametrized live URLs + session fixtures
    ├── trendyol/
    │   ├── __init__.py
    │   ├── test_live_scrape.py  # Parametrized live scrape tests
    │   └── test_live_apis.py    # 18 live Trendyol API tests
    ├── hepsiburada/
        ├── __init__.py
        └── test_live_scrape.py  # Parametrized live scrape tests
    └── mediamarkt/
        ├── __init__.py
        └── test_live_scrape.py  # Parametrized live scrape tests (Cloudflare)
docs/
├── wiki/                       # GitHub Wiki content (auto-published via CI)
│   ├── Home.md                      # Wiki landing page
│   ├── trendyol-README.md           # Trendyol API documentation index
│   ├── trendyol-component_data.md   # Component-read endpoint
│   ├── trendyol-kredi_teklifleri.md # Credit/installment endpoint (external)
│   ├── trendyol-review_read.md      # Reviews + AI summary
│   ├── trendyol-delivery_date.md    # Delivery dates
│   ├── trendyol-installment.md      # Bank installment options
│   ├── trendyol-merchant_questions.md   # Q&A
│   ├── trendyol-seller_acceptance.md    # Seller question acceptance
│   ├── trendyol-slicing_attributes.md   # Variants/colors
│   ├── trendyol-seller_store.md         # Seller store info
│   ├── trendyol-sellerstore_follow.md   # Follower count
│   ├── trendyol-social_proof.md         # Favorites
│   ├── trendyol-video_content.md        # Product videos
│   ├── trendyol-stamps.md               # Badges/stamps
│   ├── trendyol-stickers.md             # Stickers
│   ├── trendyol-currencies.md           # Exchange rates
│   ├── trendyol-product_eligibility.md  # Eligibility
│   ├── trendyol-vas.md                  # Value-added services
│   ├── trendyol-complete_the_look.md    # CTL markers
│   ├── trendyol-description.md          # Product description
│   ├── trendyol-jsonld.md               # JSON-LD structured data
│   ├── trendyol-shared_props.md         # Embedded SHARED_PROPS state
│   ├── hepsiburada-README.md            # Hepsiburada API documentation index
│   ├── hepsiburada-product_listings.md  # Seller listings
│   ├── hepsiburada-without_affordability.md  # Discounted price + campaign
│   ├── hepsiburada-installment.md       # Installment / credit options
│   ├── hepsiburada-other_merchants.md   # Other sellers
│   ├── hepsiburada-payment_options.md   # Payment options
│   ├── hepsiburada-shipping_due_date.md # Shipping delivery date
│   ├── hepsiburada-ask_to_seller.md     # Seller question status
│   ├── hepsiburada-vas.md               # Value-added services
│   ├── hepsiburada-jsonld.md            # HTML-embedded structured data
│   ├── hepsiburada-description.md       # Product description (DOM)
│   ├── hepsiburada-redux_store.md       # Embedded reduxStore state
│   ├── mediamarkt-README.md             # MediaMarkt documentation index
│   ├── mediamarkt-preloaded_state.md    # __PRELOADED_STATE__ / Apollo cache
│   ├── mediamarkt-graphql.md            # GraphQL persisted queries (media + loyalty)
│   └── dataset-schema.md                # Product dataset output schema
├── trendyol-example.json           # Example raw Trendyol output
├── hepsiburada-example.json        # Example raw Hepsiburada output
└── mediamarkt-example.json         # Example raw MediaMarkt output
```

## Requirements

- Python 3.13+
- uv (package manager)
- Dependencies: `requests`, `bs4`, `lxml`
- Dev: `pytest`, `ruff`, `pyright`, `urllib3`

## Testing

Tests are split into **unit** (fixture-based, zero network) and **integration** (live, hits real APIs).

### Unit Tests

You need to create fixtures with tests/fixtures/capture_fixtures.py first to use unit tests.
All unit tests use captured HTML/API fixtures - no internet required
Finishes within 10 seconds.

```bash
uv run pytest                              # Runs unit tests only (default)
uv run pytest tests/unit/ -v               # Explicit unit tests with verbose
uv run pytest tests/unit/trendyol/         # Trendyol unit tests only
uv run pytest tests/unit/hepsiburada/      # Hepsiburada unit tests only
uv run pytest tests/unit/mediamarkt/       # MediaMarkt unit tests only
```

### Integration Tests

Integration tests hit live product pages and APIs (require internet and change, break)
Needs ~4 minutes for all integration tests. (Will fix soon)

```bash
uv run pytest tests/integration/ -v -m integration             # All integration tests
uv run pytest tests/integration/trendyol/ -v -m integration    # Trendyol live tests
uv run pytest tests/integration/hepsiburada/ -v -m integration # Hepsiburada live tests
uv run pytest tests/integration/mediamarkt/ -v -m integration  # MediaMarkt live tests
```

### Fixture Capture

To recapture fixtures (e.g. after API changes):

```bash
uv run python tests/fixtures/capture_fixtures.py
```

This fetches live data once and saves to `tests/fixtures/` for offline unit testing.

## Linting

```bash
uv run ruff check src/ tests/    # Linting
uv run ruff format src/ tests/   # Formatting
uv run pyright src/ tests/       # Type checking
```

## Discovered Storefront APIs

API documentation lives in `docs/wiki/` as flattened, prefixed Markdown pages and is published to the GitHub Wiki automatically on push (see `.github/workflows/publish-wiki.yml`). `docs/wiki/Home.md` links everything together.

**Trendyol** (`docs/wiki/trendyol-*.md`) documents 18 internal endpoints discovered via browser network inspection:

- review-read, component-read, delivery-date, installment, merchant-questions, seller-acceptance, currencies, stickers, video-content, complete-the-look
- slicing-attributes, social-proof, seller-store, sellerstore-follow, stamps, product-eligibility, coc-webview credit endpoint

See `docs/wiki/trendyol-README.md` for the full endpoint list, headers, and accessibility matrix.

**Hepsiburada** (`docs/wiki/hepsiburada-*.md`) documents the PDP storefront APIs and JSON-LD structured data:

- product listings, withoutAffordability (discounted price + campaign), installment, other merchants, payment options, shipping due date, ask-to-seller, VAS

See `docs/wiki/hepsiburada-README.md` for details. For Hepsiburada, Akamai `_abck` protection can be completely bypass, server doesnt check it.

**MediaMarkt Türkiye** (`docs/wiki/mediamarkt-*.md`) is documented differently: the PDP exposes **no JSON-LD** - the core product aggregate (name, brand, price, image, description, features, category, availability, reviews, installments, VA services) lives entirely in the SSR-embedded Apollo cache `window.__PRELOADED_STATE__` - `apolloState`. On top of that, two GraphQL persisted queries (`GET https://www.mediamarkt.com.tr/api/v1/graphql`) return media content and loyalty points. The GraphQL endpoint is served to plain `requests`: a GET with the persisted-query hash, the `pwa` extensions block and the apollo/`x-mms-*`/gateway headers (plus `Content-Type` and `Origin` for the CSRF check) returns `200` - no `curl_cffi` impersonation or browser cookies needed, though the client keeps a best-effort cookie warm-up/retry fallback. Documentation:

- `mediamarkt-README.md` - overview, base URL, common headers, endpoint index
- `mediamarkt-preloaded_state.md` - Apollo cache extraction and schema
- `mediamarkt-graphql.md` - persisted queries, `extensions` blocks, accessibility notes

Example raw output lives at `docs/mediamarkt-example.json`.