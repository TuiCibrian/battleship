#? Importaciones
import tkinter as tk
import sqlite3 as sql
import random
import winsound

#? Creación de base de datos
conexion = sql.connect("datos.db")
cursor = conexion.cursor()

try:
    cursor.execute("CREATE TABLE estadisticas (ganadas INTEGER, perdidas INTEGER, precision INTEGER)") #TODO: Historial de partidas
    conexion.commit()
except sql.OperationalError:
    pass

#? Funciones
def iniciar_partida():
	if 10>=tablero_anchura.get()>=8 and 10>=tablero_altura.get()>=8:
		inicio_valido_msj.set("Iniciando partida...")
	else: # Caso de datos incorrectos
		inicio_valido_msj.set("Ingrese dimensiones válidas")

#? Opciones de ventana
root = tk.Tk()
root.title("Battleship")
root.state("zoomed")
root.configure(bg="#f5f5f5")

#? Variables
tablero_anchura = tk.IntVar(value=0)
tablero_altura = tk.IntVar(value=0)
inicio_valido_msj = tk.StringVar(value="")

#? Paleta de colores
BG = "#f5f5f5"
FG = "#222222"

#? Interfaz de selección
logo_img = tk.PhotoImage(file="logo.png")
logo_contenedor = tk.Label(root, image=logo_img, height=500) #FIXME: Altura temporal para pruebas
titulo = tk.Label(root, text="Battleship")

lbl_anchura = tk.Label(root, text="Anchura del mapa (8-10):")
entry_anchura = tk.Entry(root, textvariable=tablero_anchura)
lbl_altura = tk.Label(root, text="Altura del mapa (8-10):")
entry_altura = tk.Entry(root,  textvariable=tablero_altura)

btn_iniciar = tk.Button(root, text="Iniciar partida", command=iniciar_partida)
lbl_inicio_valido = tk.Label(root, textvariable=inicio_valido_msj) #No muestra texto a menos que el usuario ingrese mal datos


#? Empaquetado
logo_contenedor.pack()
titulo.pack()

lbl_anchura.pack()
entry_anchura.pack()
lbl_altura.pack()
entry_altura.pack()

btn_iniciar.pack()
lbl_inicio_valido.pack()









#? Bucle principal
root.mainloop()