# Proactive worker

Runs reminder scheduling. Default path uses the in-process scheduler
(also used by the API). Set `TEMPORAL_HOST` in production and wire a Temporal
worker against the same reminder contracts.

```bash
cd apps/api && source .venv/bin/activate
python ../worker/main.py
```
