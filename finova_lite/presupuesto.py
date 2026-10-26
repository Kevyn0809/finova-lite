"""Función 3: presupuesto mensual por categoría con alertas (lógica)."""
from datetime import date

from database import conectar

UMBRAL_ALERTA = 80  # % del límite a partir del cual se avisa


def establecer_limite(usuario_id, categoria, limite):
    """Crea o actualiza el límite mensual de una categoría."""
    if not categoria:
        return False, "Debes elegir una categoría."
    if limite is None or limite <= 0:
        return False, "El límite debe ser mayor que cero."
    with conectar() as con:
        con.execute(
            "INSERT INTO presupuestos (usuario_id, categoria, limite) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT (usuario_id, categoria) DO UPDATE SET limite = excluded.limite",
            (usuario_id, categoria, float(limite)),
        )
    return True, f"Límite de «{categoria}» guardado."


def eliminar_limite(usuario_id, categoria):
    """Quita el límite de una categoría."""
    with conectar() as con:
        con.execute(
            "DELETE FROM presupuestos WHERE usuario_id = ? AND categoria = ?",
            (usuario_id, categoria),
        )


def estado_presupuesto(usuario_id):
    """Compara lo gastado este mes con cada límite.

    Devuelve una lista de diccionarios con: categoria, limite, gastado,
    porcentaje y estado ('ok', 'cerca' o 'excedido').
    """
    mes_actual = date.today().strftime("%Y-%m")
    with conectar() as con:
        limites = con.execute(
            "SELECT categoria, limite FROM presupuestos "
            "WHERE usuario_id = ? ORDER BY categoria",
            (usuario_id,),
        ).fetchall()
        gastos = {
            f["categoria"]: f["total"]
            for f in con.execute(
                "SELECT categoria, SUM(monto) AS total FROM movimientos "
                "WHERE usuario_id = ? AND tipo = 'gasto' AND fecha LIKE ? "
                "GROUP BY categoria",
                (usuario_id, mes_actual + "%"),
            )
        }

    resultado = []
    for fila in limites:                      # ciclo for: una vuelta por categoría
        gastado = gastos.get(fila["categoria"], 0.0)
        porcentaje = gastado / fila["limite"] * 100
        if porcentaje > 100:
            estado = "excedido"
        elif porcentaje >= UMBRAL_ALERTA:
            estado = "cerca"
        else:
            estado = "ok"
        resultado.append({
            "categoria": fila["categoria"],
            "limite": fila["limite"],
            "gastado": gastado,
            "porcentaje": porcentaje,
            "estado": estado,
        })
    return resultado


def alertas(usuario_id):
    """Devuelve una lista de (nivel, mensaje) para las categorías en riesgo."""
    mensajes = []
    for item in estado_presupuesto(usuario_id):
        if item["estado"] == "excedido":
            mensajes.append(("error", f"Superaste el límite de «{item['categoria']}» "
                                      f"({item['porcentaje']:.0f}%)."))
        elif item["estado"] == "cerca":
            mensajes.append(("warning", f"Vas en {item['porcentaje']:.0f}% del límite "
                                        f"de «{item['categoria']}»."))
    return mensajes
