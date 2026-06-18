# payout-reconciler

Nightly reconciliation of payout batches against the custody ledger.

Pulls the day's payouts and the custody service's ledger entries, compares
them, and writes any discrepancies above tolerance to `out/discrepancies.csv`.

## Usage

```
pip install -r requirements.txt
python reconcile.py --date 2026-09-27
```

Operator API access is required — see `config.json`. Keys are per-environment
and should be rotated on offboarding.

## Cron

```
5 2 * * *  cd /srv/payout-reconciler && /usr/bin/python3 reconcile.py >> /var/log/reconcile.log 2>&1
```
