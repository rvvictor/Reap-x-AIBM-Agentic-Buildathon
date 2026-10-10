# Shared-file owners

One writer per shared file. Others ask the owner with `uak msg ID --kind request`. Patterns are relative, with no spaces; directories end in `/`.

| Pattern | Owner task |
|---|---|
| pyproject.toml | HACK-001 |
| uv.lock | HACK-001 |
| package.json | HACK-001 |
| package-lock.json | HACK-001 |
| web/package.json | HACK-001 |
| web/package-lock.json | HACK-001 |
| app/main.py | HACK-001 |
| app/config.py | HACK-001 |
| web/src/App.tsx | HACK-001 |
| web/src/index.css | HACK-001 |
| .github/workflows/ | HACK-001 |
| .env.example | HACK-001 |
| app/schemas/ | HACK-002 |
| web/DESIGN.md | HACK-002 |
| .uak/PROJECT.md | HACK-001 |
