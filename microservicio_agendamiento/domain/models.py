import uuid
from enum import Enum
from datetime import datetime

# --- ENUMS ---
class EstadoCita(Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    ANULADA = "ANULADA"
    REALIZADA = "REALIZADA"

# --- VALUE OBJECTS / REFERENCIAS ---
# Estos objetos guardan una "foto" de los datos del paciente/médico 
# en el momento de la cita, por si cambian después.
class PacienteRef:
    def __init__(self, id_paciente, nombre, email, telefono):
        self.id = id_paciente
        self.nombre = nombre
        self.email = email
        self.telefono = telefono

class MedicoRef:
    def __init__(self, id_medico, nombre, especialidad):
        self.id = id_medico
        self.nombre = nombre
        self.especialidad = especialidad

# --- ENTIDAD CITA (Aggregate Root) ---
class Cita:
    def __init__(self, fecha_hora: str, motivo: str, paciente_ref: PacienteRef, medico_ref: MedicoRef):
        self.id = uuid.uuid4()
        self.fechaHora = fecha_hora # String ISO o DateTime
        self.motivo = motivo
        self.paciente = paciente_ref # Relación 1 a 1 en el objeto
        self.medico = medico_ref     # Relación 1 a 1 en el objeto
        self.estado = EstadoCita.PENDIENTE

    # --- Métodos del Diagrama ---
    
    def agendar(self):
        """Lógica de negocio al crear la cita"""
        self.estado = EstadoCita.CONFIRMADA
        # Aquí podrías validar reglas de negocio (ej. no agendar en pasado)
        return self

    def modificar(self, nueva_fecha: str):
        if self.estado == EstadoCita.ANULADA:
            raise Exception("No se puede modificar una cita anulada")
        self.fechaHora = nueva_fecha
        return self

    def anular(self, motivo_anulacion: str):
        self.estado = EstadoCita.ANULADA
        self.motivo = f"{self.motivo} [ANULADA: {motivo_anulacion}]"
        return True