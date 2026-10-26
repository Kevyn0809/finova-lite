"""FINOVA Lite - Aplicación web (Streamlit). Se abre bien desde el celular."""
import pandas as pd
import streamlit as st

import finanzas
import inversiones
import presupuesto
import tutor
import usuarios
from database import crear_tablas

st.set_page_config(page_title="FINOVA Lite", page_icon="💰", layout="centered")
crear_tablas()


def moneda(valor):
    """Formatea un número como pesos colombianos: $1.234.567"""
    return "$" + f"{valor:,.0f}".replace(",", ".")


# ---------- Pantalla de acceso ----------
def pantalla_acceso():
    st.title("💰 FINOVA Lite")
    st.caption("Aprende a manejar tu dinero e invierte sin riesgo.")
    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_login:
        with st.form("form_login"):
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            enviar = st.form_submit_button("Entrar", width="stretch")
        if enviar:
            fila = usuarios.iniciar_sesion(usuario, clave)
            if fila:
                st.session_state["usuario"] = dict(fila)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with tab_registro:
        with st.form("form_registro"):
            nombre = st.text_input("Nombre completo")
            usuario = st.text_input("Usuario", key="reg_usuario")
            clave = st.text_input(
                "Contraseña (mínimo 6 caracteres)", type="password", key="reg_clave"
            )
            enviar = st.form_submit_button("Crear cuenta", width="stretch")
        if enviar:
            ok, mensaje = usuarios.registrar(nombre, usuario, clave)
            (st.success if ok else st.error)(mensaje)


# ---------- Secciones de la app ----------
def seccion_inicio(usuario):
    st.header(f"Hola, {usuario['nombre'].split()[0]} 👋")
    datos = finanzas.resumen(usuario["id"])

    st.metric("Saldo disponible", moneda(datos["saldo"]))
    col1, col2 = st.columns(2)
    col1.metric("Ingresos", moneda(datos["ingresos"]))
    col2.metric("Gastos", moneda(datos["gastos"]))

    for nivel, mensaje in presupuesto.alertas(usuario["id"]):
        (st.error if nivel == "error" else st.warning)(mensaje)

    if datos["gastos_por_categoria"]:
        st.subheader("Gastos por categoría")
        tabla = pd.Series(datos["gastos_por_categoria"], name="Gastos")
        st.bar_chart(tabla)
    else:
        st.info("Aún no tienes gastos registrados. Ve a «Ingresos y gastos».")


def seccion_movimientos(usuario):
    st.header("Ingresos y gastos")
    tipo = st.radio("¿Qué quieres registrar?", ["Gasto", "Ingreso"], horizontal=True)
    categorias = (
        finanzas.CATEGORIAS_GASTO if tipo == "Gasto" else finanzas.CATEGORIAS_INGRESO
    )

    with st.form("form_movimiento", clear_on_submit=True):
        categoria = st.selectbox("Categoría", categorias)
        monto = st.number_input("Monto (COP)", min_value=0, step=1000)
        fecha = st.date_input("Fecha")
        enviar = st.form_submit_button("Guardar", width="stretch")
    if enviar:
        ok, mensaje = finanzas.registrar_movimiento(
            usuario["id"], tipo.lower(), categoria, monto, fecha
        )
        (st.success if ok else st.error)(mensaje)

    st.subheader("Historial")
    movimientos = finanzas.listar_movimientos(usuario["id"], limite=50)
    if not movimientos:
        st.info("Todavía no hay movimientos.")
        return
    tabla = pd.DataFrame(movimientos)
    tabla["monto"] = tabla["monto"].map(moneda)
    st.dataframe(
        tabla[["fecha", "tipo", "categoria", "monto"]],
        hide_index=True,
        width="stretch",
    )

    with st.expander("Eliminar un movimiento"):
        opciones = {
            f"{m['fecha']} · {m['tipo']} · {m['categoria']} · {moneda(m['monto'])}": m["id"]
            for m in movimientos
        }
        elegido = st.selectbox("Elige el movimiento", list(opciones))
        if st.button("Eliminar"):
            finanzas.eliminar_movimiento(usuario["id"], opciones[elegido])
            st.rerun()


def seccion_presupuesto(usuario):
    st.header("Presupuesto mensual")
    st.caption("Define cuánto quieres gastar al mes en cada categoría.")

    with st.form("form_presupuesto", clear_on_submit=True):
        categoria = st.selectbox("Categoría", finanzas.CATEGORIAS_GASTO)
        limite = st.number_input("Límite mensual (COP)", min_value=0, step=10000)
        enviar = st.form_submit_button("Guardar límite", width="stretch")
    if enviar:
        ok, mensaje = presupuesto.establecer_limite(usuario["id"], categoria, limite)
        (st.success if ok else st.error)(mensaje)

    estados = presupuesto.estado_presupuesto(usuario["id"])
    if not estados:
        st.info("Aún no has definido límites.")
        return

    st.subheader("Cómo vas este mes")
    for item in estados:
        st.write(f"**{item['categoria']}**: {moneda(item['gastado'])} "
                 f"de {moneda(item['limite'])} ({item['porcentaje']:.0f}%)")
        st.progress(min(item["porcentaje"], 100) / 100)
        if item["estado"] == "excedido":
            st.error("Superaste el límite.")
        elif item["estado"] == "cerca":
            st.warning("Estás cerca del límite.")

    with st.expander("Quitar un límite"):
        elegida = st.selectbox("Categoría", [e["categoria"] for e in estados],
                               key="quitar_limite")
        if st.button("Quitar límite"):
            presupuesto.eliminar_limite(usuario["id"], elegida)
            st.rerun()


def seccion_inversiones(usuario):
    st.header("Simulador de inversiones")
    st.caption("Practica con dinero virtual. Los precios son simulados, no reales.")

    extra = st.session_state.get("dias_extra", 0)
    dia = inversiones.dia_simulado(extra)
    efectivo = inversiones.saldo(usuario["id"])
    posiciones, valor_cartera = inversiones.ver_cartera(usuario["id"], dia)
    total = efectivo + valor_cartera

    st.metric("Patrimonio virtual", moneda(total),
              delta=moneda(total - inversiones.CAPITAL_INICIAL).replace("$-", "-$"))
    col1, col2 = st.columns(2)
    col1.metric("Efectivo", moneda(efectivo))
    col2.metric("En inversiones", moneda(valor_cartera))

    if st.button("⏭ Avanzar un día", width="stretch"):
        st.session_state["dias_extra"] = extra + 1
        st.rerun()
    if extra:
        st.caption(f"Has avanzado {extra} día(s) en la simulación.")

    tab_mercado, tab_operar, tab_cartera = st.tabs(["Mercado", "Operar", "Mi cartera"])

    with tab_mercado:
        filas = []
        for activo in inversiones.ACTIVOS:
            hoy = inversiones.precio(activo, dia)
            ayer = inversiones.precio(activo, dia - 1)
            filas.append({
                "Activo": activo,
                "Precio": moneda(hoy),
                "Cambio del día": f"{(hoy / ayer - 1) * 100:+.1f}%",
            })
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")

    with tab_operar:
        accion = st.radio("Acción", ["Comprar", "Vender"], horizontal=True)
        activo = st.selectbox("Activo", list(inversiones.ACTIVOS))
        cantidad = st.number_input("Cantidad", min_value=1, step=1, value=1)
        precio_unit = inversiones.precio(activo, dia)
        st.write(f"Precio actual: **{moneda(precio_unit)}** · "
                 f"Total: **{moneda(precio_unit * cantidad)}**")
        if st.button(f"{accion} ahora", width="stretch"):
            funcion = inversiones.comprar if accion == "Comprar" else inversiones.vender
            ok, mensaje = funcion(usuario["id"], activo, int(cantidad), precio_unit)
            if ok:
                st.success(mensaje)
                st.rerun()
            else:
                st.error(mensaje)

    with tab_cartera:
        if not posiciones:
            st.info("Aún no tienes inversiones. Compra algo en la pestaña «Operar».")
        else:
            tabla = pd.DataFrame(posiciones)
            for col in ["precio_promedio", "precio_actual", "valor", "ganancia"]:
                tabla[col] = tabla[col].map(moneda)
            tabla["porcentaje"] = tabla["porcentaje"].map(lambda p: f"{p:+.1f}%")
            tabla.columns = ["Activo", "Cantidad", "Precio compra", "Precio actual",
                             "Valor", "Ganancia", "Rendimiento"]
            st.dataframe(tabla, hide_index=True, width="stretch")


def seccion_tutor(usuario):
    st.header("Tutor financiero")
    st.caption("Lee la lección y responde el quiz. Se guarda tu mejor puntaje.")

    avance = tutor.progreso(usuario["id"])
    dominadas = sum(1 for p, t in avance.values() if p == t)
    st.metric("Lecciones dominadas", f"{dominadas} de {len(tutor.LECCIONES)}")
    st.progress(dominadas / len(tutor.LECCIONES))

    titulos = {}
    for leccion in tutor.LECCIONES:
        mejor = avance.get(leccion["id"])
        marca = f" ({mejor[0]}/{mejor[1]})" if mejor else ""
        titulos[leccion["titulo"] + marca] = leccion
    leccion = titulos[st.selectbox("Lección", list(titulos))]

    st.info(leccion["texto"])
    preguntas = leccion["preguntas"]

    with st.form(f"quiz_{leccion['id']}"):
        st.subheader("Quiz")
        respuestas = []
        for i, (enunciado, opciones, _, _) in enumerate(preguntas):
            respuestas.append(st.radio(f"{i + 1}. {enunciado}", opciones,
                                       index=None, key=f"q_{leccion['id']}_{i}"))
        enviar = st.form_submit_button("Calificar", width="stretch")

    if enviar:
        if None in respuestas:
            st.warning("Responde todas las preguntas antes de calificar.")
            return
        aciertos = tutor.calificar(preguntas, respuestas)
        tutor.guardar_resultado(usuario["id"], leccion["id"], aciertos, len(preguntas))
        for (enunciado, opciones, correcta, explicacion), resp in zip(preguntas, respuestas):
            if resp == opciones[correcta]:
                st.success(f"✔ {enunciado} {explicacion}")
            else:
                st.error(f"✘ {enunciado} Correcta: {opciones[correcta]}. {explicacion}")
        st.subheader(f"Puntaje: {aciertos} de {len(preguntas)}")
        if aciertos == len(preguntas):
            st.balloons()


def seccion_pendiente(nombre):
    st.header(nombre)
    st.info("Esta sección se construye en una próxima etapa. 🚧")


# ---------- Programa principal ----------
def main():
    usuario = st.session_state.get("usuario")
    if not usuario:
        pantalla_acceso()
        return

    secciones = {
        "🏠 Inicio": lambda: seccion_inicio(usuario),
        "💵 Ingresos y gastos": lambda: seccion_movimientos(usuario),
        "🎯 Presupuesto": lambda: seccion_presupuesto(usuario),
        "📈 Inversiones": lambda: seccion_inversiones(usuario),
        "🎓 Tutor": lambda: seccion_tutor(usuario),
    }
    with st.sidebar:
        st.write(f"**{usuario['nombre']}**")
        eleccion = st.radio("Menú", list(secciones), label_visibility="collapsed")
        if st.button("Cerrar sesión", width="stretch"):
            st.session_state.clear()
            st.rerun()
    secciones[eleccion]()


main()
