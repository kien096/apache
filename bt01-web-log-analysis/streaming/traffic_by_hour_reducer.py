#!/usr/bin/env python3
import sys

current_key = None
current_count = 0


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 3:
        continue

    day, hour, count_text = parts
    try:
        count = int(count_text)
    except ValueError:
        continue

    key = (day, hour)
    if current_key is None:
        current_key = key
        current_count = count
    elif key == current_key:
        current_count += count
    else:
        print(f"{current_key[0]}\t{current_key[1]}\t{current_count}")
        current_key = key
        current_count = count

if current_key is not None:
    print(f"{current_key[0]}\t{current_key[1]}\t{current_count}")
