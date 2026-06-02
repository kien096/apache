#!/usr/bin/env python3
import sys
from apache_log_parser import parse_normalized


for line in sys.stdin:
    row = parse_normalized(line)
    if row:
        print(f'{row["day"]}\t{row["status"]}\t1')
