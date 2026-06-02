#!/usr/bin/env python3
import heapq
import sys

current_ip = None
current_count = 0
top = []


def push_ip(ip, count):
    item = (count, ip)
    if len(top) < 20:
        heapq.heappush(top, item)
    elif item > top[0]:
        heapq.heapreplace(top, item)


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 2:
        continue

    ip, count_text = parts
    try:
        count = int(count_text)
    except ValueError:
        continue

    if current_ip is None:
        current_ip = ip
        current_count = count
    elif ip == current_ip:
        current_count += count
    else:
        push_ip(current_ip, current_count)
        current_ip = ip
        current_count = count

if current_ip is not None:
    push_ip(current_ip, current_count)

for count, ip in sorted(top, key=lambda item: (-item[0], item[1])):
    print(f"{ip}\t{count}")
