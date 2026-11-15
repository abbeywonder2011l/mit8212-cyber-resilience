# Banking Cyber-Resilience Assessment and Planning Prototype

Academic proof of concept for the MIT 8212 seminar (Miva Open University). **All data is fictional.**
"Bank X" is not a real bank. This is not a compliance assessment product.


Live demo: https://mit8212-cyber-resilience.streamlit.app/

## Setup (Windows, Python 3.14)

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the tests

```
.venv\Scripts\python.exe -m pytest
```

## Run the application

```
.venv\Scripts\python.exe -m streamlit run app/main.py
```

On first run the database (`data/bcr.sqlite3`) is created and the demonstration profile is loaded.
Other profiles (B0, SC1 to SC5) can be loaded from the "Data and setup" page.
Set `DATABASE_URL` to use PostgreSQL (for example, Neon); the app reads it from `.env`, `.env.local`,
the process environment, or Streamlit secrets. This takes precedence over `BCR_DB`, which selects a
SQLite database file. Keep database URLs in ignored env files or deployment secrets, never in Git.

## Share a temporary preview with Cloudflare Tunnel

This keeps Streamlit running on your computer and gives it a temporary public URL. It is for
development/demo use; your computer and both terminal processes must remain running. The URL
is public to anyone who has it and changes when the tunnel restarts. Do not put real or sensitive
assessment data in this prototype.

1. Start Streamlit from the project folder: `.venv\\Scripts\\python.exe -m streamlit run app/main.py`.
2. In a second terminal, run `cloudflared tunnel --url http://localhost:8501`.
3. Open the `https://...trycloudflare.com` URL printed by `cloudflared`.

For a stable hostname, create a named Cloudflare Tunnel and configure a published application
route to `http://localhost:8501` in the Cloudflare dashboard. Cloudflare Tunnel provides the
public route; it does not host the Streamlit process or make this local SQLite database durable.

## Layout

| Path | Contents |
|---|---|
| `bcr/engine/` | Logic layer: grades, scoring, gates, gaps, resumption decision. No database or interface imports |
| `bcr/data/` | SQLAlchemy models, repository and seed loader |
| `bcr/reporting/` | HTML report and CSV extracts |
| `bcr/profiles.py` | Builds the synthetic profiles from `data/seed/` |
| `app/` | Streamlit interface |
| `data/control_library.json` | Control catalogue (single source of truth) |
| `tools/build_catalogue.py` | Regenerates `docs/03-control-catalogue.md` |
| `tests/` | Unit, integration and scenario tests |
| `docs/` | Blueprint, framework specification, catalogue, scenarios, requirements |

## Status on 14 November 2026

- 192 automated tests pass (`pytest`), including interface smoke tests of all 13 pages.
- All 13 pages were opened in a browser. Two actions were exercised by hand: saving an assessment entry
  and loading a profile. Other forms (services, assets, risks, exceptions, Tool 2 entry) and the three
  downloads were not exercised by hand; the repository tests cover the writes behind them.
- The application is served on this machine only (`.streamlit/config.toml`).
- Not implemented: login, multiple organisations, in-app catalogue editing, automated evidence collection, PDF export.
