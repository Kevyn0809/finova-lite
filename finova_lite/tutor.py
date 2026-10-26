"""Función 5: tutor financiero con lecciones y quiz (lógica y contenido)."""
from database import conectar

# Cada pregunta: (enunciado, [opciones], índice de la correcta, explicación)
LECCIONES = [
    {
        "id": "ahorro",
        "titulo": "💰 Ahorro",
        "texto": (
            "Ahorrar es guardar una parte de tu ingreso **antes** de gastarlo. "
            "Una guía popular es la regla **50/30/20**: 50 % para necesidades, "
            "30 % para gustos y 20 % para ahorro. También conviene tener un "
            "**fondo de emergencia**: dinero reservado para imprevistos, "
            "equivalente a 3 a 6 meses de gastos."
        ),
        "preguntas": [
            ("¿Qué propone la regla 50/30/20?",
             ["50 % ahorro, 30 % necesidades, 20 % gustos",
              "50 % necesidades, 30 % gustos, 20 % ahorro",
              "Gastar todo y ahorrar lo que sobre"], 1,
             "50 % necesidades, 30 % gustos y 20 % ahorro."),
            ("¿Qué es un fondo de emergencia?",
             ["Dinero para comprar acciones",
              "Un préstamo del banco",
              "Dinero reservado para imprevistos (3 a 6 meses de gastos)"], 2,
             "Es un colchón para imprevistos, no una inversión."),
            ("¿Cuándo conviene ahorrar?",
             ["Al final del mes, con lo que sobre",
              "Apenas recibes el ingreso, antes de gastar",
              "Solo cuando ganas más"], 1,
             "Si esperas a ver qué sobra, casi nunca sobra."),
        ],
    },
    {
        "id": "presupuesto",
        "titulo": "🎯 Presupuesto",
        "texto": (
            "Un presupuesto es un **plan de ingresos y gastos**. Los gastos "
            "**fijos** se repiten cada mes (arriendo, transporte) y los "
            "**variables** cambian (ocio, comida fuera). Registrar lo que "
            "gastas y revisar tus límites cada semana te permite corregir "
            "a tiempo."
        ),
        "preguntas": [
            ("¿Qué es un gasto fijo?",
             ["Una compra impulsiva",
              "Uno que se repite cada mes con valor similar, como el arriendo",
              "Un gasto que ocurre una sola vez"], 1,
             "Los fijos son predecibles y se repiten."),
            ("Si superas el límite de una categoría, lo mejor es:",
             ["Ignorar la alerta",
              "Subir el límite sin pensar",
              "Revisar en qué se fue y ajustar los demás gastos"], 2,
             "La alerta sirve para corregir, no para ignorarla."),
            ("¿Para qué sirve registrar los gastos?",
             ["Para saber a dónde se va tu dinero y poder planear",
              "Para gastar más",
              "Para no pagar impuestos"], 0,
             "Lo que no se mide, no se puede mejorar."),
        ],
    },
    {
        "id": "riesgo",
        "titulo": "⚖️ Riesgo e inversión",
        "texto": (
            "Invertir es poner tu dinero a trabajar para que crezca, "
            "asumiendo cierto **riesgo**. En general, a **mayor rentabilidad "
            "esperada, mayor riesgo**. Nunca inviertas el dinero que "
            "necesitas para tus gastos básicos. Un simulador con dinero "
            "virtual te deja practicar sin perder dinero real."
        ),
        "preguntas": [
            ("Normalmente, a mayor rentabilidad esperada hay...",
             ["Menor riesgo", "No hay riesgo", "Mayor riesgo"], 2,
             "Rentabilidad y riesgo suelen ir de la mano."),
            ("¿Qué dinero NO deberías invertir?",
             ["El que necesitas para tus gastos básicos",
              "El que te sobra", "Ninguno"], 0,
             "Invierte solo lo que puedas dejar quieto sin afectar tu día a día."),
            ("¿Qué ventaja tiene un simulador?",
             ["Garantiza ganancias reales",
              "Practicar decisiones sin perder dinero real",
              "Evita tener que aprender"], 1,
             "Equivocarte en el simulador no cuesta dinero."),
        ],
    },
    {
        "id": "diversificacion",
        "titulo": "📊 Diversificación y ETFs",
        "texto": (
            "**Diversificar** es repartir tu dinero en varios activos para no "
            "depender de uno solo. Un **ETF** es un fondo que agrupa muchos "
            "activos y se negocia como una acción. El **COLCAP** es un índice "
            "de las acciones más líquidas de la Bolsa de Valores de Colombia."
        ),
        "preguntas": [
            ("¿Qué significa diversificar?",
             ["Poner todo en una sola acción",
              "Vender todo", "Repartir el dinero en varios activos"], 2,
             "No poner todos los huevos en la misma canasta."),
            ("Un ETF es...",
             ["Una cuenta de ahorros",
              "Un fondo que agrupa muchos activos y se negocia como una acción",
              "Un impuesto"], 1,
             "Con un ETF compras un pedacito de muchos activos a la vez."),
            ("¿Por qué diversificar reduce el riesgo?",
             ["Porque garantiza ganancias",
              "Porque elimina la inflación",
              "Porque si un activo cae, otros pueden compensar la pérdida"], 2,
             "Reduce el riesgo, pero no lo elimina."),
        ],
    },
]


def _asegurar_tabla():
    """Crea la tabla de progreso si no existe."""
    with conectar() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS progreso_tutor ("
            "usuario_id INTEGER NOT NULL, leccion TEXT NOT NULL, "
            "mejor_puntaje INTEGER NOT NULL, total INTEGER NOT NULL, "
            "PRIMARY KEY (usuario_id, leccion))"
        )


def calificar(preguntas, respuestas):
    """Cuenta los aciertos. 'respuestas' es la lista de opciones elegidas."""
    aciertos = 0                                   # contador
    for pregunta, respuesta in zip(preguntas, respuestas):
        enunciado, opciones, correcta, _ = pregunta
        if respuesta == opciones[correcta]:
            aciertos += 1
    return aciertos


def guardar_resultado(usuario_id, leccion_id, aciertos, total):
    """Guarda el mejor puntaje de la lección."""
    _asegurar_tabla()
    with conectar() as con:
        con.execute(
            "INSERT INTO progreso_tutor (usuario_id, leccion, mejor_puntaje, total) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT (usuario_id, leccion) DO UPDATE SET "
            "mejor_puntaje = MAX(mejor_puntaje, excluded.mejor_puntaje)",
            (usuario_id, leccion_id, aciertos, total),
        )


def progreso(usuario_id):
    """Devuelve {leccion_id: (mejor_puntaje, total)}."""
    _asegurar_tabla()
    with conectar() as con:
        filas = con.execute(
            "SELECT leccion, mejor_puntaje, total FROM progreso_tutor "
            "WHERE usuario_id = ?", (usuario_id,)
        ).fetchall()
    return {f["leccion"]: (f["mejor_puntaje"], f["total"]) for f in filas}
