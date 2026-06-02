#!/usr/bin/env python3
import sys
from apache_log_parser import parse_apache_combined


for line in sys.stdin:
    row = parse_apache_combined(line)
    if not row:
        continue

    print(
        "\t".join(
            [
                row["day"],
                row["hour"],
                row["ip"],
                row["method"],
                row["url"],
                row["status"],
                row["bytes"],
            ]
        )
    )
