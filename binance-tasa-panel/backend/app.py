import csv
import io
import json
import os
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, render_template, request, Response
from flask_cors import CORS

from config import (
    API_ADMIN_TOKEN,
    BASE_DIR,
    CORS_ORIGINS,
    DATA_FILE,
    FLASK_HOST,
    FLASK_PORT,
    INTERNAL_UPDATE_KEY,
    MAX_HISTORY_ENTRIES,
    TOKENS_FILE,
)

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "frontend"),
    static_folder=str(BASE_DIR / "frontend"),
)
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})


def leer_historial():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def guardar_historial(historial):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)


def cargar_tokens():
    if not TOKENS_FILE.exists():
        return {}
    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def token_info(token_recibido):
    if not token_recibido:
        return None
    if API_ADMIN_TOKEN and token_recibido == API_ADMIN_TOKEN:
        return {"email": "admin", "active": True, "role": "admin"}
    tokens = cargar_tokens()
    info = tokens.get(token_recibido)
    if info and info.get("active", False):
        if "role" not in info:
            info = {**info, "role": "user"}
        return info
    return None


def requiere_token(roles=None):
    roles = roles or {"user", "admin"}

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            token = request.headers.get("x-token")
            info = token_info(token)
            if not info or info.get("role", "user") not in roles:
                return jsonify({"error": "Token inválido o sin permisos"}), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator


def enriquecer_registro(registro):
    binance = float(registro["binance"])
    bcv = float(registro["bcv"])
    brecha = round(binance - bcv, 4)
    brecha_pct = round((brecha / bcv) * 100, 2) if bcv else 0
    return {
        **registro,
        "brecha": brecha,
        "brecha_pct": brecha_pct,
    }


def historial_a_csv(historial):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["fecha", "binance", "bcv", "brecha", "brecha_pct"])
    for row in historial:
        enriched = enriquecer_registro(row)
        writer.writerow([
            enriched["fecha"],
            enriched["binance"],
            enriched["bcv"],
            enriched["brecha"],
            enriched["brecha_pct"],
        ])
    return output.getvalue()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    historial = leer_historial()
    ultimo = historial[-1] if historial else None
    return jsonify({
        "status": "ok",
        "registros": len(historial),
        "ultima_actualizacion": ultimo["fecha"] if ultimo else None,
    })


@app.route("/api/tasa", methods=["GET"])
@requiere_token(roles={"user", "admin"})
def get_tasa():
    historial = leer_historial()
    if not historial:
        return jsonify({"error": "No hay datos disponibles"}), 404
    return jsonify(enriquecer_registro(historial[-1]))


@app.route("/api/history", methods=["GET"])
@requiere_token(roles={"admin"})
def get_history():
    historial = leer_historial()
    return jsonify([enriquecer_registro(r) for r in historial])


@app.route("/api/history/export", methods=["GET"])
@requiere_token(roles={"admin"})
def export_history():
    historial = leer_historial()
    if not historial:
        return jsonify({"error": "No hay datos para exportar"}), 404

    csv_data = historial_a_csv(historial)
    filename = f"tasas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/api/update", methods=["POST"])
def update_tasa():
    internal_key = request.headers.get("x-internal-key")
    if not INTERNAL_UPDATE_KEY or internal_key != INTERNAL_UPDATE_KEY:
        return jsonify({"error": "Firma no autorizada"}), 403

    data = request.get_json(silent=True)
    if not data or "binance" not in data or "bcv" not in data:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        binance = float(data["binance"])
        bcv = float(data["bcv"])
    except (TypeError, ValueError):
        return jsonify({"error": "Precios inválidos"}), 400

    historial = leer_historial()
    historial.append({
        "binance": binance,
        "bcv": bcv,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    historial = historial[-MAX_HISTORY_ENTRIES:]

    try:
        guardar_historial(historial)
        return jsonify({"status": "success", "registros": len(historial)})
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/web/tasa", methods=["GET"])
def web_tasa():
    historial = leer_historial()
    if not historial:
        return jsonify({"error": "No hay datos disponibles"}), 404
    return jsonify(enriquecer_registro(historial[-1]))


@app.route("/api/web/history", methods=["GET"])
def web_history():
    historial = leer_historial()
    return jsonify([enriquecer_registro(r) for r in historial])


@app.route("/api/web/export/csv", methods=["GET"])
def web_export_csv():
    historial = leer_historial()
    if not historial:
        return jsonify({"error": "No hay datos para exportar"}), 404

    csv_data = historial_a_csv(historial)
    filename = f"tasas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    # Desarrollo local: python app.py
    # Docker/producción: gunicorn (ver Dockerfile)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)
