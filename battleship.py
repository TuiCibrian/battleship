#? Importaciones
import tkinter as tk
from tkinter import ttk
import sqlite3 as sql
import random
import winsound

#? Creación de base de datos
conexion = sql.connect("datos.db")
cursor 	 = conexion.cursor()

try:
    cursor.execute("CREATE TABLE estadisticas (ganadas INTEGER, perdidas INTEGER, precision INTEGER)") #TODO: Historial de partidas
    conexion.commit()
except sql.OperationalError:
    pass

#? Clases
class Tablero:
	def __init__(self, partida, game_tab, lbl_texto):
		self.partida = partida
		self.game_tab = game_tab
		self.lbl_texto = lbl_texto

	def crear(self):
		cols = tuple(range(1,self.partida.anchura.get()+1))
		tablero = ttk.Treeview(self.game_tab, columns=cols, show="tree headings")
		for col in cols:
			tablero.heading(col, text=col, anchor="center")

		row_headers = "ABCDEFGHIJ"[0:self.partida.altura.get()]
		for row in row_headers:
			tablero.insert("",tk.END, text=row)

		lbl_tablero = tk.Label(self.game_tab, text=self.lbl_texto)

		lbl_tablero.pack()
		tablero.pack()
class Barco:
	def __init__(self):
		tamano = []
		estado = False

class Partida:
	def __init__(self):
		self.anchura 	= tk.IntVar(value=8)
		self.altura 	= tk.IntVar(value=8)
		self.n_barcos 	= tk.IntVar(value=5)	

#? Funciones
#* Validación de dimensiones de tablero válidas
def iniciar_partida():
	if 10>=partida_config.anchura.get()>=8 and 10>=partida_config.altura.get()>=8 and 10>=partida_config.n_barcos.get()>=5:
		inicio_valido_msj.set("Iniciando partida...")
		create_game_tab()
	else: # Caso de datos incorrectos
		inicio_valido_msj.set("Ingrese dimensiones y cantidad de barcos válidos")

def create_game_tab():
	game_tab = tk.Toplevel(root)
	game_tab.state("zoomed")

	tablero_computadora = Tablero(partida_config,game_tab,"Tablero enemigo").crear()
	tablero_jugador = Tablero(partida_config,game_tab,"Tu tablero").crear()



#? Opciones de ventana
root = tk.Tk()
root.title("Battleship")
root.state("zoomed")
root.configure(bg="#f5f5f5")

#? Variables
partida_config = Partida()
inicio_valido_msj = tk.StringVar(value="")

#? Paleta de colores
BG = "#f5f5f5"
FG = "#222222"

#? Interfaz de selección
logo_img = tk.PhotoImage(file="logo.png")
logo_contenedor = tk.Label(root, image=logo_img, height=500)
titulo = tk.Label(root, text="Battleship")

lbl_anchura = tk.Label(root, text="Anchura del mapa (8-10):")
entry_anchura = tk.Entry(root, textvariable=partida_config.anchura)
lbl_altura = tk.Label(root, text="Altura del mapa (8-10):")
entry_altura = tk.Entry(root, textvariable=partida_config.altura)

lbl_n_barcos = tk.Label(root, text="Cantidad de barcos (5-10):")
entry_n_barcos = tk.Entry(root, textvariable=partida_config.n_barcos)

btn_iniciar = tk.Button(root, text="Iniciar partida", command=iniciar_partida)
lbl_inicio_valido = tk.Label(root, textvariable=inicio_valido_msj) #No muestra texto a menos que el usuario ingrese mal datos


#? Empaquetado
logo_contenedor.pack()
titulo.pack()

lbl_anchura.pack()
entry_anchura.pack()
lbl_altura.pack()
entry_altura.pack()

lbl_n_barcos.pack()
entry_n_barcos.pack()

btn_iniciar.pack()
lbl_inicio_valido.pack()







#? Bucle principal
root.mainloop()