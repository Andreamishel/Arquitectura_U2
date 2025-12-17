from flask import Blueprint, request, jsonify
import requests
import pika
import json
from domain.models import Cita, PacienteRef, MedicoRef
from repositories.cita_repository import SQLiteCitaRepository

controller = Blueprint('cita_controller', __name__)
repo = SQLiteCitaRepository()

# --- 1. LÓGICA DE CONEXIÓN AL BROKER ---
def publicar_evento(mensaje):
    try:
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
        print(f" [x] Evento enviado al Broker: {mensaje.get('asunto')}", flush=True)
    except Exception as e:
        print(f" [!] Error Broker: {e}", flush=True)

# --- 2. HELPER: CONVERTIR OBJETO A DICCIONARIO JSON ---
def cita_to_dict(c: Cita):
    return {
        "id": str(c.id),
        "fechaHora": c.fechaHora,
        "motivo": c.motivo,
        # .value es importante para obtener el string del Enum (ej: "CONFIRMADA")
        "estado": c.estado.value, 
        "paciente": {
            "id": c.paciente.id,
            "nombre": c.paciente.nombre,
            "email": c.paciente.email
        },
        "medico": {
            "id": c.medico.id,
            "nombre": c.medico.nombre,
            "especialidad": c.medico.especialidad
        }
    }

# --- 3. ENDPOINT: AGENDAR CITA ---
@controller.route('/agendar', methods=['POST'])
def agendar_cita():
    data = request.json
    try:
        # A. OBTENER DATOS REALES DEL PACIENTE
        try:
            resp_pac = requests.get(f"http://pacientes:5003/buscar?q={data['pacienteId']}")
            pacientes_encontrados = resp_pac.json()
            if not pacientes_encontrados:
                return jsonify({"error": "Paciente no encontrado"}), 404
            
            info_pac = pacientes_encontrados[0]
            paciente_ref = PacienteRef(info_pac['id'], info_pac['nombre'], info_pac['email'], info_pac['telefono'])
        except Exception as e:
            return jsonify({"error": f"Error conectando con Pacientes: {e}"}), 500

        # B. OBTENER DATOS REALES DEL MÉDICO
        try:
            resp_med = requests.get("http://medicos:5002/")
            lista_medicos = resp_med.json()
            info_med = next((m for m in lista_medicos if m['id'] == data['medicoId']), None)
            
            if not info_med:
                return jsonify({"error": "Médico no encontrado"}), 404
            
            medico_ref = MedicoRef(info_med['id'], f"{info_med['nombre']} {info_med['apellido']}", info_med['especialidad'])
        except Exception as e:
            return jsonify({"error": f"Error conectando con Médicos: {e}"}), 500

        # C. RESERVAR SLOT
        resp_reserva = requests.patch(f"http://medicos:5002/reservar-slot/{data['slotId']}")
        if resp_reserva.status_code != 200:
             return jsonify({"error": "Turno no disponible"}), 409

        # D. GUARDAR CITA (Dominio)
        nueva_cita = Cita(data['fechaHora'], data['motivo'], paciente_ref, medico_ref)
        nueva_cita.agendar() # Cambia estado a CONFIRMADA
        repo.save(nueva_cita)

        # E. NOTIFICAR (RabbitMQ)
        evento = {
            "citaId": str(nueva_cita.id),
            "pacienteId": str(paciente_ref.id), # ¡Importante para el consumidor!
            "destinatario": paciente_ref.email,
            "asunto": "Cita Confirmada",
            "mensaje": f"Hola {paciente_ref.nombre}, su cita con el Dr. {medico_ref.nombre} ha sido agendada para el {data['fechaHora']}.",
            "tipo": "EMAIL"
        }
        publicar_evento(evento)

        return jsonify({"id": str(nueva_cita.id), "mensaje": "Cita agendada exitosamente"}), 201

    except Exception as e:
        print(f"Error Agendar: {e}")
        return jsonify({"error": str(e)}), 500

# --- 4. ENDPOINT: LISTAR CON FILTROS ---
@controller.route('/', methods=['GET'])
def listar_citas():
    # Recibimos los filtros desde la URL (?fecha=...&pacienteId=...)
    fecha = request.args.get('fecha')
    medico_nombre = request.args.get('medico') # Opcional si decides usarlo a futuro
    paciente_id = request.args.get('pacienteId')
    
    try:
        # Usamos el repo para buscar
        # Nota: Asegúrate de que tu Repo tenga el método find_by_filters actualizado
        citas = repo.find_by_filters(fecha, medico_nombre, paciente_id)
        
        # Convertimos la lista de objetos a lista de diccionarios JSON
        return jsonify([cita_to_dict(c) for c in citas]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 5. ENDPOINT: ANULAR CITA ---
@controller.route('/anular/<id>', methods=['PATCH'])
def anular_cita(id):
    data = request.json
    motivo = data.get('motivo', 'Cancelación por usuario')
    
    try:
        # A. Buscar la cita
        cita = repo.find_by_id(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        
        # B. Aplicar lógica de Dominio
        # Esto cambia el estado a ANULADA y actualiza el motivo
        cita.anular(motivo)
        
        # C. Guardar cambios
        repo.save(cita)
        
        # D. Notificar Cancelación
        evento = {
            "citaId": str(cita.id),
            "pacienteId": str(cita.paciente.id), # ¡Importante!
            "destinatario": cita.paciente.email,
            "asunto": "Cita Anulada",
            "mensaje": f"Su cita del {cita.fechaHora} ha sido ANULADA. Motivo: {motivo}",
            "tipo": "EMAIL"
        }
        publicar_evento(evento)

        return jsonify({"mensaje": "Cita anulada correctamente"}), 200

    except Exception as e:
        print(f"Error Anular: {e}")
        return jsonify({"error": str(e)}), 500