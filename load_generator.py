"""
Load generator — fires concurrent requests at /checkout so you can
reproduce the incident on demand.

Usage:
    python load_generator.py                # default: 20 workers, 30s
    python load_generator.py --workers 30 --duration 20 --url http://localhost:5000/checkout
"""

import argparse
import time
import threading
import urllib.request
import urllib.error

lock = threading.Lock()
counts = {"success": 0, "failure": 0}


def hit(url, stop_at):
    while time.time() < stop_at:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                resp.read()
                with lock:
                    counts["success"] += 1
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            with lock:
                counts["failure"] += 1
        time.sleep(0.01)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5000/checkout")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--duration", type=int, default=30)
    args = parser.parse_args()

    stop_at = time.time() + args.duration
    threads = [threading.Thread(target=hit, args=(args.url, stop_at)) for _ in range(args.workers)]

    print(f"Firing {args.workers} concurrent workers at {args.url} for {args.duration}s...")
    for t in threads:
        t.start()

    last_print = 0
    while time.time() < stop_at:
        time.sleep(1)
        now = int(time.time() - (stop_at - args.duration))
        if now != last_print:
            with lock:
                print(f"[{now}s] success={counts['success']} failure={counts['failure']}")
            last_print = now

    for t in threads:
        t.join()

    with lock:
        total = counts["success"] + counts["failure"]
        fail_rate = (counts["failure"] / total * 100) if total else 0
        print(f"\nDone. total={total} success={counts['success']} failure={counts['failure']} fail_rate={fail_rate:.1f}%")


if __name__ == "__main__":
    main()
