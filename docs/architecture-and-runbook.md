# AIQAHub Architecture and Runbook

## Scope

AIQAHub is a modular-monolith quality assurance control plane. The current MVP covers:

- Project management
- Test suite registry
- Execution orchestration
- Report aggregation
- Quality gate rules and evaluation
- AI analysis entry points
- Asset inventory
- System settings
- Audit logs

## Architecture

### Backend

- `app/main.py` creates the FastAPI app and initializes tables on startup.
- `app/api/v1/routes/` contains thin HTTP endpoints.
- `app/services/` contains business logic.
- `app/crud/` contains reusable repository helpers.
- `app/models/` contains SQLAlchemy models.
- `app/schemas/` contains Pydantic request/response contracts.
- `app/db/seed.py` seeds demo data for local use and tests.

### Frontend

- `frontend/src/App.tsx` owns routing and shell navigation.
- `frontend/src/pages/` contains one page per control-plane domain.
- `frontend/src/lib/api.ts` centralizes HTTP access and shared types.
- `frontend/src/styles.css` defines the dashboard visual system.

## Runtime Flow

1. User opens the UI and logs in.
2. Frontend calls the FastAPI backend with a bearer token.
3. Control-plane pages read projects, suites, executions, reports, rules, and logs.
4. Creating a project, execution, or gate rule writes an audit record.
5. Startup creates tables and seeds demo data so the platform is not empty.

## Local Development

### Backend

```bash
python3 -m pip install -e .
python3 -m app.main
```

### Frontend

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

### Validation

```bash
python3 -m pytest -q
python3 -m compileall app
npm --prefix frontend run build
```

## API Summary

- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{id}`
- `GET /api/v1/suites`
- `GET /api/v1/executions`
- `POST /api/v1/executions`
- `GET /api/v1/executions/{id}`
- `GET /api/v1/executions/{id}/artifacts`
- `GET /api/v1/executions/{id}/timeline`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{execution_id}`
- `GET /api/v1/gates/rules`
- `POST /api/v1/gates/rules`
- `PUT /api/v1/gates/rules/{rule_id}`
- `DELETE /api/v1/gates/rules/{rule_id}`
- `POST /api/v1/gates/evaluate`
- `POST /api/v1/ai/analyze`
- `GET /api/v1/assets`
- `POST /api/v1/assets`
- `GET /api/v1/settings`
- `GET /api/v1/audit`

## Notes

- The app uses SQLite by default via `DATABASE_URL=sqlite:///./aiqahub.db`.
- The demo seed is idempotent.
- The current AI, asset, and reporting logic is intentionally lightweight and can be replaced with real integrations later.
