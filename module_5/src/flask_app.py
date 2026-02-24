"""Flask application for Module 5."""

import os
from flask import Flask, jsonify, render_template_string, request
import psycopg

from src import scrape, load_data, query_data
from src.query_data import fetch_all_users
from src.security import clamp_limit


def create_app(config=None, scraper=None, loader=None, query_fn=None):
    """Flask app factory for dependency injection."""

    app = Flask(__name__)

    app.config.update({
        "BUSY": False,
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    })

    if config:
        app.config.update(config)

    app.scraper = scraper or scrape.scrape_data
    app.loader = loader or load_data.load_rows
    app.query_fn = query_fn or query_data.compute_analysis

    @app.route("/users")
    def users():
        """Return users safely with enforced limit."""
        raw_limit = request.args.get("limit", 25)
        safe_limit = clamp_limit(raw_limit)

        try:
            data = fetch_all_users(safe_limit)
            return jsonify(data)
        except psycopg.Error:
            return jsonify({"error": "Database error"}), 500

    @app.route("/analysis", methods=["GET"])
    def analysis():
        """Render analysis page."""
        data = app.query_fn() or {}

        html = """
        <html>
        <head><title>Analysis</title></head>
        <body>
            <h1>Analysis</h1>
            {% for key, value in data.items() %}
                <div>
                    <strong>{{ key }}</strong>
                    <p>Answer: {{ value }}</p>
                </div>
            {% endfor %}
        </body>
        </html>
        """
        return render_template_string(html, data=data), 200

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """Trigger scraping and loading."""
        if app.config["BUSY"]:
            return jsonify({"busy": True}), 409

        try:
            app.config["BUSY"] = True
            rows = app.scraper()
            app.loader(rows)
            return jsonify({"ok": True}), 200
        except psycopg.Error:
            return jsonify({"ok": False}), 500
        finally:
            app.config["BUSY"] = False

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """Recompute analysis."""
        if app.config["BUSY"]:
            return jsonify({"busy": True}), 409

        try:
            app.query_fn()
            return jsonify({"ok": True}), 200
        except psycopg.Error:
            return jsonify({"ok": False}), 500

    return app
