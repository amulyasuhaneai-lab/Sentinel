"""
Sentinel demo app — "checkout-service"

A tiny Flask API standing in for a real microservice. It has one job
(process a checkout) and one deliberately-breakable dependency
(a DB connection pool).

Endpoints:
  GET  /checkout        -> simulates a checkout request (uses the pool)
  GET  /health           -> basic liveness check
  POST /admin/break-pool -> manually shrink the pool (YOU use this to seed the incident)
  POST /admin/reset-pool -> restore/set the pool size (the AGENT will call this later to "fix" it)
  GET  /admin/pool-status -> see current pool size / in-use count

Run:
    python app.py
Then hit http://localhost:5000/checkout
"""

import time
import logging
from flask import Flask, jsonify, request

from pool import ConnectionPool, ConnectionPoolExhausted

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("checkout-service")

app = Flask(__name__)

DEFAULT_POOL_SIZE = 20
pool = ConnectionPool(size=DEFAULT_POOL_SIZE, checkout_timeout=0.5)

# simple in-memory counters for a quick /admin/pool-status view
stats = {"requests": 0, "successes": 0, "failures": 0}


@app.route("/checkout", methods=["GET"])
def checkout():
    stats["requests"] += 1
    start = time.time()
    try:
        pool.acquire()
        try:
            latency_ms = pool.simulate_query()
            stats["successes"] += 1
            elapsed_ms = round((time.time() - start) * 1000, 1)
            log.info(f"checkout OK - query_latency_ms={latency_ms} total_ms={elapsed_ms} pool_size={pool.size} in_use={pool.in_use}")
            return jsonify({
                "status": "success",
                "message": "Checkout processed",
                "query_latency_ms": latency_ms,
                "total_ms": elapsed_ms,
            }), 200
        finally:
            pool.release()

    except ConnectionPoolExhausted as e:
        stats["failures"] += 1
        elapsed_ms = round((time.time() - start) * 1000, 1)
        log.error(f"checkout FAILED - connection pool exhausted - pool_size={pool.size} in_use={pool.in_use} waited_ms={elapsed_ms}")
        return jsonify({
            "status": "error",
            "message": "connection pool exhausted",
            "total_ms": elapsed_ms,
        }), 503


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/admin/pool-status", methods=["GET"])
def pool_status():
    return jsonify({
        "pool_size": pool.size,
        "in_use": pool.in_use,
        "stats": stats,
    }), 200


@app.route("/admin/break-pool", methods=["POST"])
def break_pool():
    """Manually seed the incident — e.g. {"size": 5}"""
    new_size = int(request.json.get("size", 5)) if request.is_json else 5
    pool.resize(new_size)
    log.warning(f"POOL DELIBERATELY BROKEN - resized to {new_size}")
    return jsonify({"status": "pool resized (broken)", "pool_size": pool.size}), 200


@app.route("/admin/reset-pool", methods=["POST"])
def reset_pool():
    """This is the remediation endpoint the AGENT will call later.
    Defaults back to a healthy size if none is given."""
    new_size = int(request.json.get("size", DEFAULT_POOL_SIZE)) if request.is_json else DEFAULT_POOL_SIZE
    pool.resize(new_size)
    log.info(f"POOL RESET - resized to {new_size}")
    return jsonify({"status": "pool resized (fixed)", "pool_size": pool.size}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
