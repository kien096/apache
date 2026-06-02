#!/usr/bin/env python3
import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

STATUSES = [200, 200, 200, 200, 200, 301, 302, 404, 404, 500]
METHODS = ["GET", "GET", "GET", "POST", "HEAD"]
URLS = [
    "/",
    "/index.html",
    "/products",
    "/products/laptop",
    "/products/phone",
    "/cart",
    "/checkout",
    "/login",
    "/api/search",
    "/assets/app.css",
    "/assets/app.js",
    "/docs/hadoop",
    "/docs/hive",
    "/docs/mapreduce",
    "/missing-page",
]
AGENTS = [
    "Mozilla/5.0",
    "Chrome/125.0",
    "Safari/605.1.15",
    "curl/8.0",
    "BT01SyntheticBot/1.0",
]


def random_ip():
    # Keep a few hot networks so top-IP results are visible in the dashboard.
    if random.random() < 0.35:
        return f"10.10.{random.randint(1, 8)}.{random.randint(1, 80)}"
    return f"{random.randint(11, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def weighted_time(start, day_offset):
    base = start + timedelta(days=day_offset)
    hour = random.choices(range(24), weights=[2, 1, 1, 1, 2, 3, 5, 8, 11, 12, 13, 12, 10, 9, 10, 12, 14, 16, 15, 11, 8, 6, 4, 3])[0]
    return base.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))


def main():
    parser = argparse.ArgumentParser(description="Generate Apache Combined Log files for BT01.")
    parser.add_argument("--lines", type=int, default=2_000_000)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--start-date", default="2026-06-01")
    parser.add_argument("--out", default="data/raw")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    for old_file in out_root.rglob("*.log"):
        old_file.unlink()

    handles = {}
    try:
        for i in range(args.lines):
            day_offset = i % args.days
            ts = weighted_time(start, day_offset)
            rel_dir = Path(ts.strftime("%Y/%m/%d"))
            log_dir = out_root / rel_dir
            log_dir.mkdir(parents=True, exist_ok=True)
            path = log_dir / "access.log"

            if path not in handles:
                handles[path] = path.open("w", encoding="utf-8")

            ip = random_ip()
            method = random.choice(METHODS)
            url = random.choice(URLS)
            status = random.choice(STATUSES)
            size = "-" if status == 404 else str(random.randint(300, 180000))
            agent = random.choice(AGENTS)
            line = (
                f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S")} +0700] '
                f'"{method} {url} HTTP/1.1" {status} {size} '
                f'"-" "{agent}"\n'
            )
            handles[path].write(line)

            if (i + 1) % 100000 == 0:
                print(f"Generated {i + 1:,} lines")
    finally:
        for handle in handles.values():
            handle.close()

    print(f"Done. Logs are under {out_root.resolve()}")


if __name__ == "__main__":
    main()
