import uuid
from enum import Enum
from datetime import datetime, date, time, timedelta
from typing import List

# --- ENUMS (Según Diagrama) ---
class DiaSemana(Enum):
    LUNES = "LUNES"
    MARTES = "MARTES"
    MIERCOLES = "MIERCOLES"
    JUEVES = "JUEVES"
    VIERNES = "VIERNES"
    # Agregamos Sábado/Domingo para dar flexibilidad, aunque el diagrama base llegue a Viernes
    SABADO = "SABADO"
    DOMINGO = "DOMINGO"

class EstadoSlot(Enum):
    DISPONIBLE = "DISPONIBLE"
    RESERVADO = "RESERVADO"

# --- CLASES DEL DOMINIO ---

class Especialidad:
    def __init__(self, id: int, nombre: str):
        self.id = id
        self.nombre = nombre

class SlotAgenda:
    def __init__(self, horarioId: uuid.UUID, horaInicio: time, horaFin: time):
        self.id = uuid.uuid4()
        self.horarioId = horarioId
        self.horaInicio = horaInicio
        self.horaFin = horaFin
        self.estado = EstadoSlot.DISPONIBLE

    def reservar(self):
        self.estado = EstadoSlot.RESERVADO

    def liberar(self):
        self.estado = EstadoSlot.DISPONIBLE

class HorarioConfiguracion:
    def __init__(self, medicoId: uuid.UUID, dia: DiaSemana, horaInicio: time, horaFin: time, duracionCita: int):
        self.id = uuid.uuid4()
        self.medicoId = medicoId
        self.dia = dia
        self.horaInicio = horaInicio
        self.horaFin = horaFin
        self.duracionCita = duracionCita
        self.slots: List[SlotAgenda] = []

    def generarSlots(self):
        """Método del diagrama: Genera la lista de Slots según la duración"""
        self.slots = []
        # Fecha dummy para cálculos de tiempo
        dummy_date = date.today()
        inicio_dt = datetime.combine(dummy_date, self.horaInicio)
        fin_dt = datetime.combine(dummy_date, self.horaFin)
        
        # Iteramos sumando minutos
        while inicio_dt + timedelta(minutes=self.duracionCita) <= fin_dt:
            slot_inicio = inicio_dt.time()
            inicio_dt += timedelta(minutes=self.duracionCita)
            slot_fin = inicio_dt.time()
            
            nuevo_slot = SlotAgenda(self.id, slot_inicio, slot_fin)
            self.slots.append(nuevo_slot)
            
        return self.slots

class Medico:
    def __init__(self, nombre: str, apellido: str, especialidad: str):
        self.id = uuid.uuid4()
        self.especialidadId = uuid.uuid4() # FK simulada hacia Especialidad
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad = especialidad
        # Relación 1 a n
        self.horarios: List[HorarioConfiguracion] = [] 

    def getDisponibilidad(self, fecha: date) -> List[SlotAgenda]:
        """Método del diagrama: Filtra slots según la fecha consultada"""
        # Mapeo de Python weekday (0=Lunes) a nuestro Enum
        dias_str = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
        dia_buscado = dias_str[fecha.weekday()]
        
        slots_disponibles = []
        for horario in self.horarios:
            if horario.dia.value == dia_buscado:
                slots_disponibles.extend(horario.slots)
        
        return slots_disponibles