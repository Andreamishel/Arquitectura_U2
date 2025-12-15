import sqlite3
from domain.models import Notificacion, EstadoNotificacion

class SQLiteNotificacionRepository:
    def __init__(self, db_path="notificaciones.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notificaciones (
                    id TEXT PRIMARY KEY,
                    cita_id TEXT,
                    paciente_id TEXT,
                    destinatario TEXT,
                    asunto TEXT,
                    mensaje TEXT,
                    fecha TEXT,
                    estado TEXT
                )
            ''')
            conn.commit()

    def save(self, notif: Notificacion):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notificaciones VALUES (?,?,?,?,?,?,?,?)
            ''', (
                str(notif.id), str(notif.citaId), str(notif.pacienteId),
                notif.destinatario, notif.asunto, notif.mensaje,
                str(notif.fecha), notif.estado.value
            ))
            conn.commit()