"""Conexión a SQLite y creación de tablas de FINOVA Lite."""
import sqlite3

DB_NOMBRE = "finova.db"


def conectar():
    """Devuelve una conexión a la base de datos."""
    conexion = sqlite3.connect(DB_NOMBRE)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    """Crea las tablas si todavía no existen."""
    with conectar() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                sal TEXT NOT NULL,
                clave_hash TEXT NOT NULL,
                saldo_virtual REAL NOT NULL DEFAULT 1000000
            );

            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK (tipo IN ('ingreso', 'gasto')),
                categoria TEXT NOT NULL,
                monto REAL NOT NULL CHECK (monto > 0),
                fecha TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            );

            CREATE TABLE IF NOT EXISTS presupuestos (
                usuario_id INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                limite REAL NOT NULL CHECK (limite > 0),
                PRIMARY KEY (usuario_id, categoria),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            );

            CREATE TABLE IF NOT EXISTS cartera (
                usuario_id INTEGER NOT NULL,
                activo TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                precio_promedio REAL NOT NULL,
                PRIMARY KEY (usuario_id, activo),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            );
        """)
