#!/usr/bin/env python3
"""
US Macro Dashboard — data updater.

Fetches all required FRED series and rewrites dashboard.html with the latest data.

Usage
-----
1. Get a free FRED API key:  https://fred.stlouisfed.org/docs/api/api_key.html
2. Run one of:
       export FRED_API_KEY=your_key_here && python update.py
       python update.py your_key_here

The script reads dashboard_template.html and writes dashboard.html in the same folder.
Open dashboard.html in any browser (double-click) to view.

No external Python packages required — uses stdlib only.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://api.stlouisfed.org/fred/series/observations"

# All FRED series we pull. Order roughly matches dashboard sections.
SERIES = {
    # ---- Treasury yields (Daily) ----
    "DGS1MO":   {"label": "1-Month Treasury",   "category": "treasury",  "units": "%"},
    "DGS3MO":   {"label": "3-Month Treasury",   "category": "treasury",  "units": "%"},
    "DGS6MO":   {"label": "6-Month Treasury",   "category": "treasury",  "units": "%"},
    "DGS1":     {"label": "1-Year Treasury",    "category": "treasury",  "units": "%"},
    "DGS2":     {"label": "2-Year Treasury",    "category": "treasury",  "units": "%"},
    "DGS5":     {"label": "5-Year Treasury",    "category": "treasury",  "units": "%"},
    "DGS10":    {"label": "10-Year Treasury",   "category": "treasury",  "units": "%"},
    "DGS30":    {"label": "30-Year Treasury",   "category": "treasury",  "units": "%"},
    "T10Y2Y":   {"label": "10Y-2Y Spread",      "category": "treasury",  "units": "%"},
    "T10Y3M":   {"label": "10Y-3M Spread",      "category": "treasury",  "units": "%"},
    # ---- GDP (Quarterly) — source: BEA via FRED ----
    "GDPC1":            {"label": "Real GDP (Bn 2017$)",        "category": "gdp", "units": "Bn$"},
    "A191RL1Q225SBEA":  {"label": "Real GDP QoQ ann. (%)",      "category": "gdp", "units": "%"},
    # ---- Inflation (Monthly) — source: BLS / BEA via FRED ----
    "CPIAUCSL": {"label": "CPI (BLS)",           "category": "inflation", "units": "index"},
    "CPILFESL": {"label": "Core CPI (BLS)",      "category": "inflation", "units": "index"},
    "PCEPI":    {"label": "PCE Price Index (BEA)","category": "inflation", "units": "index"},
    "PCEPILFE": {"label": "Core PCE (BEA)",      "category": "inflation", "units": "index"},
    "T10YIE":   {"label": "10Y Breakeven Inflation", "category": "inflation", "units": "%"},
    # ---- Fed liquidity ----
    "WALCL":     {"label": "Fed Total Assets",          "category": "liquidity", "units": "Mn$"},
    "WRESBAL":   {"label": "Reserve Balances",          "category": "liquidity", "units": "Mn$"},
    "RRPONTSYD": {"label": "Overnight Reverse Repo",    "category": "liquidity", "units": "Bn$"},
    "WTREGEN":   {"label": "Treasury General Account",  "category": "liquidity", "units": "Mn$"},
    "M2SL":      {"label": "M2 Money Supply",           "category": "liquidity", "units": "Bn$"},
    "FEDFUNDS":  {"label": "Federal Funds Effective Rate","category": "liquidity", "units": "%"},
    # ---- NBER recession indicator (Monthly, 0/1) ----
    "USREC":     {"label": "NBER Recession",            "category": "recession", "units": "0/1"},
}


def fetch_series(series_id, api_key, start="1960-01-01", retries=2):
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "us-macro-dashboard/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            data = json.loads(raw)
            obs = []
            for o in data.get("observations", []):
                v = o.get("value")
                if v is None or v == "." or v == "":
                    continue
                try:
                    obs.append([o["date"], float(v)])
                except (ValueError, TypeError):
                    continue
            return obs, None
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(1.0 + attempt)
    return [], str(last_err)


def main():
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    if not api_key:
        print("ERROR: FRED API key required.")
        print("  Get a free key:  https://fred.stlouisfed.org/docs/api/api_key.html")
        print("  Then run:        export FRED_API_KEY=your_key && python update.py")
        print("             or:   python update.py your_key")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    template_path = script_dir / "dashboard_template.html"
    output_path = script_dir / "dashboard.html"

    if not template_path.exists():
        print(f"ERROR: template not found at {template_path}")
        sys.exit(1)

    print(f"Fetching {len(SERIES)} series from FRED...")
    series_data = {}
    failures = []
    for sid, meta in SERIES.items():
        line = f"  {sid:18s} {meta['label']:32s}"
        print(line, end="", flush=True)
        obs, err = fetch_series(sid, api_key)
        if err:
            print(f"  FAIL: {err}")
            failures.append((sid, err))
            series_data[sid] = {**meta, "id": sid, "obs": [], "error": err}
        else:
            latest = f"{obs[-1][0]}={obs[-1][1]}" if obs else "(empty)"
            print(f"  OK  {len(obs):>5d} obs  latest: {latest}")
            series_data[sid] = {**meta, "id": sid, "obs": obs}

    payload = {
        "meta": {
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "FRED — Federal Reserve Economic Data, St. Louis Fed",
            "n_series": len(SERIES),
            "n_failed": len(failures),
        },
        "series": series_data,
    }

    template = template_path.read_text(encoding="utf-8")
    placeholder = "/*__DATA__*/{}"
    if placeholder not in template:
        # Fall back to looser match
        if "/*__DATA__*/" not in template:
            print("ERROR: template missing /*__DATA__*/ placeholder")
            sys.exit(1)
        # Replace any /*__DATA__*/<anything-until-next-line> with the new JSON
        import re
        json_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        new_html = re.sub(
            r"/\*__DATA__\*/[^;]*;",
            f"/*__DATA__*/{json_payload};",
            template,
            count=1,
        )
    else:
        json_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        new_html = template.replace(placeholder, f"/*__DATA__*/{json_payload}", 1)

    output_path.write_text(new_html, encoding="utf-8")
    print()
    print(f"Dashboard updated: {output_path}")
    print(f"Open in browser:   file://{output_path}")
    if failures:
        print(f"\n{len(failures)} series failed — dashboard will show partial data for those.")


if __name__ == "__main__":
    main()
