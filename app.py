"""
app.py  —  Flask application factory for Interview Trainer Agent.

Routes
------
GET  /           → Landing page (input form)
POST /generate   → Accepts multipart form; returns JSON prep kit
GET  /health     → Simple liveness check for deployment platforms
"""

import io
import os
import pathlib
import sys

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
load_dotenv()

from src.agent import generate_prep_kit  # noqa: E402  (after sys.path insert)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")

    # ── Landing page ──────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return render_template("index.html")

    # ── Generation endpoint ───────────────────────────────────────────────────
    @app.route("/generate", methods=["POST"])
    def generate():
        """
        Accepts multipart/form-data:
          candidate_name, target_role, experience_level, top_k, resume (file)
        Returns JSON: { status, kit, profile }  or  { status, type, message }
        """
        name  = request.form.get("candidate_name", "").strip()
        role  = request.form.get("target_role", "").strip()
        level = request.form.get("experience_level", "").strip()
        top_k = int(request.form.get("top_k", 5))

        file_obj = None
        if "resume" in request.files and request.files["resume"].filename:
            file_obj = io.BytesIO(request.files["resume"].read())

        try:
            kit = generate_prep_kit(
                candidate_name=name,
                target_role=role,
                experience_level=level,
                uploaded_file=file_obj,
                top_k=top_k,
            )
            return jsonify({
                "status":  "ok",
                "kit":     kit,
                "profile": {"name": name, "role": role, "level": level},
            })

        except EnvironmentError as exc:
            return jsonify({
                "status":  "error",
                "type":    "credentials",
                "message": str(exc),
            }), 500

        except RuntimeError as exc:
            etype = "no_kb" if "Vector store" in str(exc) else "generation"
            return jsonify({
                "status":  "error",
                "type":    etype,
                "message": str(exc),
            }), 500

        except Exception as exc:
            return jsonify({
                "status":  "error",
                "type":    "unknown",
                "message": str(exc),
            }), 500

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
