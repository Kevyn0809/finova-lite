"""Función 4: simulador de inversiones con dinero virtual (lógica)."""
import random
from datetime import date

from database import conectar

CAPITAL_INICIAL = 1_000_000
INICIO_SIMULACION = date(2026, 1, 1)

# Precios base SIMULADOS (no son precios reales de mercado)
ACTIVOS = {
    "ECOPETROL": 2300,
    "BANCOLOMBIA": 38000,
    "NUTRESA": 52000,
    "ETF COLCAP": 15000,
    "ETF S&P 500": 480000,
}


def dia_simulado(dias_extra=0):
    """Número de días transcurridos en la simulación."""
    return (date.today() - INICIO_SIMULACION).days + dias_extra


def precio(activo, dia):
    """Precio simulado de un activo en un día dado.

    Cada día el precio sube o baja hasta un 4 %. Usa una semilla fija por
    activo, así el mismo día siempre da el mismo precio.
    """
    azar = random.Random(activo)
    valor = ACTIVOS[activo]
    for _ in range(dia):                      # ciclo for: un paso por día
        valor *= 1 + azar.uniform(-0.04, 0.04)
    return round(valor)


def saldo(usuario_id):
    """Efectivo virtual disponible."""
    with conectar() as con:
        fila = con.execute(
            "SELECT saldo_virtual FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
    return fila["saldo_virtual"]


def comprar(usuario_id, activo, cantidad, precio_unit):
    """Compra acciones/ETFs con dinero virtual. Devuelve (ok, mensaje)."""
    if activo not in ACTIVOS:
        return False, "Activo no válido."
    if cantidad < 1:
        return False, "La cantidad debe ser al menos 1."
    total = cantidad * precio_unit
    if total > saldo(usuario_id):
        return False, "No tienes suficiente efectivo virtual."

    with conectar() as con:
        con.execute(
            "UPDATE usuarios SET saldo_virtual = saldo_virtual - ? WHERE id = ?",
            (total, usuario_id),
        )
        actual = con.execute(
            "SELECT cantidad, precio_promedio FROM cartera "
            "WHERE usuario_id = ? AND activo = ?",
            (usuario_id, activo),
        ).fetchone()
        if actual is None:
            con.execute(
                "INSERT INTO cartera (usuario_id, activo, cantidad, precio_promedio) "
                "VALUES (?, ?, ?, ?)",
                (usuario_id, activo, cantidad, precio_unit),
            )
        else:
            nueva_cantidad = actual["cantidad"] + cantidad
            nuevo_promedio = (
                actual["cantidad"] * actual["precio_promedio"] + total
            ) / nueva_cantidad
            con.execute(
                "UPDATE cartera SET cantidad = ?, precio_promedio = ? "
                "WHERE usuario_id = ? AND activo = ?",
                (nueva_cantidad, nuevo_promedio, usuario_id, activo),
            )
    return True, f"Compraste {cantidad} de {activo}."


def vender(usuario_id, activo, cantidad, precio_unit):
    """Vende lo que tienes en la cartera. Devuelve (ok, mensaje)."""
    if cantidad < 1:
        return False, "La cantidad debe ser al menos 1."
    with conectar() as con:
        actual = con.execute(
            "SELECT cantidad FROM cartera WHERE usuario_id = ? AND activo = ?",
            (usuario_id, activo),
        ).fetchone()
        if actual is None or actual["cantidad"] < cantidad:
            return False, "No tienes tantas unidades de ese activo."

        con.execute(
            "UPDATE usuarios SET saldo_virtual = saldo_virtual + ? WHERE id = ?",
            (cantidad * precio_unit, usuario_id),
        )
        if actual["cantidad"] == cantidad:
            con.execute(
                "DELETE FROM cartera WHERE usuario_id = ? AND activo = ?",
                (usuario_id, activo),
            )
        else:
            con.execute(
                "UPDATE cartera SET cantidad = cantidad - ? "
                "WHERE usuario_id = ? AND activo = ?",
                (cantidad, usuario_id, activo),
            )
    return True, f"Vendiste {cantidad} de {activo}."


def ver_cartera(usuario_id, dia):
    """Devuelve (lista de posiciones, valor total de la cartera)."""
    with conectar() as con:
        filas = con.execute(
            "SELECT activo, cantidad, precio_promedio FROM cartera "
            "WHERE usuario_id = ? ORDER BY activo",
            (usuario_id,),
        ).fetchall()

    posiciones = []
    valor_total = 0.0                          # acumulador
    for fila in filas:
        actual = precio(fila["activo"], dia)
        valor = fila["cantidad"] * actual
        costo = fila["cantidad"] * fila["precio_promedio"]
        ganancia = valor - costo
        valor_total += valor
        posiciones.append({
            "activo": fila["activo"],
            "cantidad": fila["cantidad"],
            "precio_promedio": fila["precio_promedio"],
            "precio_actual": actual,
            "valor": valor,
            "ganancia": ganancia,
            "porcentaje": ganancia / costo * 100 if costo else 0.0,
        })
    return posiciones, valor_total
