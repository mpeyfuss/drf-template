# Scaling & Capacity

This project runs two long-lived services on Railway — **web** (gunicorn) and **worker**
(Celery) — both on the **gevent** async pool. Sizing them correctly means understanding
that "concurrency" is really **two independent dials answering to different limits**, and
that the limit that actually breaks first is almost always the **database connection
budget**, not CPU.

The defaults in `railway.web.toml` / `railway.worker.toml` are a conservative starting
guess, not a proven-correct configuration. Correctness comes from measuring under load
(see [How to know your numbers are right](#how-to-know-your-numbers-are-right)).

## How Railway scaling works

Nothing in the checked-in `railway.*.toml` files configures scaling. There are two
independent axes:

- **Vertical (automatic).** Railway allocates more vCPU/RAM on demand up to your plan's
  cap and bills for usage. You don't configure it. This is why "how many CPUs do I have?"
  is fuzzy on Railway — your share is elastic, not a fixed core count.
- **Horizontal (manual).** A fixed replica count via `numReplicas` in `[deploy]` (or the
  dashboard). This is a static number, **not** request-based autoscaling. Metric-based
  replica autoscaling is a separate, higher-tier dashboard feature and is not used here.

Today every service runs **1 replica**, scaling vertically only. That is a fine starting
point.

## The two dials

| Dial (env var) | Default | What it controls | Scales with |
|----------------|---------|------------------|-------------|
| `WEB_CONCURRENCY` | `2` | gunicorn **worker processes** | **CPU** — process count |
| `WEB_WORKER_CONNECTIONS` | `100` | **greenlets per web process** | I/O concurrency + downstream limits |
| `CELERY_WORKER_CONCURRENCY` | `100` | greenlets in the (single) Celery process | I/O concurrency + downstream limits |
| `DATABASE_POOL_MAX_SIZE` | `4` | DB connections **per process** | Postgres `max_connections` |

The critical distinction:

- **Process count is the CPU dial.** Python's GIL means one process saturates roughly one
  core, so `WEB_CONCURRENCY` should track your allocated vCPUs. This is the number to raise
  when CPU-bound.
- **Greenlet count is _not_ a CPU number.** Under gevent, one process cooperatively juggles
  many I/O-bound requests. The `100`s are "how many I/O waits can be in flight per process."
  100 concurrent network waits on a single core is normal and healthy for async work — but
  it is unmoored from the resource that actually runs out first (DB connections).

## Why gevent changes the math

With **sync** workers the classic formula is `workers = 2 × CPU + 1`, because each process
serves one request at a time and you need extras to cover I/O stalls.

With **gevent**, each process serves many requests concurrently via greenlets, so you run
*fewer processes, each with high connection counts*. Total in-flight capacity is:

```
web:    WEB_CONCURRENCY × WEB_WORKER_CONNECTIONS   = 2 × 100 = 200
celery: 1 process       × CELERY_WORKER_CONCURRENCY = 1 × 100 = 100
```

Those are I/O fan-out ceilings, not throughput guarantees.

## The binding constraint: database connections

Every greenlet that touches the database needs a pooled connection. The pool is capped
**per process** at `DATABASE_POOL_MAX_SIZE`:

```
web DB connections    = WEB_CONCURRENCY × DATABASE_POOL_MAX_SIZE = 2 × 4 = 8
celery DB connections = 1 process       × DATABASE_POOL_MAX_SIZE = 1 × 4 = 4
                        + Django admin, one-off shells, migrations, monitoring
```

So although 200 web greenlets can exist, only **8** can hold a DB connection at once. The
rest **queue on the pool** for up to `DATABASE_POOL_TIMEOUT` (10s), then raise. This is not
a bug — the pool is protecting Postgres — but it means:

- For **DB-bound** requests, real serving capacity ≈ the pool size, and extra greenlets just
  wait. Raise `DATABASE_POOL_MAX_SIZE` (if the DB has headroom), not the greenlet count.
- For **non-DB I/O** (Mailgun, external APIs, Redis), high greenlet counts are genuinely
  useful and don't touch this budget.

### The inequality you must never violate

```
WEB_CONCURRENCY × DATABASE_POOL_MAX_SIZE
  + (celery processes) × DATABASE_POOL_MAX_SIZE
  + headroom (admin, one-off commands, migrations, monitoring)
  ≤  Postgres max_connections
```

Railway's starter Postgres has a modest `max_connections` — check your plan; that number
is your true ceiling. Every time you raise `WEB_CONCURRENCY`, `DATABASE_POOL_MAX_SIZE`, or
add a replica, re-check this inequality. **Replicas multiply it**: two web replicas at
`WEB_CONCURRENCY=2`, `POOL_MAX_SIZE=4` is `2 × 2 × 4 = 16` web connections, not 8.

## The Railway CPU gotcha

**Do not auto-derive workers from `multiprocessing.cpu_count()` / `nproc`.** Inside the
container these report the **host machine's** core count (often 32+), not your allocated
share. `WEB_CONCURRENCY = 2 × cpu_count() + 1` would spawn dozens of processes and blow past
both memory and the connection budget. That is exactly why the config hardcodes a default of
`2` and expects you to set `WEB_CONCURRENCY` explicitly per environment. Keep it that way.

## How to know your numbers are right

Defaults are a guess. Correctness comes from watching four signals under realistic load and
tuning **one dial at a time**:

1. **CPU utilization** (per service) — pinned at 100% with requests queuing → raise
   `WEB_CONCURRENCY` or add a replica. Mostly idle → you have too many processes.
2. **Memory** — `processes × per-process RSS` must stay under the service memory limit. This
   is the hard cap on how high `WEB_CONCURRENCY` can go.
3. **Postgres active connections** — `SELECT count(*) FROM pg_stat_activity;` vs
   `max_connections`. This caps `WEB_CONCURRENCY × POOL_MAX_SIZE` (+ celery + headroom).
4. **Pool wait time / request latency** — if greenlets spend time blocked near
   `DATABASE_POOL_TIMEOUT`, the **pool** is the bottleneck, not greenlets or CPU. Raise
   `DATABASE_POOL_MAX_SIZE` if the DB has connection headroom.

### A sane tuning procedure

1. Start at the defaults (`WEB_CONCURRENCY=2`, connections `100`, pool `4`).
2. Load-test with production-like traffic (realistic DB vs external-I/O mix).
3. Read the four signals above; identify the *first* bottleneck.
4. Adjust the single dial that addresses it, re-check the connection inequality, retest.
5. Only scale horizontally (`numReplicas`) once a single instance is CPU- or memory-bound,
   and remember replicas multiply the connection budget.

## Celery Beat (when you add it)

If you add periodic tasks, run **beat as its own service pinned to a single instance**
(`numReplicas = 1`) and never autoscale it — multiple beat processes schedule every task
more than once. Beat is the one service that must never be scaled horizontally.

## Quick reference

| Env var | Default | Raise when… | Watch out for |
|---------|---------|-------------|---------------|
| `WEB_CONCURRENCY` | `2` | CPU-bound, requests queuing | memory limit; DB connection budget |
| `WEB_WORKER_CONNECTIONS` | `100` | non-DB I/O fan-out needs more headroom | pointless past pool size for DB-bound work |
| `CELERY_WORKER_CONCURRENCY` | `100` | tasks are I/O-bound and waiting | DB connection budget for DB-heavy tasks |
| `DATABASE_POOL_MAX_SIZE` | `4` | pool wait time high **and** DB has headroom | `max_connections` ceiling (× processes × replicas) |
| `numReplicas` | `1` | single instance is CPU/memory-bound | multiplies the entire connection budget |
