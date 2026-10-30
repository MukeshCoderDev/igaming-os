#!/usr/bin/env python3
"""Generate 10 Django app skeletons under src/noventra/apps/.

Per stage-02-handoff.md §3.1, Phase 3 creates 9 apps from the bounded
contexts + 1 `core` app for the baseline migration. Each app follows
the hexagonal layout (DEC-0002 / ADR-0002):

  <app>/
    __init__.py
    apps.py
    domain/
      __init__.py
      aggregates.py     (empty stub)
      commands.py       (empty stub)
      events.py         (empty stub)
      ports.py          (empty stub)
    adapters/
      __init__.py
      orm.py            (empty stub)
      events.py         (empty stub)
      http.py           (empty stub)
    api/
      __init__.py
      views.py          (empty stub)
      serializers.py    (empty stub)
      urls.py           (empty stub)
    migrations/
      __init__.py

Run:  python3 /home/z/my-project/scripts/generate_app_skeletons.py
"""

from pathlib import Path

APPS_DIR = Path("/home/z/my-project/src/noventra/apps")

# (app_name, app_label, app_verbose_name, owner_role)
APPS = [
    ("core", "core", "Core (platform baseline)", "Architecture Lead"),
    ("tenancy", "tenancy", "Tenancy", "Architecture Lead"),
    ("identity", "identity", "Identity", "Identity Lead"),
    ("audit", "audit", "Audit", "Architecture Lead"),
    ("config", "config", "Configuration", "Infrastructure Lead"),
    ("flags", "flags", "Feature Flags", "Architecture Lead"),
    ("telemetry", "telemetry", "Telemetry", "Infrastructure Lead"),
    ("reliability", "reliability", "Reliability", "Architecture Lead"),
    ("backups", "backups", "Backups & DR", "Operations Lead"),
    ("webhooks", "webhooks", "Webhooks", "Infrastructure Lead"),
]

DOMAIN_STUB = '"""{app} domain — pure domain logic (no infra imports)."""\n'
ADAPTERS_STUB = '"""{app} adapters — infrastructure adapters (DB, HTTP, events)."""\n'
API_STUB = '"""{app} API — DRF views, serializers, URLs (boundary)."""\n'
MIGRATIONS_STUB = ""


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or content:
        path.write_text(content)


def apps_py(app_name: str, app_label: str, verbose_name: str) -> str:
    class_name = "".join(p.capitalize() for p in app_name.split("_")) + "Config"
    return f'''"""{app_name} app configuration."""

from django.apps import AppConfig


class {class_name}(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "noventra.apps.{app_name}"
    label = "{app_label}"
    verbose_name = "{verbose_name}"
'''


def generate_app(app_name: str, app_label: str, verbose_name: str) -> None:
    app_dir = APPS_DIR / app_name
    # __init__.py
    write_file(app_dir / "__init__.py", f'"""{app_name} app — Phase 3 skeleton."""\n')
    # apps.py
    write_file(app_dir / "apps.py", apps_py(app_name, app_label, verbose_name))
    # domain/
    write_file(app_dir / "domain" / "__init__.py", DOMAIN_STUB.format(app=app_name))
    write_file(app_dir / "domain" / "aggregates.py", f'"""{app_name} domain aggregates (Phase 4+)."""\n')
    write_file(app_dir / "domain" / "commands.py", f'"""{app_name} domain commands (Phase 4+)."""\n')
    write_file(app_dir / "domain" / "events.py", f'"""{app_name} domain events (Phase 4+)."""\n')
    write_file(app_dir / "domain" / "ports.py", f'"""{app_name} domain ports (interfaces)."""\n')
    # adapters/
    write_file(app_dir / "adapters" / "__init__.py", ADAPTERS_STUB.format(app=app_name))
    write_file(app_dir / "adapters" / "orm.py", f'"""{app_name} ORM adapter (Phase 4+)."""\n')
    write_file(app_dir / "adapters" / "events.py", f'"""{app_name} event store adapter (Phase 4+)."""\n')
    write_file(app_dir / "adapters" / "http.py", f'"""{app_name} HTTP adapter (Phase 4+)."""\n')
    # api/
    write_file(app_dir / "api" / "__init__.py", API_STUB.format(app=app_name))
    write_file(app_dir / "api" / "views.py", f'"""{app_name} API views (Phase 4+)."""\n')
    write_file(app_dir / "api" / "serializers.py", f'"""{app_name} API serializers (Phase 4+)."""\n')
    write_file(app_dir / "api" / "urls.py", f'"""{app_name} API URLs (Phase 4+)."""\n\nfrom django.urls import path\n\nurlpatterns = []\n')
    # migrations/
    write_file(app_dir / "migrations" / "__init__.py", "")
    print(f"generated app: {app_name}/")


def main():
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    for (name, label, verbose, _owner) in APPS:
        generate_app(name, label, verbose)
    print(f"\n{len(APPS)} app skeletons generated under {APPS_DIR}/")


if __name__ == "__main__":
    main()
