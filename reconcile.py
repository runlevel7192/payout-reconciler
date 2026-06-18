#!/usr/bin/env python3
"""Reconcile daily payout batches against the custody ledger.

Runs as a nightly cron. Discrepancies above tolerance are written to
out/discrepancies.csv for manual review the next morning.
"""
import argparse
import csv
import json
import os
import sys
from datetime import date

import requests

CONFIG_PATH = os.environ.get("RECONCILE_CONFIG", "config.json")
TOLERANCE = 0.01  # currency units


def load_config(path=CONFIG_PATH):
    with open(path) as fh:
        return json.load(fh)


def _session(cfg):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {cfg['api_key']}"})
    return s


def fetch_payouts(cfg, sess, day):
    r = sess.get(f"{cfg['base_url']}/payouts", params={"date": day}, timeout=20)
    r.raise_for_status()
    return r.json().get("payouts", [])


def fetch_ledger(cfg, sess, day):
    r = sess.get(f"{cfg['base_url']}/custody/ledger", params={"date": day}, timeout=20)
    r.raise_for_status()
    return r.json().get("entries", [])


def reconcile(payouts, ledger):
    ledger_by_ref = {e["ref"]: e for e in ledger}
    out = []
    for p in payouts:
        entry = ledger_by_ref.get(p["ref"])
        if entry is None:
            out.append((p["ref"], p["amount"], "MISSING_IN_LEDGER"))
        elif abs(entry["amount"] - p["amount"]) > TOLERANCE:
            out.append((p["ref"], p["amount"], f"MISMATCH:{entry['amount']}"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", default=date.today().isoformat())
    args = ap.parse_args(argv)

    cfg = load_config()
    sess = _session(cfg)
    payouts = fetch_payouts(cfg, sess, args.date)
    ledger = fetch_ledger(cfg, sess, args.date)
    discrepancies = reconcile(payouts, ledger)

    os.makedirs("out", exist_ok=True)
    with open("out/discrepancies.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "amount", "status"])
        w.writerows(discrepancies)

    print(f"{len(payouts)} payouts, {len(ledger)} ledger entries, "
          f"{len(discrepancies)} discrepancies -> out/discrepancies.csv")
    return 1 if discrepancies else 0


if __name__ == "__main__":
    sys.exit(main())
