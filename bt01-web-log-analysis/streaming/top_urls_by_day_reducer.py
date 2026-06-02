#!/usr/bin/env python3
import heapq
import sys

current_key = None
current_count = 0
current_day = None
top_for_day = []


def flush_url(day, url, count):
    global current_day, top_for_day

    if current_day is None:
        current_day = day
    elif day != current_day:
        flush_day()
        current_day = day

    item = (count, url)
    if len(top_for_day) < 10:
        heapq.heappush(top_for_day, item)
    elif item > top_for_day[0]:
        heapq.heapreplace(top_for_day, item)


def flush_day():
    global top_for_day

    if current_day is None:
        return
    for count, url in sorted(top_for_day, key=lambda item: (-item[0], item[1])):
        print(f"{current_day}\t{url}\t{count}")
    top_for_day = []


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 3:
        continue

    day, url, count_text = parts
    try:
        count = int(count_text)
    except ValueError:
        continue

    key = (day, url)
    if current_key is None:
        current_key = key
        current_count = count
    elif key == current_key:
        current_count += count
    else:
        flush_url(current_key[0], current_key[1], current_count)
        current_key = key
        current_count = count

if current_key is not None:
    flush_url(current_key[0], current_key[1], current_count)
flush_day()
