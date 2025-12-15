from flask import Blueprint, request, jsonify
import requests
from domain.models import Cita, PacienteRef, MedicoRef
from repositories.cita_repository import SQLiteCitaRepository

controller = Blueprint('cita_controller', __name__)
repo = SQLiteCitaRepository()

# Configuración de URLs de los otros microservicios (Nombres de Docker)
URL_PACIENTES = "http://pacientes:5003/api/pacientes" # Ajusta según rutas internas si es necesario, o usa directo al puerto
URL_MEDICOS = "http://medicos:5002"

# Nota: Como el Gateway redirige /api/pacientes -> pacientes:5003, internamente podemos ir directo a la raíz del servicio si el blueprint lo permite
# Asumiremos que los servicios internos responden en la raiz '/' o según definiste sus blueprints.
# Revisando tu código anterior: Pacientes responde en /, Medicos en /.

@controller.route('/agendar', methods=['POST'])
def agendar_cita():
    data = request.json
    try:
        # 1. Obtener datos del Request
        paciente_id = data['pacienteId']
        medico_id = data['medicoId']
        slot_id = data['slotId'] # Necesario para reservar
        fecha_hora = data['fechaHora'] # "2023-10-20 08:00"
        motivo = data.get('motivo', 'Consulta General')

        # 2. VALIDAR PACIENTE (Comunicación Síncrona)
        # Hacemos un GET al microservicio de pacientes para ver si existe y traer sus datos
        resp_paciente = requests.get(f"http://pacientes:5003/validar/{paciente_id}")
        
        # OJO: Tu endpoint validar solo devolvía {existe: bool}. 
        # Para llenar PacienteRef necesitamos nombre, email.
        # ASUMIREMOS que existe un endpoint /<id> en pacientes que devuelve el detalle, 
        # SI NO EXISTE, deberías crearlo en Pacientes o usar datos dummy por ahora si no quieres tocar el otro código.
        # Por robustez, usaré datos genéricos si solo validamos existencia, o idealmente haríamos:
        # resp_detalle = requests.get(f"http://pacientes:5003/{paciente_id}")
        
        if resp_paciente.status_code != 200 or not resp_paciente.json().get('existe'):
            return jsonify({"error": "Paciente no válido o no encontrado"}), 404

        # Simulamos datos del paciente ya que el endpoint validar solo dice True/False
        # En un caso real, harías GET /pacientes/<id> para obtener nombre y email.
        paciente_ref = PacienteRef(paciente_id, "Paciente Info", "email@test.com", "0999999") 

        # 3. RESERVAR SLOT MÉDICO (Comunicación Síncrona)
        # Llamamos al endpoint que creaste hace un momento
        resp_reserva = requests.patch(f"http://medicos:5002/reservar-slot/{slot_id}")
        
        if resp_reserva.status_code != 200:
            return jsonify({"error": "No se pudo reservar el horario. Puede que ya esté ocupado."}), 400

        # Datos dummy del médico (Idealmente también harías un GET al médico)
        medico_ref = MedicoRef(medico_id, "Dr. Consultado", "Especialidad")

        # 4. CREAR Y GUARDAR CITA (Dominio)
        nueva_cita = Cita(fecha_hora, motivo, paciente_ref, medico_ref)
        nueva_cita.agendar() # Cambia estado a CONFIRMADA
        
        repo.save(nueva_cita)

        # 5. ENVIAR NOTIFICACIÓN (Llamada al nuevo microservicio)
        try:
            requests.post("http://notificaciones:5004/enviar", json={
                "citaId": str(nueva_cita.id),
                "pacienteId": str(paciente_ref.id),
                "destinatario": paciente_ref.email,
                "asunto": "Confirmación de Cita Médica",
                "mensaje": f"Su cita con el Dr. {medico_ref.nombre} ha sido agendada para el {fecha_hora}.",
                "tipo": "EMAIL"
            })
        except Exception as e:
            print(f"No se pudo enviar la notificación: {e}") # No detenemos el proceso si falla el email

        return jsonify({"id": str(nueva_cita.id), "mensaje": "Cita agendada exitosamente"}), 201


    except Exception as e:
        return jsonify({"error": str(e)}), 500

@controller.route('/consultar/<id>', methods=['GET'])
def consultar_cita(id):
    cita = repo.find_by_id(id)
    if not cita:
        return jsonify({"error": "Cita no encontrada"}), 404
    
    return jsonify({
        "id": str(cita.id),
        "fecha": cita.fechaHora,
        "estado": cita.estado.value,
        "paciente": cita.paciente.nombre,
        "medico": cita.medico.nombre
    }), 200

@controller.route('/anular/<id>', methods=['PUT'])
def anular_cita(id):
    data = request.json
    motivo = data.get('motivo', 'Sin motivo')
    
    cita = repo.find_by_id(id)
    if not cita:
        return jsonify({"error": "Cita no encontrada"}), 404

    # Lógica de dominio
    cita.anular(motivo)
    
    # Persistencia
    repo.update(cita)
    
    # Aquí deberías idealmente liberar el Slot en el servicio de Médicos
    # requests.patch(f"http://medicos:5002/liberar-slot/...") 

    return jsonify({"mensaje": "Cita anulada"}), 200