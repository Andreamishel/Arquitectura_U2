import uuid
from enum import Enum
from datetime import datetime

# --- ENUMS ---
class EstadoPaciente(Enum):
    Activo = "Activo"
    Inactivo = "Inactivo"

class TipoIdentificacion(Enum):
    Cedula = "Cedula"
    Pasaporte = "Pasaporte"

class Genero(Enum):
    Masculino = "Masculino"
    Femenino = "Femenino"

# --- VALUE OBJECTS ---
class Direccion:
    def __init__(self, calle: str, numero: str, ciudad: str):
        self.calle = calle
        self.numero = numero
        self.ciudad = ciudad

class DatosContacto:
    def __init__(self, email: str, telefono: str):
        self.email = email
        self.telefono = telefono

# --- ENTIDAD PACIENTE ---
class Paciente:
    def __init__(self, identificacion: str, tipoId: TipoIdentificacion, 
                 nombre: str, genero: Genero, fechaNac: str, 
                 contacto: DatosContacto, direccion: Direccion):
        self.id = uuid.uuid4()
        self.identificacion = identificacion
        self.tipoIdentificacion = tipoId
        self.nombreCompleto = nombre
        self.genero = genero
        self.fechaNacimiento = fechaNac
        self.datosContacto = contacto
        self.direccion = direccion
        self.estado = EstadoPaciente.Activo

    # --- MÉTODOS DEL DIAGRAMA ---
    def registrar(self):
        """Asigna estado activo inicial"""
        self.estado = EstadoPaciente.Activo
        return self

    def actualizarDomicilio(self, d: Direccion):
        """Evento de Negocio: Modifica la dirección"""
        self.direccion = d

    def validarExistencia(self):
        """Evento de Negocio: Verifica consistencia"""
        return True if self.identificacion else False