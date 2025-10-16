# Tesla Used Inventory Scanner

This project provides a simple command line tool for monitoring Tesla's used Model S inventory.  
It focuses on vehicles that meet the following requirements by default:

- Model year 2023 or newer
- Less than 50,000 miles
- Clean vehicle history (no recorded repairs or accidents)

When a run detects new matching vehicles, a formatted summary is printed to stdout and a price vs. mileage scatter plot is written to `artifacts/price_vs_mileage.png`.

## Setup

1. Create a virtual environment (recommended) and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the scanner once:

```bash
python -m inventory_scanner.cli --zip 94506
```

3. To continuously monitor the inventory (polling every 15 minutes):

```bash
python -m inventory_scanner.cli --zip 94506 --continuous --interval 900
```

Data about previously seen vehicles is stored in `data/known_inventory.json`. Delete this file if you want to reset the history.

## Dealing with `403 Access Denied`

Tesla recently placed its inventory endpoints behind Akamai bot protection.
If you see a `403 Access Denied` error, it means the API request was rejected
because it did not include the same cookies and headers that your browser
receives after completing the bot check. You can forward those values to the
CLI without changing the source code:

1. Open https://www.tesla.com/inventory/used/ms in a real browser and confirm
   you can view inventory results.
2. Copy the full `Cookie` header from the browser's developer tools (look for
   values such as `bm_sz`, `bm_sv`, or `ak_bmsc`).
3. Optionally copy additional headers like `x-tesla-user-agent` that appear on
   the request to `inventory-results`.
4. Pass the captured cookie and extra headers to the CLI:

   ```bash
   python -m inventory_scanner.cli --cookie "bm_sz=...; bm_sv=..." \
       --header "x-tesla-user-agent:TeslaApp/4.32.2-1741"
   ```

The tool now forwards the cookie and header values on every API call. This is
usually enough to satisfy the bot check and eliminate 403 responses. The error
message printed by the CLI also includes the Akamai reference number to help
with debugging.
