from flask import Blueprint, request, jsonify
from domain.models import ServicioNotificacion
from repositories.notificacion_repository import SQLiteNotificacionRepository

controller = Blueprint('notificacion_controller', __name__)
repo = SQLiteNotificacionRepository()
servicio = ServicioNotificacion(repo)

@controller.route('/enviar', methods=['POST'])
def enviar_notificacion():
    data = request.json
    try:
        # data espera: { citaId, pacienteId, destinatario, asunto, mensaje, tipo }
        
        # 1. Configurar Estrategia (Email o SMS)
        tipo = data.get('tipo', 'EMAIL')
        servicio.preparar_estrategia(tipo)
        
        # 2. Procesar (Dominio)
        notificacion = servicio.procesar_notificacion(data)
        
        return jsonify({
            "id": str(notificacion.id),
            "estado": notificacion.estado.value,
            "mensaje": f"Notificación procesada por {tipo}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500