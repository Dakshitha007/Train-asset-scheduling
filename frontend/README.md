# RailOpt AI Streamlit Frontend

The Streamlit app presents live railway asset and optimization data from the
existing FastAPI backend. It does not connect to PostgreSQL directly and
contains no database credentials.

## Run

From the project root, activate the project virtual environment and run:

```powershell
streamlit run frontend/app.py
```

The API base URL defaults to `http://127.0.0.1:8000`. To point the frontend at
another API instance, set `RAILOPT_API_URL` in the frontend process environment.
The frontend makes HTTP requests with a 12-second timeout.

## Pages and API calls

- **Dashboard** — `GET /health`, `GET /dashboard/summary`,
  `GET /dashboard/charts`
- **Railway Assets** — `GET /assets`; supports the API's asset type and zone
  filters, with text search on the loaded page
- **Predictions & Risk** — `GET /assets` and `POST /prediction/batch`
- **Block Planning** — `GET /assets` and `POST /optimization`; displays the
  returned schedule and metrics on the same page
- **System Status** — `GET /health`

Planning availability is the optimizer's scheduled-hours metric, not measured
real-world asset uptime. All charts and dashboard counts are populated from
backend responses rather than frontend sample values.
