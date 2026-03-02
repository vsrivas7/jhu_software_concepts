"""
Flask application factory for the GradCafe web app.
Supports dependency injection for testing.
"""

import os

from flask import Flask, jsonify, render_template_string

from . import load_data, query_data, scrape

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

ANALYSIS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Analysis</title></head>
<body>
    <h1>Analysis</h1>
    <button data-testid="pull-data-btn">Pull Data</button>
    <button data-testid="update-analysis-btn">Update Analysis</button>
    {% for key, value in data.items() %}
        <div>
            <strong>{{ key }}</strong>
            <p>Answer: {{ value }}</p>
        </div>
    {% endfor %}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(config=None, scraper=None, loader=None, query_fn=None):
    """
    Flask app factory.
    Allows dependency injection for testing.
    """
    app = Flask(__name__)

    app.config.update(
        {
            "BUSY": False,
            "DATABASE_URL": os.getenv("DATABASE_URL"),
        }
    )

    if config:
        app.config.update(config)

    # Dependency injection — fall back to real implementations
    app.scraper = scraper or scrape.scrape_data
    app.loader = loader or load_data.load_rows
    app.query_fn = query_fn or query_data.compute_analysis

    # -----------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------

    @app.route("/analysis", methods=["GET"])
    def analysis():
        """Render the analysis page."""
        data = app.query_fn() or {}
        return render_template_string(ANALYSIS_TEMPLATE, data=data), 200

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """Scrape GradCafe and load results into the database."""
        if app.config["BUSY"]:
            return jsonify({"busy": True}), 409

        try:
            app.config["BUSY"] = True
            rows = app.scraper()
            app.loader(rows)
            return jsonify({"ok": True}), 200
        except Exception:  # pylint: disable=broad-except
            return jsonify({"ok": False}), 500
        finally:
            app.config["BUSY"] = False

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """Re-run the analysis computation."""
        if app.config["BUSY"]:
            return jsonify({"busy": True}), 409

        try:
            app.query_fn()
            return jsonify({"ok": True}), 200
        except Exception:  # pylint: disable=broad-except
            return jsonify({"ok": False}), 500

    return app
