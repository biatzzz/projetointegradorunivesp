## Purpose
Make concise, codebase-specific instructions to help AI coding agents be immediately productive in this Flask + SQLAlchemy app.

## Big picture
- This is a small monolithic Flask web app. The HTTP routes live in `app.py`. Templates are in `templates/` and static assets in `static/`.
- Data layer uses SQLAlchemy ORM models in `db.py` with a local SQLite engine `sqlite:///banco.db`. Models, many-to-many association tables, and enums live in `db.py`.
- Business logic is organized into per-entity CRUD modules under `crud/` (e.g. `crud/aluno_crud.py`, `crud/curso_crud.py`). Routes call these CRUD functions passing an active SQLAlchemy Session.

## How to run locally (discovered from code)
- The app starts by running `app.py` — main block calls `app.run(debug=True)`.
- The DB engine is `create_engine("sqlite:///banco.db", echo=True)` defined in `db.py`. Running `db.py` directly will create tables and seed reference data when executed as `__main__`.

Example: (run from repository root)
```ps1
# Windows PowerShell (project root)
python .\app.py
```

## Key patterns and conventions (project-specific)
- Session usage: routes always create a Session via `with Session(db.engine) as session:` and pass that session to `crud` functions. Preserve this pattern to avoid session/DetachedInstanceError issues.
- Error signaling from CRUD: many `crud/*.py` functions return either a model object or a dict like `{"erro": "message"}`. Routes check `isinstance(resultado, dict)` to detect and propagate errors. When editing or adding new CRUD functions follow this convention.
- Eager-loading: CRUD functions often use `selectinload(...)` to load relationships before templates access them (see `crud/aluno_crud.buscar_alunos`). Prefer using SQLAlchemy loading options where templates require related objects.
- Form conversions: `app.py` provides `to_date()` and `to_int()` helper functions and maps form field names to model attributes (e.g., `nome` -> `nomeProfessor` in professor creation). Prefer reusing or mirror these helpers when adding new form handlers.
- Templates expect certain attributes on model instances (e.g., `aluno.nome`, `aluno.id_Aluno`, or `turma.alunos`); maintain attribute names defined in `db.py` to avoid breaking templates.

## Files to inspect for examples
- `app.py` — Routing, form parsing, conversions, patterns for GET/POST flows and redirects (common flow used across entities).
- `db.py` — All models, association tables (`curso_turma`, `curso_aluno`), enums, engine creation, and seeding script in `__main__`.
- `crud/*.py` — Each file shows how to implement create/read/update/delete using Session objects and the return conventions.

## Common change patterns and gotchas
- When modifying models: update `db.Base.metadata.create_all(engine)` usage and review `crud/` functions for fields/relationship names used in queries and templates.
- Avoid returning raw SQLAlchemy objects in JSON responses; the app uses server-rendered templates and passes model instances into templates.
- Keep `sqlite:///banco.db` in mind: schema changes require either migration scripts (not present) or re-creating the DB. There is no Alembic config in repo.

## Development notes for contributors (quick heuristics)
- To add a CRUD entity: add model in `db.py` → create CRUD functions in `crud/` using the same API (Session in argument, return model or {"erro":...}) → add route(s) in `app.py` following the existing GET/POST patterns → add templates in `templates/` and link forms to fields expected by CRUD.
- Use `with Session(db.engine) as session:` consistently. Avoid creating sessions with global scope.

## Example snippets to follow
- Create pattern: `novo = Model(...); session.add(novo); session.commit(); session.refresh(novo); return novo` (see `crud/aluno_crud.cadastrar_aluno`).
- Update pattern: load entity via helper e.g. `buscar_aluno_por_id(session, id)` then set attributes and `session.commit()` (see `crud/aluno_crud.atualizar_aluno`).

## What NOT to change without coordination
- The public attribute names in `db.py` (like `id_Aluno`, `nomeProfessor`) are referenced in templates and CRUD modules — renaming requires coordinated edits across templates and code.
- The session-per-request style in `app.py`. Changing session lifecycle can introduce DetachedInstanceError and other threading/session issues.

## If you need to run tests / CI
- No test suite or CI config found in repo root. If adding tests, prefer small unit tests that create a temporary SQLite memory DB and use the same Session-based API.

## Questions for maintainers (left for the human)
- Do you want migrations (Alembic) added or is re-creating `banco.db` acceptable?
- Are there preferred linting/formatting rules (black/flake8)?

---
If anything above is incorrect or you'd like additional examples (e.g., a full CRUD addition example for a new entity), tell me which part to expand.
