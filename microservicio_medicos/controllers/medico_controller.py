from flask import Blueprint, request, jsonify
from domain.models import Medico, HorarioConfiguracion, DiaSemana
from repositories.medico_repository import SQLiteMedicoRepository
from datetime import datetime
import uuid

controller = Blueprint('medico_controller', __name__)
repo = SQLiteMedicoRepository()

# --- 1. CREAR MÉDICO ---
@controller.route('/crear', methods=['POST'])
def crear_medico():
    data = request.json
    try:
        medico = Medico(data['nombre'], data['apellido'], data['especialidad'])
        repo.save(medico)
        return jsonify({"id": str(medico.id), "mensaje": "Médico creado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- 2. CONFIGURAR HORARIO ---
@controller.route('/configurar-horario', methods=['POST'])
def configurar_horario():
    data = request.json
    try:
        medico = repo.find_by_id(data['medicoId'])
        if not medico: return jsonify({"error": "Médico no encontrado"}), 404
        
        # Conversión de datos
        dia_enum = DiaSemana(data['dia'])
        h_inicio = datetime.strptime(data['horaInicio'], "%H:%M").time()
        h_fin = datetime.strptime(data['horaFin'], "%H:%M").time()
        duracion = int(data['duracion'])
        
        # Crear Configuración y Generar Slots (Dominio)
        config = HorarioConfiguracion(medico.id, dia_enum, h_inicio, h_fin, duracion)
        slots_generados = config.generarSlots()
        
        # Persistencia
        repo.save_horario_completo(config)
        
        return jsonify({
            "mensaje": "Horario configurado",
            "slots_creados": len(slots_generados),
            "dia": dia_enum.value
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- 3. OBTENER DISPONIBILIDAD (IMPLEMENTADO) ---
@controller.route('/disponibilidad', methods=['GET'])
def obtener_disponibilidad():
    try:
        medico_id = request.args.get('medicoId')
        fecha_str = request.args.get('fecha')
        
        if not medico_id or not fecha_str:
            return jsonify({"error": "Faltan parámetros medicoId o fecha"}), 400
            
        # 1. Recuperar Agregado Completo
        medico = repo.find_by_id(medico_id)
        if not medico:
            return jsonify({"error": "Médico no encontrado"}), 404
            
        # 2. Convertir Fecha
        fecha_consulta = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # 3. Consultar al Dominio
        slots = medico.getDisponibilidad(fecha_consulta)
        
        # 4. Respuesta (DTO simplificado)
        response = []
        for s in slots:
            response.append({
                "id": str(s.id),
                "horaInicio": s.horaInicio.strftime("%H:%M"),
                "horaFin": s.horaFin.strftime("%H:%M"),
                "estado": s.estado.value
            })
            
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 4. RESERVAR SLOT (NECESARIO PARA AGENDAMIENTO) ---
@controller.route('/reservar-slot/<slot_id>', methods=['PATCH'])
def reservar_slot(slot_id):
    try:
        # Nota: Aquí deberías implementar un método en el repo para buscar SOLO el slot
        # O buscar el médico, encontrar el slot en memoria y guardar todo.
        # Por simplicidad del prototipo, asumiremos que actualizas el estado directo en BD o vía repo.
        
        exito = repo.reservar_slot(slot_id) 
        if exito:
            return jsonify({"mensaje": "Slot reservado con éxito"}), 200
        else:
            return jsonify({"error": "No se pudo reservar o slot no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Helper para JSON
def medico_to_dict(m: Medico):
    return {
        "id": str(m.id),
        "nombre": m.nombre,
        "apellido": m.apellido,
        "especialidad": m.especialidad
    }

# 5. LISTAR TODOS
@controller.route('/', methods=['GET'])
def listar_todos():
    try:
        medicos = repo.find_all()
        return jsonify([medico_to_dict(m) for m in medicos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 6. BUSCAR
@controller.route('/buscar', methods=['GET'])
def buscar_medicos():
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Falta parámetro de búsqueda"}), 400
        
        medicos = repo.search(query)
        return jsonify([medico_to_dict(m) for m in medicos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500