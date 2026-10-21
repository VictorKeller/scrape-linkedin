# Public LinkedIn job reader

Standalone experiment, separate from the job-search pipeline. Requires Python
3.10+ standard library only; no packages, browser driver, login or cookies.

Run in PowerShell from this folder:

```powershell
python .\linkedin_scraper.py --limit 10 --remote
```

If `python` opens the Microsoft Store, use the installed Codex runtime:

```powershell
& 'C:\Users\VNFSK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\linkedin_scraper.py --limit 10 --remote
```

`scrape linkedin.py` remains a compatible entry point. Defaults: search for
`analista de dados` in Brazil, one search page, ten successfully validated ads,
five seconds between requests. Options: `--keywords`, `--location`, `--remote`,
`--limit` (1..100), `--max-pages` (1..5), `--delay` (>=3 seconds),
`--output NEW_DIRECTORY`. Search labels are not verified eligibility.

Each run creates `output/<timestamp>/` with:

- `jobs.csv`: UTF-8 BOM CSV for Excel/R, saved after each job.
- `jobs.jsonl`: equivalent records, saved after each job.
- `run.json`: counts, outcome and explicit errors.

The reader uses numeric vacancy IDs, deduplicates within a run, fetches each
vacancy separately and requires its detail page to confirm the expected ID.
Failures are not exported as blank successful jobs. Previous runs and the
historical CSV are preserved. No main-pipeline triage, rating or cross-run
deduplication is included. The old R script targets the historical CSV's dates;
new exports use ISO dates (parse with `as.Date(df$Date)`).

HTTP 401/403/429/999, detected authentication/challenge pages or three detail
failures stop collection. No automatic retries or bypasses. Exit code 0 means
the requested count was collected; 1 means partial, blocked or failed.

LinkedIn prohibits scraping in its policies and can block automated public
access. This reader is not undetectable. A successful test does not guarantee
future availability. Do not use it to bypass login, CAPTCHA or rate limits.

## Live test, 2026-10-19

Requested ten remote Brazil ads. The corrected run saved three complete ads
(Unifacisa, Âmbar Energia and FIT Economia de Energia), then received HTTP 429
on its fifth request and stopped without retrying. Results are in
`output/20261019-102651-241018/`. An earlier single search request exposed a
boolean HTML-attribute parsing error; that error was fixed before this run.
Thus the reader can parse public pages, but reliable ten-ad collection has
not been demonstrated. Four offline parser/identity validation tests passed:
`python -m unittest -v`.
