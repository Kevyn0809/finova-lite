"""Función 1: registro e inicio de sesión."""
import hashlib
import hmac
import os
import sqlite3

from database import conectar


def _hashear(clave, sal):
    """Convierte la clave en un hash seguro (nunca se guarda la clave real)."""
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, 100_000).hex()


def registrar(nombre, usuario, clave):
    """Crea un usuario nuevo. Devuelve (ok, mensaje)."""
    nombre, usuario = nombre.strip(), usuario.strip().lower()
    if not nombre or not usuario:
        return False, "El nombre y el usuario no pueden estar vacíos."
    if len(clave) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."

    sal = os.urandom(16)
    try:
        with conectar() as con:
            con.execute(
                "INSERT INTO usuarios (nombre, usuario, sal, clave_hash) "
                "VALUES (?, ?, ?, ?)",
                (nombre, usuario, sal.hex(), _hashear(clave, sal)),
            )
    except sqlite3.IntegrityError:
        return False, "Ese usuario ya existe."
    return True, "Cuenta creada correctamente."


def iniciar_sesion(usuario, clave):
    """Valida las credenciales. Devuelve el usuario (fila) o None."""
    with conectar() as con:
        fila = con.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario.strip().lower(),)
        ).fetchone()
    if fila is None:
        return None
    hash_calculado = _hashear(clave, bytes.fromhex(fila["sal"]))
    if hmac.compare_digest(hash_calculado, fila["clave_hash"]):
        return fila
    return None
