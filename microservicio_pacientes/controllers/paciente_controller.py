from flask import Blueprint, request, jsonify
from domain.models import Paciente, Direccion, DatosContacto, TipoIdentificacion, Genero
from repositories.paciente_repository import SQLitePacienteRepository

controller = Blueprint('paciente_controller', __name__)
repo = SQLitePacienteRepository()

# 1. REGISTRAR PACIENTE
@controller.route('/registrar', methods=['POST'])
def registrar():
    d = request.json
    try:
        # Validar Enums
        try:
            tipo_enum = TipoIdentificacion(d['tipoIdentificacion'])
            genero_enum = Genero(d['genero'])
        except ValueError:
            return jsonify({"error": "Valores de Genero o TipoID incorrectos"}), 400

        # Crear Value Objects
        contacto = DatosContacto(d['email'], d['telefono'])
        direccion = Direccion(d['calle'], d['numero'], d['ciudad'])
        
        # Crear Entidad
        p = Paciente(d['identificacion'], tipo_enum, d['nombre'], 
                     genero_enum, d['fechaNacimiento'], contacto, direccion)
        
        # Ejecutar lógica de dominio
        p.registrar()
        
        # Persistir
        repo.save(p)
        return jsonify({"id": str(p.id), "mensaje": "Paciente registrado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. ACTUALIZAR DOMICILIO (Modificado para DDD)
@controller.route('/<id>/domicilio', methods=['PUT'])
def actualizar_domicilio(id):
    d = request.json
    
    # A. Recuperar la entidad (Reconstitución)
    paciente = repo.find_by_id(id)
    
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404
        
    try:
        # B. Crear el Value Object necesario
        nueva_direccion = Direccion(d['calle'], d['numero'], d['ciudad'])
        
        # C. Ejecutar el comportamiento del Dominio (La entidad se modifica a sí misma)
        paciente.actualizarDomicilio(nueva_direccion)
        
        # D. Persistir los cambios del objeto
        exito = repo.update(paciente)
        
        if exito:
            return jsonify({"mensaje": "Domicilio actualizado exitosamente"}), 200
        else:
            return jsonify({"error": "No se pudieron guardar los cambios"}), 500
            
    except KeyError:
        return jsonify({"error": "Faltan datos de dirección (calle, numero, ciudad)"}), 400

# 3. VALIDAR EXISTENCIA
@controller.route('/validar/<identificacion>', methods=['GET'])
def validar(identificacion):
    existe = repo.exists_by_identificacion(identificacion)
    return jsonify({"existe": existe}), 200