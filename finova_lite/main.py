"""FINOVA Lite - Menú principal."""
import getpass

import usuarios
from database import crear_tablas


def pedir_clave(mensaje):
    """Pide la contraseña mostrándola en pantalla."""
    return input(mensaje)


def menu_inicio():
    """Menú de bienvenida: registro o login. Devuelve el usuario o None."""
    while True:
        print("\n=== FINOVA Lite ===")
        print("1. Iniciar sesión")
        print("2. Crear cuenta")
        print("0. Salir")
        opcion = input("Elige una opción: ").strip()

        if opcion == "1":
            usuario = input("Usuario: ")
            fila = usuarios.iniciar_sesion(usuario, pedir_clave("Contraseña: "))
            if fila:
                print(f"\n¡Bienvenido, {fila['nombre']}!")
                return fila
            print("Usuario o contraseña incorrectos.")
        elif opcion == "2":
            nombre = input("Nombre completo: ")
            usuario = input("Usuario: ")
            ok, msg = usuarios.registrar(nombre, usuario, pedir_clave("Contraseña: "))
            print(msg)
        elif opcion == "0":
            return None
        else:
            print("Opción no válida.")


def menu_principal(usuario):
    """Menú del usuario con sesión iniciada (se irá llenando por etapas)."""
    while True:
        print(f"\n--- Menú de {usuario['nombre']} ---")
        print("1. Ingresos y gastos   (próxima etapa)")
        print("2. Presupuesto         (próxima etapa)")
        print("3. Simulador de inversiones (próxima etapa)")
        print("4. Tutor financiero    (próxima etapa)")
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        if opcion == "0":
            print("Sesión cerrada.")
            return
        print("Esta función se construye en la siguiente etapa.")


def main():
    crear_tablas()
    usuario = menu_inicio()
    if usuario:
        menu_principal(usuario)
    print("¡Hasta pronto!")


if __name__ == "__main__":
    main()
