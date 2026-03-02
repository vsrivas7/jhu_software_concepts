"""Flask application factory for the GradCafe web app."""
import os
from flask import Flask, jsonify, render_template_string
from publisher import publish_task

ANALYSIS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Analysis</title></head>
<body>
    <h1>Analysis</h1>
    <button onclick="fetch('/pull-data',{method:'POST'}).then(()=>alert('Queued!'))" data-testid="pull-data-btn">Pull Data</button>
    <button onclick="fetch('/update-analysis',{method:'POST'}).then(()=>alert('Queued!'))" data-testid="update-analysis-btn">Update Analysis</button>
    {% for key, value in data.items() %}<div><strong>{{ key }}</strong><p>{{ value }}</p></div>{% endfor %}
</body>
</html>
"""

def create_app(config=None):
    """Flask app factory."""
    app = Flask(__name__)
    app.config.update({"DATABASE_URL": os.getenv("DATABASE_URL")})
    if config:
        app.config.update(config)

    @app.route("/analysis", methods=["GET"])
    def analysis():
        """Render the analysis page."""
        return render_template_string(ANALYSIS_TEMPLATE, data={}), 200

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """Queue a scrape task."""
        try:
            publish_task("scrape_new_data")
            return jsonify({"queued": True}), 202
        except Exception:  # pylint: disable=broad-except
            return jsonify({"ok": False}), 503

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """Queue an analytics recompute task."""
        try:
            publish_task("recompute_analytics")
            return jsonify({"queued": True}), 202
        except Exception:  # pylint: disable=broad-except
            return jsonify({"ok": False}), 503

    return app

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=8080)
