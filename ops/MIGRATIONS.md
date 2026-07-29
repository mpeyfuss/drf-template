# Migrations Playbook

This project deploys to Railway with **zero-downtime, overlapping deploys**. During any
deploy there is a window where the old code and the new code run against the **same
database at the same time**. Migrations must be written so that both versions of the code
work against whatever schema is live at any instant.

This is not optional discipline — it is the rule that keeps deploys from causing outages.
CI enforces the mechanical parts of it (see [Automated checks](#automated-checks)).

## How a Railway deploy actually sequences

The **web** service owns migrations. Its `preDeployCommand` (`railway.web.toml`) runs
`python manage.py migrate --noinput` in a one-off container **after build, before any new
instance receives traffic**, and aborts the deploy if it fails.

```
1. Build new image
2. preDeployCommand → migrate runs → NEW schema is now live
3. OLD web instances are STILL serving OLD code against the NEW schema
4. NEW instances boot, /health passes, traffic cuts over, OLD instances drain
```

Two consequences you cannot design away:

- **Step 3 overlap.** Old code runs against the new schema for the duration of the
  migration plus the healthcheck window. Every migration must be safe for the *currently
  running* code to execute against.
- **The worker deploys independently** (`railway.worker.toml`, no migrations). Old worker
  code can hit the new schema, and new worker code can briefly hit the old schema, in
  either order. There is no way to order services on Railway.

The answer to both is the same: **expand/contract**.

## The one rule

> Never ship a schema change and the code that depends on it in the same deploy.

Every migration must pass this test:

> *If this migration runs and then the OLD code keeps serving requests for 60 seconds,
> does anything break?*

If yes, the change is not deploy-safe. Split it into multiple deploys.

## Expand / contract

Break any breaking change into separate, independently-deployable steps. Each step is a
merge/deploy that is safe on its own.

| Change | ❌ One deploy | ✅ Expand → migrate → contract |
|--------|--------------|-------------------------------|
| **Add a required (NOT NULL) column** | `AddField(null=False)` | 1. Add `null=True` (or with a DB `default`). 2. Backfill existing rows. 3. Enforce `NOT NULL`. |
| **Rename a column/field** | `AlterField` rename | 1. Add the new column; write to both old and new in code. 2. Backfill new from old. 3. Switch reads to new. 4. Drop old. |
| **Drop a column/field** | Remove field + migration together | 1. Stop referencing it in code; ship and let it go fully live. 2. `RemoveField` in a later deploy. |
| **Change a column type** | `AlterField` type change | New column → dual-write → backfill → switch reads → drop old. |
| **Add NOT NULL + UNIQUE** | In one migration | Add nullable → backfill → add the constraint in a separate migration (see locking notes). |
| **Rename a table/model** | `RenameModel` | Same expand/contract, or keep the old `db_table` and alias. |

Adding a genuinely new, always-nullable column that no old code reads is the one common
change that is safe in a single deploy.

## Postgres locking traps

A migration can be "backward-compatible" and still cause an outage by taking an
`ACCESS EXCLUSIVE` lock on a busy table. The database is Postgres in production
(`ATOMIC_REQUESTS = True`, so each request runs in a transaction — a locked table stalls
live requests).

- **Adding an index** → always build concurrently. Use
  `django.contrib.postgres.operations.AddIndexConcurrently` and set `atomic = False` on the
  migration class (a concurrent build cannot run inside a transaction).
- **Adding NOT NULL to an existing column** → don't let Django do a bare rewrite-scan under
  a lock. Add a `CHECK (col IS NOT NULL) NOT VALID` constraint, `VALIDATE CONSTRAINT` it in
  a separate step (validation takes a weaker lock), then set the column `NOT NULL`.
- **Adding a column with a default** → a *constant* default is a metadata-only change on
  Postgres 11+ and is safe. Avoid per-row/volatile defaults.
- **Long backfills** → never in a migration's `RunPython` on a large table. It holds a
  transaction and blocks the pre-deploy container (Railway will kill a slow pre-deploy).
  Backfill *after* the expand deploy is live, as a management command or Celery task, in
  batches.

## Keep migrations small

`preDeployCommand` applies migrations one at a time. If it dies partway (timeout, bad DDL),
the deploy aborts with the database **partially migrated** and old code still live. Keep
each migration to one concern so every intermediate state is a valid, old-code-safe schema.

## Deploy ordering for a full expand/contract cycle

You cannot enforce web-vs-worker order on Railway, but because each step is written to be
safe against both schema versions, order does not matter for correctness. In practice:

- **Expand steps** (add column/index): deploy web first so the schema leads the code.
- **Contract steps** (drop column): let the code stop using it and go fully live first,
  then deploy the migration that drops it.

## Automated checks

CI (`.github/workflows/ci.yml`, `pytest` job) runs two gates on every PR:

- **`makemigrations --check --dry-run`** — fails if a model changed without a migration, so
  you never deploy code whose migration was forgotten.
- **`lintmigrations`** ([django-migration-linter](https://github.com/3YOURMIND/django-migration-linter))
  — statically flags backward-incompatible operations (dropping columns, adding NOT NULL,
  renames, etc.) on **migrations added since the base branch** (`dev` by default, or the
  branch a PR targets). Already-released migrations are never re-flagged.

Run both locally before pushing:

```bash
make check-migrations   # git fetch origin dev first if it's stale
```

When the linter flags a migration you have deliberately made safe (e.g. you built the index
concurrently, or added the `NOT NULL` as a separate validated step), suppress just that one
migration by adding an `IgnoreMigration` operation to it rather than weakening the gate:

```python
from django_migration_linter import IgnoreMigration


class Migration(migrations.Migration):
    operations = [
        IgnoreMigration(),
        # ... the operations you have verified are safe ...
    ]
```

To silence a specific rule across the whole project instead, pass its code to the command,
e.g. `lintmigrations --exclude-migration-tests NOT_NULL` (rule codes are printed with each
finding).
