import uuid
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod

# --- ENUMS ---
class EstadoNotificacion(Enum):
    PENDIENTE = "Pendiente"
    ENVIADA = "Enviada"
    FALLIDA = "Fallida"

# --- ENTIDAD NOTIFICACION ---
class Notificacion:
    def __init__(self, citaId, pacienteId, destinatario, asunto, mensaje):
        self.id = uuid.uuid4()
        self.citaId = citaId
        self.pacienteId = pacienteId
        self.destinatario = destinatario
        self.asunto = asunto
        self.mensaje = mensaje
        self.fecha = datetime.now()
        self.estado = EstadoNotificacion.PENDIENTE

# --- PATRÓN STRATEGY (Interfaces y Concreciones) ---

# 1. La Interfaz (Abstracta)
class INotificador(ABC):
    @abstractmethod
    def enviar(self, notificacion: Notificacion) -> bool:
        pass

# 2. Estrategia Email
class NotificadorEmail(INotificador):
    def enviar(self, notificacion: Notificacion) -> bool:
        # Aquí iría la lógica real con SMTP (Gmail, SendGrid, etc.)
        print(f" 📧 [EMAIL] Para: {notificacion.destinatario} | Asunto: {notificacion.asunto}")
        print(f"   Mensaje: {notificacion.mensaje}")
        return True # Simulamos éxito

# 3. Estrategia SMS
class NotificadorSMS(INotificador):
    def enviar(self, notificacion: Notificacion) -> bool:
        # Aquí iría la lógica con Twilio o AWS SNS
        print(f" 📧 [SMS] Para: {notificacion.destinatario} | Texto: {notificacion.mensaje}")
        return True # Simulamos éxito

# --- SERVICIO DE DOMINIO (Contexto) ---
class ServicioNotificacion:
    def __init__(self, repo):
        self.repo = repo
        self.notificador: INotificador = None

    def preparar_estrategia(self, tipo: str):
        """Define qué estrategia usar según el tipo solicitado"""
        if tipo.upper() == 'SMS':
            self.notificador = NotificadorSMS()
        else:
            self.notificador = NotificadorEmail()

    def procesar_notificacion(self, data):
        # 1. Crear la Entidad
        notif = Notificacion(
            data['citaId'], 
            data['pacienteId'], 
            data['destinatario'], 
            data['asunto'], 
            data['mensaje']
        )
        
        # 2. Validar (Lógica básica)
        if not self.notificador:
            self.preparar_estrategia("EMAIL") # Default

        # 3. Intentar Enviar (Usando la estrategia seleccionada)
        try:
            exito = self.notificador.enviar(notif)
            notif.estado = EstadoNotificacion.ENVIADA if exito else EstadoNotificacion.FALLIDA
        except Exception as e:
            print(f"Error al enviar: {e}")
            notif.estado = EstadoNotificacion.FALLIDA

        # 4. Persistir (Guardar log)
        self.repo.save(notif)
        
        return notif