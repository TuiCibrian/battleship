
#? Importaciones
import tkinter as tk
from tkinter import ttk, messagebox  # messagebox para diálogos
import sqlite3, random, threading    # Hilos para ejecutar sonidos en paralelo
import winsound

#? Base de datos
con = sqlite3.connect("datos.db")
cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS historial (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha     TEXT DEFAULT (datetime('now','localtime')),
        resultado TEXT,
        disparos  INTEGER,
        impactos  INTEGER,
        precision REAL
    )
""")
con.commit()  # guarda los cambios en el archivo

#? Clases
#* Clase Barco
class Barco:
    # Representa un barco con su tamaño y el seguimiento de golpes recibidos
    def __init__(self, tamano, celdas):
        self.tamano = tamano       # número de celdas que ocupa
        self.celdas = set(celdas)  # posiciones (fila, col) que ocupa, como conjunto
        self.estado = "vivo"       # cambia a "hundido" cuando recibe todos los golpes
        self.golpes = set()        # posiciones ya golpeadas

    def recibir(self, pos):
        # Recibe un disparo en la posición (fila, col)
        if pos not in self.celdas:
            return "agua"          		# el disparo no tocó este barco
        self.golpes.add(pos)       		# registra el golpe
        if self.golpes == self.celdas:  # si todas las celdas fueron golpeadas
            self.estado = "hundido"
            return "hundido"
        return "impacto"           		# golpeado pero aún no hundido

#* Clase Tablero
class Tablero:
    # Representa la cuadrícula de juego y todos los barcos colocados en ella
    def __init__(self, filas, cols):
        self.filas  = filas
        self.cols   = cols
        # Grid 2D inicializado con "~" (agua) en cada celda
        self.grid   = [["~"] * cols for _ in range(filas)]
        self.barcos = []  # lista de objetos Barco colocados

    def colocar(self, f, c, tam, horiz):
        # Intenta colocar un barco de tamaño `tam` desde (f,c)
        # horiz=True y crece hacia la derecha; False y crece hacia abajo
        celdas = [(f, c+i) if horiz else (f+i, c) for i in range(tam)]
        # Verifica que todas las celdas estén dentro del tablero y vacías
        if any(r<0 or r>=self.filas or k<0 or k>=self.cols or self.grid[r][k]!="~"
            for r,k in celdas):
            return False  # posición inválida
        for r,k in celdas:
            self.grid[r][k] = "B"  # marca las celdas como ocupadas por barco
        self.barcos.append(Barco(tam, celdas))  # registra el barco
        return True

    def colocar_random(self, tam):
        # Intenta hasta 200 veces colocar un barco en posición aleatoria
        for _ in range(200):
            f = random.randint(0, self.filas-1)
            c = random.randint(0, self.cols-1)
            if self.colocar(f, c, tam, random.choice([True, False])):
                return  # éxito, termina el bucle

    def disparar(self, f, c):
        # Procesa un disparo en la celda (f, c) y devuelve el resultado
        if self.grid[f][c] in ("X","H","O"):
            return "ya"  # celda ya disparada anteriormente
        for b in self.barcos:
            res = b.recibir((f, c))  # pregunta a cada barco si fue golpeado
            if res == "hundido":
                for r,k in b.celdas:
                    self.grid[r][k] = "H"  # marca todas las celdas del barco como hundidas
                return "hundido"
            if res == "impacto":
                self.grid[f][c] = "X"  # marca la celda como impactada
                return "impacto"
        self.grid[f][c] = "O"  # ningún barco fue alcanzado y fallo
        return "agua"

    def todos_hundidos(self):
        # Devuelve True si todos los barcos del tablero están hundidos
        return all(b.estado == "hundido" for b in self.barcos)


class Partida:
    # Almacena el estado completo de una partida en curso
    def __init__(self, cols, filas, n):
        self.cols   = cols
        self.filas  = filas
        self.n      = n                          # cantidad de barcos por jugador
        self.tj     = Tablero(filas, cols)       # tablero del jugador
        self.te     = Tablero(filas, cols)       # tablero del enemigo (IA)
        self.disparos  = 0                       # total de disparos del jugador
        self.impactos  = 0                       # disparos que dieron en un barco
        self.turno     = "jugador"               # de quién es el turno
        self.fase      = "colocar"               # fase actual: colocar | batalla | fin
        self.pendientes = list(range(n, 0, -1))  # tamaños de barcos aún por colocar
        self.horiz     = True                    # orientación actual del barco a colocar
        self.cola_ia   = []                      # celdas prioritarias para la IA

    def precision(self):
        # Porcentaje de disparos que dieron en un barco
        if self.disparos == 0:
            return 0.0
        return round(self.impactos / self.disparos * 100, 1)

    def disparo_ia(self):
        # Elige la celda que disparará la IA
        if self.cola_ia:
            return self.cola_ia.pop(0)  # usa la cola de celdas prioritarias si hay
        # Si no, dispara aleatoriamente a celdas no disparadas
        libres = [(r,c) for r in range(self.filas) for c in range(self.cols)
                if self.tj.grid[r][c] in ("~","B")]
        return random.choice(libres)

    def encolar_ia(self, f, c):
        # Tras un impacto, agrega las 4 celdas adyacentes a la cola de la IA
        for df,dc in [(-1,0),(1,0),(0,-1),(0,1)]:  # arriba, abajo, izquierda, derecha
            r, k = f+df, c+dc
            # Solo agrega si está dentro del tablero, no disparada y no está ya en cola
            if 0<=r<self.filas and 0<=k<self.cols \
            and self.tj.grid[r][k] in ("~","B") \
            and (r,k) not in self.cola_ia:
                self.cola_ia.append((r,k))

def sonido(tipo):
        # Diccionario de sonidos (frecuencia en hz, duración en ms)
        notas = {
            "colocar":  [(600, 80)],
            "agua":     [(1200, 60)],
            "impacto":  [(400, 200)],
            "hundido":  [(300,120),(200,120),(150,120)],
            "victoria": [(523,150),(659,150),(784,150),(1047,150)],
            "derrota":  [(400,200),(300,200),(200,200)],
        }
        # Ejecuta los sonidos en un hilo separado para no bloquear la interfaz
        threading.Thread(
            target=lambda: [winsound.Beep(f,d) for f,d in notas.get(tipo,[])],
            daemon=True  # el hilo muere si cierra el programa
        ).start()


#? Constantes de la interfaz
LETRAS = "ABCDEFGHIJ"  	# etiquetas de filas (A, B, C...)
CS = 40   				# tamaño de cada celda en píxeles
HS = 26   				# tamaño de la cabecera de filas/columnas en píxeles

COLORES = {
    "~": "#1b3a5c",      # agua (celda vacía)
    "B": "#06d6a0",      # barco propio (solo visible en tu tablero)
    "X": "#e63946",      # impacto
    "H": "#78909c",      # hundido
    "O": "#e0f7fa",      # fallo (disparo al agua)
    "hover":   "#2176ae",  # celda resaltada al pasar el mouse
    "preview": "#4fc3f7",  # preview de dónde quedará el barco al colocarlo
}

#? Ventana raíz
root = tk.Tk()
root.title("Batalla Naval")
root.configure(bg="#0d1b2a")
root.state("zoomed")

partida = None  # variable global que guarda la partida activa

#? Funciones de dibujo
def cel_desde_evento(event, tab):
    # Convierte coordenadas de pixel (event.x, event.y) a celda (fila, col)
    c = (event.x - HS) // CS  # columna
    r = (event.y - HS) // CS  # fila
    if 0 <= r < tab.filas and 0 <= c < tab.cols:
        return r, c  # celda válida dentro del tablero
    return None  # el mouse está fuera del tablero

def dibujar(cv, tab, revelar, hover=None, preview=None):
    # Dibuja un tablero completo en el canvas `cv`
    # revelar=True muestra los barcos (tablero propio); False los oculta (tablero enemigo)
    cv.delete("all")                   # borra el canvas antes de redibujar
    w = HS + tab.cols * CS             # ancho total del canvas
    h = HS + tab.filas * CS            # alto total del canvas
    cv.config(width=w, height=h)       # ajusta el tamaño del canvas

    for r in range(tab.filas):
        for c in range(tab.cols):
            x1, y1 = HS + c*CS, HS + r*CS  # esquina superior izquierda de la celda
            v = tab.grid[r][c]              # valor de la celda ("~","B","X","H","O")
            # Si es barco pero no se revela, se muestra como agua
            color = COLORES[v] if (v != "B" or revelar) else COLORES["~"]
            if preview and (r,c) in preview:
                color = COLORES["preview"]    # preview de colocación (azul claro)
            if hover == (r,c) and color == COLORES["~"]:
                color = COLORES["hover"]      # resalte al pasar el mouse (solo en agua)
            cv.create_rectangle(x1, y1, x1+CS, y1+CS,
                                fill=color, outline="#0d1b2a", width=1)

    # Dibuja los números de columna en la cabecera superior
    for c in range(tab.cols):
        cv.create_text(HS + c*CS + CS//2, HS//2,
                    text=str(c+1), fill="#e0f7fa", font=("Courier New", 8))
    # Dibuja las letras de fila en la cabecera izquierda
    for r in range(tab.filas):
        cv.create_text(HS//2, HS + r*CS + CS//2,
                    text=LETRAS[r], fill="#e0f7fa", font=("Courier New", 8))

def redibujar(hover_j=None, hover_e=None):
    # Redibuja ambos tableros y actualiza el label de información
    p = partida

    # Calcula el preview del barco a colocar si el mouse está sobre el tablero jugador
    prev = None
    if p.fase == "colocar" and hover_j and p.pendientes:
        tam = p.pendientes[0]  # tamaño del barco que se está colocando
        # Genera la lista de celdas que ocuparía el barco según orientación
        celdas = [(hover_j[0], hover_j[1]+i) if p.horiz
                else (hover_j[0]+i, hover_j[1]) for i in range(tam)]
        # Filtra las celdas que estén dentro del tablero
        prev = [cel for cel in celdas if 0<=cel[0]<p.tj.filas and 0<=cel[1]<p.tj.cols]

    dibujar(cv_j, p.tj, True,           hover_j, prev)  # tablero jugador (revela barcos)
    dibujar(cv_e, p.te, p.fase=="fin",  hover_e)         # tablero enemigo (oculta barcos salvo al final)

    # Actualiza el texto de información según la fase actual
    if p.fase == "colocar":
        tam    = p.pendientes[0] if p.pendientes else 0
        orient = "Horizontal" if p.horiz else "Vertical"
        lbl_info.config(
            text=f"Coloca tu barco de tamaño {tam} [{orient}] — Clic der: rotar  ({len(p.pendientes)} restantes)",
            fg="#4fc3f7")
    elif p.fase == "batalla":
        txt = "Tu turno — dispara en el tablero enemigo" if p.turno=="jugador" else "Turno enemigo..."
        lbl_info.config(
            text=f"{txt}   |   Disparos: {p.disparos}  Impactos: {p.impactos}  Precisión: {p.precision()}%",
            fg="#ffd166" if p.turno=="jugador" else "#e63946")
    elif p.fase == "fin":
        lbl_info.config(
            text=f"Partida terminada  |  Disparos: {p.disparos}  Impactos: {p.impactos}  Precisión: {p.precision()}%",
            fg="#e0f7fa")

#? Eventos del tablero jugador (fase: colocar barcos)

def hover_j(event):
    # Cuando el mouse se mueve sobre el tablero jugador, muestra el preview del barco
    if partida.fase != "colocar": return  # solo activo en fase de colocación
    redibujar(hover_j=cel_desde_evento(event, partida.tj))

def click_j(event):
    # Cuando el jugador hace clic en su tablero, intenta colocar el siguiente barco
    p = partida
    if p.fase != "colocar" or not p.pendientes: return
    cel = cel_desde_evento(event, p.tj)
    if not cel: return  # clic fuera del tablero
    if p.tj.colocar(cel[0], cel[1], p.pendientes[0], p.horiz):  # intenta colocar
        p.pendientes.pop(0)  # elimina el barco de la lista de pendientes
        sonido("colocar")
        if not p.pendientes:       # si ya no quedan barcos por colocar
            p.fase = "batalla"     # pasa a la fase de batalla
    redibujar()

def rotar(event=None):
    # Alterna la orientación del barco entre Horizontal y Vertical
    if partida.fase == "colocar":
        partida.horiz = not partida.horiz  # True y False o False y True
        redibujar()

#? Eventos del tablero enemigo (fase: batalla)

def hover_e(event):
    # Resalta la celda bajo el mouse en el tablero enemigo durante el turno del jugador
    if partida.fase != "batalla" or partida.turno != "jugador": return
    redibujar(hover_e=cel_desde_evento(event, partida.te))

def click_e(event):
    # El jugador dispara al tablero enemigo haciendo clic
    p = partida
    if p.fase != "batalla" or p.turno != "jugador": return  # solo en turno del jugador
    cel = cel_desde_evento(event, p.te)
    if not cel: return
    res = p.te.disparar(cel[0], cel[1])  # dispara y obtiene resultado
    if res == "ya": return               # celda ya disparada, no hace nada
    p.disparos += 1                      # incrementa el contador de disparos
    if res in ("impacto","hundido"):
        p.impactos += 1                  # incrementa impactos si dio en un barco
    sonido("hundido" if res=="hundido" else "impacto" if res=="impacto" else "agua")
    redibujar()
    if p.te.todos_hundidos():            # si hundió toda la flota enemiga y gana
        fin("victoria"); return
    p.turno = "enemigo"                  # pasa el turno a la IA
    redibujar()
    root.after(600, turno_ia)            # espera 600ms antes del turno de la IA

def turno_ia():
    # Ejecuta el disparo de la IA en el tablero del jugador
    p = partida
    f, c = p.disparo_ia()               # elige la celda (inteligente o aleatoria)
    res  = p.tj.disparar(f, c)          # dispara en el tablero del jugador
    if res == "ya":
        root.after(100, turno_ia); return  # celda ya usada, reintenta rápido
    if res == "impacto":
        p.encolar_ia(f, c)              # tras impacto, prioriza celdas adyacentes
    sonido("hundido" if res=="hundido" else "impacto" if res=="impacto" else "agua")
    redibujar()
    if p.tj.todos_hundidos():           # si hundió toda la flota del jugador y pierde
        fin("derrota"); return
    p.turno = "jugador"                 # devuelve el turno al jugador
    redibujar()

#? Fin de partida
def fin(resultado):
    p = partida
    p.fase = "fin"                      # marca la partida como terminada
    sonido("victoria" if resultado=="victoria" else "derrota")
    # Guarda el resultado en la base de datos
    cur.execute(
        "INSERT INTO historial (resultado,disparos,impactos,precision) VALUES (?,?,?,?)",
        (resultado, p.disparos, p.impactos, p.precision())
    )
    con.commit()  # persiste en el archivo .db
    redibujar()   # muestra el tablero enemigo revelado
    emoji = "¡VICTORIA!" if resultado=="victoria" else "DERROTA"
    # Pregunta si quiere jugar de nuevo; askyesno devuelve True o False
    if messagebox.askyesno("Fin", f"{emoji}\n\nDisparos: {p.disparos}  Impactos: {p.impactos}  Precisión: {p.precision()}%\n\n¿Jugar de nuevo?"):
        iniciar()  # reinicia la partida con la misma configuración

#? Iniciar / reiniciar partida
def iniciar():
    global partida  # modifica la variable global
    cols  = v_cols.get()   # lee el IntVar de columnas
    filas = v_filas.get()  # lee el IntVar de filas
    n     = v_n.get()      # lee el IntVar de barcos
    if not (8<=cols<=10 and 8<=filas<=10 and 5<=n<=10):
        lbl_err.config(text="Valores fuera de rango (cols/filas: 8-10, barcos: 5-10)")
        return
    lbl_err.config(text="")            # limpia el mensaje de error
    partida = Partida(cols, filas, n)  # crea una nueva partida
    for tam in range(n, 0, -1):
        partida.te.colocar_random(tam) # la IA coloca sus barcos aleatoriamente
    redibujar()

#? Historial de partidas
def ver_historial():
    # Abre una ventana secundaria con el historial de partidas guardadas en SQLite
    win = tk.Toplevel(root)
    win.title("Historial")
    win.configure(bg="#0d1b2a")
    win.resizable(False, False)
    tk.Label(win, text="HISTORIAL DE PARTIDAS", font=("Georgia",13,"bold"),
            bg="#0d1b2a", fg="#ffd166").pack(pady=12)
    # Treeview: tabla con columnas definidas
    cols = ("Fecha","Resultado","Disparos","Impactos","Precisión")
    t = ttk.Treeview(win, columns=cols, show="headings", height=12)
    ttk.Style().configure("Treeview", background="#1b3a5c",
                        foreground="white", fieldbackground="#1b3a5c")
    for col in cols:
        t.heading(col, text=col)               # cabecera de cada columna
        t.column(col, width=115, anchor="center")
    # Consulta las últimas 20 partidas ordenadas por más reciente
    for row in cur.execute(
        "SELECT fecha,resultado,disparos,impactos,precision FROM historial ORDER BY id DESC LIMIT 20"
    ):
        t.insert("","end", values=row)         # inserta cada fila en la tabla
    t.pack(padx=16, pady=4)
    tk.Button(win, text="Cerrar", bg="#2176ae", fg="white", relief="flat",
            cursor="hand2", padx=14, pady=6, command=win.destroy).pack(pady=10)

#? Construcción de la interfaz
# Barra superior con título y botón de historial
top = tk.Frame(root, bg="#1b3a5c", pady=6)
top.pack(fill="x")
tk.Label(top, text="BATALLA NAVAL", font=("Georgia",14,"bold"),
        bg="#1b3a5c", fg="#ffd166").pack(side="left", padx=16)
tk.Button(top, text="Historial", font=("Courier New",9), bg="#1b3a5c",
        fg="#ffd166", relief="flat", cursor="hand2",
        command=ver_historial).pack(side="right", padx=8)

# Barra de configuración con entradas vinculadas a IntVar
cfg = tk.Frame(root, bg="#0d1b2a", pady=8)
cfg.pack(fill="x")
v_cols  = tk.IntVar(value=8)  # columnas del tablero (valor por defecto: 8)
v_filas = tk.IntVar(value=8)  # filas del tablero
v_n     = tk.IntVar(value=5)  # cantidad de barcos
# Crea los 3 pares label+entry con un for
for i, (txt, var) in enumerate([("Columnas (8-10):", v_cols),
                                ("Filas (8-10):",    v_filas),
                                ("Barcos (5-10):",   v_n)]):
    tk.Label(cfg, text=txt, font=("Courier New",10), bg="#0d1b2a",
            fg="#e0f7fa").grid(row=0, column=i*2, padx=(16,4))
    tk.Entry(cfg, textvariable=var, width=4, font=("Courier New",10),
            bg="#1b3a5c", fg="white", insertbackground="white",
            relief="flat", justify="center").grid(row=0, column=i*2+1, padx=(0,8))
tk.Button(cfg, text="▶ Iniciar", font=("Courier New",10,"bold"),
        bg="#2176ae", fg="white", relief="flat", padx=12, pady=4,
        cursor="hand2", command=iniciar).grid(row=0, column=6, padx=16)
tk.Button(cfg, text="Rotar [clic der]", font=("Courier New",9),
        bg="#0d1b2a", fg="#4fc3f7", relief="flat", cursor="hand2",
        command=rotar).grid(row=0, column=7, padx=4)
lbl_err = tk.Label(cfg, text="", font=("Courier New",9), bg="#0d1b2a", fg="#e63946")
lbl_err.grid(row=0, column=8, padx=8)  # label de error (vacío hasta que haya un error)

# Label de información de turno/fase (se actualiza en redibujar())
lbl_info = tk.Label(root, text="Configura e inicia una partida",
                    font=("Courier New",10,"bold"), bg="#0d1b2a", fg="#e0f7fa")
lbl_info.pack(pady=4)

# Frame central con los dos tableros uno al lado del otro
body = tk.Frame(root, bg="#0d1b2a")
body.pack(expand=True)

tk.Label(body, text="TU FLOTA", font=("Courier New",9,"bold"),
        bg="#0d1b2a", fg="#06d6a0").grid(row=0, column=0, pady=(8,2))
tk.Label(body, text="FLOTA ENEMIGA", font=("Courier New",9,"bold"),
        bg="#0d1b2a", fg="#e63946").grid(row=0, column=1, pady=(8,2))

cv_j = tk.Canvas(body, bg="#0d1b2a", highlightthickness=0)  # canvas tablero jugador
cv_j.grid(row=1, column=0, padx=20, pady=4)
cv_e = tk.Canvas(body, bg="#0d1b2a", highlightthickness=0)  # canvas tablero enemigo
cv_e.grid(row=1, column=1, padx=20, pady=4)

# Enlaza eventos del mouse a las funciones correspondientes
cv_j.bind("<Motion>",   hover_j)              # mouse se mueve sobre tablero jugador
cv_j.bind("<Leave>",    lambda e: redibujar()) # mouse sale del tablero y limpia hover
cv_j.bind("<Button-1>", click_j)              # clic izquierdo y colocar barco
cv_j.bind("<Button-3>", rotar)                # clic derecho y rotar barco
cv_e.bind("<Motion>",   hover_e)              # mouse se mueve sobre tablero enemigo
cv_e.bind("<Leave>",    lambda e: redibujar()) # mouse sale del tablero y limpia hover
cv_e.bind("<Button-1>", click_e)              # clic izquierdo y disparar

# Leyenda de colores en la parte inferior
ley = tk.Frame(root, bg="#0d1b2a")
ley.pack(pady=6)
for color, txt in [("#06d6a0","Barco"),("#e63946","Impacto"),
                ("#78909c","Hundido"),("#e0f7fa","Fallo"),("#1b3a5c","Agua")]:
    tk.Label(ley, text=f"■ {txt}", font=("Courier New",9),
            bg="#0d1b2a", fg=color).pack(side="left", padx=10)

#? Bucle principal
root.mainloop()  # inicia el ciclo de eventos de Tkinter; sin esto la ventana se cierra
con.close()      # cierra la conexión a SQLite al salir