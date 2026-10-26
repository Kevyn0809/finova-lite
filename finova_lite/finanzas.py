"""Función 2: registro de ingresos y gastos (lógica, sin interfaz)."""
from datetime import date

from database import conectar

CATEGORIAS_INGRESO = ["Apoyo socioeconómico", "Mesada", "Trabajo", "Otros"]
CATEGORIAS_GASTO = [
    "Alimentación", "Transporte", "Estudio", "Vivienda",
    "Salud", "Ocio", "Otros",
]


def registrar_movimiento(usuario_id, tipo, categoria, monto, fecha=None):
    """Guarda un ingreso o gasto. Devuelve (ok, mensaje)."""
    if tipo not in ("ingreso", "gasto"):
        return False, "Tipo de movimiento no válido."
    if not categoria:
        return False, "Debes elegir una categoría."
    if monto is None or monto <= 0:
        return False, "El monto debe ser mayor que cero."

    fecha = (fecha or date.today()).isoformat()
    with conectar() as con:
        con.execute(
            "INSERT INTO movimientos (usuario_id, tipo, categoria, monto, fecha) "
            "VALUES (?, ?, ?, ?, ?)",
            (usuario_id, tipo, categoria, float(monto), fecha),
        )
    return True, f"{tipo.capitalize()} registrado correctamente."


def listar_movimientos(usuario_id, limite=None):
    """Devuelve los movimientos del usuario, del más reciente al más antiguo."""
    consulta = (
        "SELECT id, tipo, categoria, monto, fecha FROM movimientos "
        "WHERE usuario_id = ? ORDER BY fecha DESC, id DESC"
    )
    parametros = [usuario_id]
    if limite:
        consulta += " LIMIT ?"
        parametros.append(limite)
    with conectar() as con:
        return [dict(f) for f in con.execute(consulta, parametros).fetchall()]


def eliminar_movimiento(usuario_id, movimiento_id):
    """Borra un movimiento (solo si pertenece al usuario)."""
    with conectar() as con:
        con.execute(
            "DELETE FROM movimientos WHERE id = ? AND usuario_id = ?",
            (movimiento_id, usuario_id),
        )


def resumen(usuario_id):
    """Calcula totales y gastos por categoría."""
    with conectar() as con:
        totales = {"ingreso": 0.0, "gasto": 0.0}
        for fila in con.execute(
            "SELECT tipo, SUM(monto) AS total FROM movimientos "
            "WHERE usuario_id = ? GROUP BY tipo",
            (usuario_id,),
        ):
            totales[fila["tipo"]] = fila["total"]

        por_categoria = {
            fila["categoria"]: fila["total"]
            for fila in con.execute(
                "SELECT categoria, SUM(monto) AS total FROM movimientos "
                "WHERE usuario_id = ? AND tipo = 'gasto' "
                "GROUP BY categoria ORDER BY total DESC",
                (usuario_id,),
            )
        }
    return {
        "ingresos": totales["ingreso"],
        "gastos": totales["gasto"],
        "saldo": totales["ingreso"] - totales["gasto"],
        "gastos_por_categoria": por_categoria,
    }
