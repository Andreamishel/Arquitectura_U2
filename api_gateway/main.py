from flask import Flask, request, jsonify
from flask_cors import CORS  
import requests

app = Flask(__name__)
CORS(app) # <--- ESTO PERMITE QUE TU HTML SE CONECTE

# Configuración de URLs (Nombres de servicio en Docker)
URLS = {
    "medicos": "http://medicos:5002",
    "pacientes": "http://pacientes:5003",
    "agendamiento": "http://agendamiento:5001",
    "notificaciones": "http://notificaciones:5004"
}

@app.route('/api/<servicio>/<path:ruta>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def gateway(servicio, ruta):
    if servicio not in URLS:
        return jsonify({"error": "Servicio no encontrado"}), 404

    url_destino = f"{URLS[servicio]}/{ruta}"

    try:
        resp = requests.request(
            method=request.method,
            url=url_destino,
            params=request.args, 
            json=request.get_json() if request.is_json else None
        )
        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"El servicio {servicio} no está disponible"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)