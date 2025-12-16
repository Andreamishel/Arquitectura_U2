import sqlite3
from domain.models import Paciente, Direccion, DatosContacto, EstadoPaciente, TipoIdentificacion, Genero

class SQLitePacienteRepository:
    def __init__(self, db_path="pacientes.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pacientes (
                    id TEXT PRIMARY KEY,
                    identificacion TEXT UNIQUE,
                    tipo_id TEXT,
                    nombre TEXT,
                    genero TEXT,
                    fecha_nacimiento TEXT,
                    email TEXT,
                    telefono TEXT,
                    calle TEXT,
                    numero TEXT,
                    ciudad TEXT,
                    estado TEXT
                )
            ''')
            conn.commit()

    def save(self, p: Paciente):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pacientes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(p.id), p.identificacion, p.tipoIdentificacion.value,
                p.nombreCompleto, p.genero.value, p.fechaNacimiento,
                p.datosContacto.email, p.datosContacto.telefono,
                p.direccion.calle, p.direccion.numero, p.direccion.ciudad,
                p.estado.value
            ))
            conn.commit()
        return p

    def find_by_id(self, id_paciente: str) -> Paciente:
        """
        Recupera un registro de la BD y lo reconstruye como Objeto de Dominio (Paciente).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pacientes WHERE id = ?', (id_paciente,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Mapeo de columnas a variables (según el orden del CREATE TABLE)
            # 0:id, 1:identificacion, 2:tipo_id, 3:nombre, 4:genero, 
            # 5:fecha, 6:email, 7:tel, 8:calle, 9:num, 10:ciudad, 11:estado

            try:
                # Reconstruir Enums y Value Objects
                tipo_enum = TipoIdentificacion(row[2])
                genero_enum = Genero(row[4])
                contacto = DatosContacto(row[6], row[7])
                direccion = Direccion(row[8], row[9], row[10])
                
                # Instanciar la Entidad
                p = Paciente(row[1], tipo_enum, row[3], genero_enum, row[5], contacto, direccion)
                
                # IMPORTANTE: Sobrescribir el ID generado por el constructor con el de la BD
                p.id = row[0] 
                
                # Restaurar el estado
                p.estado = EstadoPaciente(row[11])
                
                return p
            except ValueError as e:
                print(f"Error de integridad de datos en ID {id_paciente}: {e}")
                return None

    def update(self, p: Paciente):
        """
        Guarda los cambios realizados en el objeto Paciente de vuelta a la BD.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pacientes 
                SET calle = ?, numero = ?, ciudad = ?, 
                    email = ?, telefono = ?, estado = ?
                WHERE id = ?
            ''', (
                p.direccion.calle, p.direccion.numero, p.direccion.ciudad,
                p.datosContacto.email, p.datosContacto.telefono, p.estado.value,
                str(p.id)
            ))
            conn.commit()
            return cursor.rowcount > 0

    def exists_by_identificacion(self, identificacion: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM pacientes WHERE identificacion = ?', (identificacion,))
            return cursor.fetchone() is not None
        
    def find_all(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pacientes')
            rows = cursor.fetchall()
            pacientes = []
            
            for row in rows:
                try:
                    # Reconstrucción (Misma lógica que find_by_id)
                    tipo_enum = TipoIdentificacion(row[2])
                    genero_enum = Genero(row[4])
                    contacto = DatosContacto(row[6], row[7])
                    direccion = Direccion(row[8], row[9], row[10])
                    
                    p = Paciente(row[1], tipo_enum, row[3], genero_enum, row[5], contacto, direccion)
                    p.id = row[0]
                    p.estado = EstadoPaciente(row[11])
                    
                    pacientes.append(p)
                except ValueError:
                    continue # Saltar registros corruptos si los hubiera
            
            return pacientes
        
    def search(self, query):
        """Busca por identificación exacta O por nombre parcial"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # El % sirve para buscar texto que contenga la palabra
            param = f"%{query}%" 
            cursor.execute('''
                SELECT * FROM pacientes 
                WHERE identificacion LIKE ? OR nombre LIKE ?
            ''', (param, param))
            
            rows = cursor.fetchall()
            pacientes = []
            
            for row in rows:
                try:
                    # Reconstrucción (Mismo código que en find_all)
                    tipo_enum = TipoIdentificacion(row[2])
                    genero_enum = Genero(row[4])
                    contacto = DatosContacto(row[6], row[7])
                    direccion = Direccion(row[8], row[9], row[10])
                    p = Paciente(row[1], tipo_enum, row[3], genero_enum, row[5], contacto, direccion)
                    p.id = row[0]
                    p.estado = EstadoPaciente(row[11])
                    pacientes.append(p)
                except Exception:
                    continue
            return pacientes