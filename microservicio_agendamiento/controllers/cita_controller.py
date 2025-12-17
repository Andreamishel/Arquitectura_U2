from flask import Blueprint, request, jsonify
import requests
import pika
import json
from domain.models import Cita, PacienteRef, MedicoRef
from repositories.cita_repository import SQLiteCitaRepository

controller = Blueprint('cita_controller', __name__)
repo = SQLiteCitaRepository()

# --- LÓGICA DE CONEXIÓN AL BROKER ---
def publicar_evento(mensaje):
    try:
        # Conectamos a la capa 'broker' definida en docker-compose
        connection = pika.BlockingConnection(pika.ConnectionParameters('broker'))
        channel = connection.channel()
        channel.queue_declare(queue='cola_notificaciones', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='cola_notificaciones',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2) # Persistente
        )
        connection.close()
        print(f" [x] Evento enviado al Broker: {mensaje['destinatario']}", flush=True)
    except Exception as e:
        print(f" [!] Error Broker: {e}", flush=True)

@controller.route('/agendar', methods=['POST'])
def agendar_cita():
    data = request.json
    try:
        # 1. Validaciones (Mantenemos tu lógica existente)
        # ... (Tu código de request.get a pacientes y medicos) ...
        # simulamos para el ejemplo:
        paciente_ref = PacienteRef(data['pacienteId'], "Paciente Real", "email@test.com", "099123456") 
        medico_ref = MedicoRef(data['medicoId'], "Medico Real", "Especialidad")

        # 2. Reservar Slot (Mantenemos tu lógica)
        requests.patch(f"http://medicos:5002/reservar-slot/{data['slotId']}")

        # 3. Guardar Cita
        nueva_cita = Cita(data['fechaHora'], data['motivo'], paciente_ref, medico_ref)
        nueva_cita.agendar()
        repo.save(nueva_cita)

        # 4. ENVIAR AL BROKER (ASÍNCRONO)
        evento = {
            "citaId": str(nueva_cita.id),
            "pacienteId": str(paciente_ref.id),
            "destinatario": "correo_simulado@test.com", # Usar paciente_ref.email
            "asunto": "Confirmación de Cita",
            "mensaje": f"Su cita con el Dr. {medico_ref.nombre} es el {data['fechaHora']}",
            "tipo": "EMAIL"
        }
        publicar_evento(evento)

        return jsonify({"id": str(nueva_cita.id), "mensaje": "Cita agendada exitosamente"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# ... (Mantener endpoints consultar y anular) ...