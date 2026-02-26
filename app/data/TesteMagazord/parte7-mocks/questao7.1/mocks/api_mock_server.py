from __future__ import annotations

import time
from typing import Any, Dict, List

from flask import Flask, jsonify, request

app = Flask(__name__)

# --- In-memory "database" ---
_products: List[Dict[str, Any]] = [
    {"id": 1, "title": "Product", "price": 100.0, "description": "Mock item", "category": "mock", "image": "https://example.com/p.png"},
    {"id": 2, "title": "Another", "price": 50.5, "description": "Mock item 2", "category": "mock", "image": "https://example.com/p2.png"},
]
_next_id = 3

# --- Rate limit simulation ---
_calls = {"GET_/products": 0}
_RATE_LIMIT_AFTER = 10  # after 10 successful GET /products, return 429


def _maybe_timeout():
    # /products?slow=true -> sleeps 6s
    if request.args.get("slow", "").lower() == "true":
        time.sleep(6)


def _maybe_500():
    # /products?error=500 -> returns 500
    if request.args.get("error") == "500":
        return jsonify({"error": "internal"}), 500
    return None


@app.get("/__health")
def health():
    return jsonify({"ok": True})


@app.post("/__reset")
def reset_state():
    global _products, _next_id, _calls
    _products = [
        {"id": 1, "title": "Product", "price": 100.0, "description": "Mock item", "category": "mock", "image": "https://example.com/p.png"},
        {"id": 2, "title": "Another", "price": 50.5, "description": "Mock item 2", "category": "mock", "image": "https://example.com/p2.png"},
    ]
    _next_id = 3
    _calls = {"GET_/products": 0}
    return jsonify({"reset": True})


@app.get("/products")
def list_products():
    _maybe_timeout()
    maybe = _maybe_500()
    if maybe:
        return maybe

    _calls["GET_/products"] += 1
    if _calls["GET_/products"] > _RATE_LIMIT_AFTER:
        return jsonify({"error": "Rate limit exceeded"}), 429

    return jsonify(_products), 200


@app.post("/products")
def create_product():
    maybe = _maybe_500()
    if maybe:
        return maybe

    global _next_id
    data = request.get_json(silent=True) or {}

    # minimal validation (mock behavior)
    if "title" not in data or "price" not in data:
        return jsonify({"error": "Missing required fields: title, price"}), 400

    created = {
        "id": _next_id,
        "title": data.get("title"),
        "price": float(data.get("price")),
        "description": data.get("description", ""),
        "category": data.get("category", "mock"),
        "image": data.get("image", ""),
    }
    _next_id += 1
    _products.append(created)
    return jsonify(created), 201


@app.put("/products/<int:pid>")
def update_product(pid: int):
    maybe = _maybe_500()
    if maybe:
        return maybe

    data = request.get_json(silent=True) or {}

    for p in _products:
        if p["id"] == pid:
            # update fields if present
            for k in ["title", "price", "description", "category", "image"]:
                if k in data:
                    p[k] = float(data[k]) if k == "price" else data[k]
            return jsonify(p), 200

    return jsonify({"error": "Product not found"}), 404


@app.delete("/products/<int:pid>")
def delete_product(pid: int):
    maybe = _maybe_500()
    if maybe:
        return maybe

    global _products
    before = len(_products)
    _products = [p for p in _products if p["id"] != pid]
    if len(_products) == before:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"deleted": True, "id": pid}), 200


if __name__ == "__main__":
    # fixed port for tests
    app.run(host="127.0.0.1", port=5050)