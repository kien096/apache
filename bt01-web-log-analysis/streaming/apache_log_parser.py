#!/usr/bin/env python3
import re
from datetime import datetime

LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+)\s+(?P<url>\S+)\s+(?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)


def parse_apache_combined(line):
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None

    raw_time = match.group("time").split()[0]
    try:
        parsed_time = datetime.strptime(raw_time, "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        return None

    size = match.group("size")
    return {
        "day": parsed_time.strftime("%Y-%m-%d"),
        "hour": parsed_time.strftime("%H"),
        "ip": match.group("ip"),
        "method": match.group("method"),
        "url": match.group("url"),
        "status": match.group("status"),
        "bytes": "0" if size == "-" else size,
    }


def parse_normalized(line):
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 7:
        return None

    return {
        "day": parts[0],
        "hour": parts[1],
        "ip": parts[2],
        "method": parts[3],
        "url": parts[4],
        "status": parts[5],
        "bytes": parts[6],
    }
