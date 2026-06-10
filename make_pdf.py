#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el informe PDF EDFO sobre la 1.a vuelta presidencial de Colombia 2026."""
from fpdf import FPDF

# --- Paleta de marca EDFO ---
NAVY = (0, 34, 68)       # #002244
GOLD = (198, 172, 132)   # #C6AC84
GREEN = (5, 128, 8)      # #058008
INK = (26, 25, 21)
GRAY = (107, 101, 87)
LINE = (214, 209, 196)
SOFT = (245, 243, 238)
WHITE = (255, 255, 255)
ORANGE = (206, 116, 42)  # De la Espriella
PURPLE = (140, 55, 140)  # Cepeda
BLUE = (41, 128, 185)    # Valencia


def miles(n):
    return f"{int(n):,}".replace(",", ".")


class PDF(FPDF):
    section = ""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*NAVY)
        self.rect(15, 10, 7, 7, "F")
        self.set_text_color(*GOLD)
        self.set_font("Helvetica", "B", 6)
        self.set_xy(15, 11.6)
        self.cell(7, 4, "ED", align="C")
        self.set_xy(25, 9.8)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 9)
        self.cell(60, 4, "ECKARDT DAGER")
        self.set_xy(25, 14)
        self.set_text_color(*GOLD)
        self.set_font("Helvetica", "", 6.5)
        self.cell(60, 3, "FAMILY OFFICE")
        self.set_xy(110, 12)
        self.set_text_color(*GRAY)
        self.set_font("Helvetica", "", 7.5)
        self.cell(85, 4, self.section, align="R")
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(15, 20, 195, 20)
        self.set_y(27)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_draw_color(*LINE)
        self.set_line_width(0.2)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GRAY)
        self.cell(90, 5, "Documento confidencial  ·  www.eckardtdager.com")
        self.cell(90, 5, f"Pagina {self.page_no() - 1}", align="R")


pdf = PDF(format="A4")
pdf.set_auto_page_break(True, margin=18)


def titulo(t):
    if pdf.get_y() > 250:
        pdf.add_page()
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, t)
    y = pdf.get_y() + 8.5
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.7)
    pdf.line(15, y, 42, y)
    pdf.set_y(y + 3.5)


def parrafo(t, size=10, color=INK, gap=2):
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*color)
    pdf.multi_cell(180, 5.2, t)
    pdf.set_y(pdf.get_y() + gap)


def vineta(t, bold_head=None):
    y = pdf.get_y()
    if y > 262:
        pdf.add_page()
        y = pdf.get_y()
    pdf.set_fill_color(*GOLD)
    pdf.rect(16, y + 1.7, 2.2, 2.2, "F")
    pdf.set_xy(21, y)
    pdf.set_text_color(*INK)
    if bold_head:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        w = pdf.get_string_width(bold_head + " ")
        pdf.cell(w, 5.2, bold_head + " ")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*INK)
        pdf.multi_cell(180 - 6 - w, 5.2, t)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(174, 5.2, t)
    pdf.set_y(pdf.get_y() + 1.5)


def barra_cand(nombre, pct, votos, color, maxpct):
    y = pdf.get_y()
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*INK)
    pdf.set_xy(15, y)
    pdf.cell(52, 6, nombre)
    bx, bw = 70, 95
    pdf.set_fill_color(*LINE)
    pdf.rect(bx, y + 1, bw, 4.2, "F")
    pdf.set_fill_color(*color)
    pdf.rect(bx, y + 1, bw * pct / maxpct, 4.2, "F")
    pdf.set_xy(bx + bw + 3, y)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(15, 6, f"{pct:.2f}%".replace(".", ","))
    pdf.set_xy(bx + bw + 18, y)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, miles(votos))
    pdf.set_y(y + 6.6)


# ============================ PORTADA ============================
pdf.add_page()
pdf.set_fill_color(*NAVY)
pdf.rect(0, 0, 210, 297, "F")
# franja dorada decorativa
pdf.set_fill_color(*GOLD)
pdf.rect(0, 0, 210, 3, "F")
pdf.rect(0, 294, 210, 3, "F")
# Monograma
cx, cy = 105, 62
pdf.set_draw_color(*GOLD)
pdf.set_line_width(1.6)
pdf.rect(cx - 19, cy - 19, 38, 38)
pdf.set_line_width(0.5)
pdf.rect(cx - 15, cy - 15, 30, 30)
pdf.set_text_color(*GOLD)
pdf.set_font("Helvetica", "B", 30)
pdf.set_xy(cx - 19, cy - 11)
pdf.cell(38, 20, "ED", align="C")
# Wordmark
pdf.set_text_color(*WHITE)
pdf.set_font("Helvetica", "B", 30)
pdf.set_xy(0, 100)
pdf.cell(210, 12, "ECKARDT DAGER", align="C")
pdf.set_text_color(*GOLD)
pdf.set_font("Helvetica", "", 12)
pdf.set_xy(0, 114)
pdf.cell(210, 6, "F A M I L Y   O F F I C E", align="C")
pdf.set_draw_color(*GOLD)
pdf.set_line_width(0.6)
pdf.line(80, 130, 130, 130)
# Titulo
pdf.set_text_color(*WHITE)
pdf.set_font("Helvetica", "B", 20)
pdf.set_xy(20, 150)
pdf.multi_cell(170, 9, "Elecciones Presidenciales\nde Colombia 2026", align="C")
pdf.set_text_color(*GOLD)
pdf.set_font("Helvetica", "", 12.5)
pdf.set_xy(20, 178)
pdf.multi_cell(170, 6, "Primera vuelta  ·  Analisis macro-politico e implicaciones", align="C")
# Caja datos clave
pdf.set_fill_color(8, 46, 82)
pdf.rect(45, 198, 120, 26, "F")
pdf.set_draw_color(*GOLD)
pdf.set_line_width(0.4)
pdf.rect(45, 198, 120, 26)
pdf.set_text_color(*WHITE)
pdf.set_font("Helvetica", "B", 11)
pdf.set_xy(45, 203)
pdf.cell(120, 6, "A. de la Espriella 43,74%   |   I. Cepeda 40,91%", align="C")
pdf.set_text_color(*GOLD)
pdf.set_font("Helvetica", "", 9)
pdf.set_xy(45, 211)
pdf.cell(120, 5, "Se define en segunda vuelta el 21 de junio de 2026", align="C")
# Pie de portada
pdf.set_text_color(200, 196, 186)
pdf.set_font("Helvetica", "", 9)
pdf.set_xy(20, 250)
pdf.multi_cell(170, 5,
               "Corte oficial Registraduria Nacional: 31 de mayo de 2026, 7:23 p.m. (99,95% de mesas).\n"
               "Documento confidencial preparado para inversionistas, socios y clientes de EDFO.", align="C")

# ============================ RESUMEN EJECUTIVO ============================
pdf.section = "Resumen ejecutivo"
pdf.add_page()
titulo("Resumen ejecutivo")
parrafo("La primera vuelta presidencial del 31 de mayo de 2026 dejo un resultado historico y "
        "ajustado: Abelardo de la Espriella (Defensores de la Patria, centro-derecha) encabezo "
        "con 43,74% frente a Ivan Cepeda (Pacto Historico, izquierda) con 40,91%. Ambos disputaran "
        "la segunda vuelta el 21 de junio. Estas son las conclusiones para la toma de decisiones:")
vineta("De la Espriella superó a Cepeda por 2,83 puntos (cerca de 670.000 votos), uno de los "
       "margenes mas estrechos de la historia reciente; nadie alcanzo el 50% requerido.",
       "Resultado abierto.")
vineta("La suma de la centro-derecha (De la Espriella + Valencia) llega a 50,66%, por encima de "
       "Cepeda; pero los votos no se transfieren en bloque de forma automatica.", "Aritmetica de bloques.")
vineta("Todas las encuestas de mayo daban a Cepeda como primero; el ascenso de De la Espriella fue "
       "la gran sorpresa. La firma mas cercana al resultado fue AtlasIntel.", "Sorpresa demoscopica.")
vineta("El mercado de prediccion (Polymarket) asigna hoy cerca de 80% de probabilidad a De la "
       "Espriella para la Presidencia, frente a 16% de Cepeda.", "Mercado.")
vineta("La lectura de consenso es de un sesgo pro-mercado ante una eventual presidencia de "
       "centro-derecha, con alta volatilidad cambiaria y de tasas hasta el balotaje.", "Implicacion para portafolios.")

# ============================ RESULTADO NACIONAL ============================
pdf.section = "Resultado nacional"
titulo("Resultado nacional")
parrafo("Distribucion de la votacion valida con 99,95% de mesas escrutadas (boletin oficial):")
cands = [
    ("Abelardo de la Espriella", 43.74, 10355589, ORANGE),
    ("Ivan Cepeda Castro", 40.91, 9685737, PURPLE),
    ("Paloma Valencia Laserna", 6.92, 1638810, BLUE),
    ("Sergio Fajardo Valderrama", 4.25, 1008444, GRAY),
    ("Voto en blanco", 1.71, 406920, LINE),
]
for n, p, v, c in cands:
    barra_cand(n, p, v, c, 45)
pdf.set_y(pdf.get_y() + 2)
parrafo("Participacion: 57,86% del censo (24,0 millones de votantes de 41,4 millones habilitados). "
        "Abstencion: 42,13%. La participacion fue mas alta que el promedio reciente, senal de una "
        "ciudadania movilizada y polarizada.", gap=1)

# ============================ DISTRIBUCION REGIONAL ============================
pdf.section = "Mapa regional"
titulo("Distribucion regional")
parrafo("El resultado dibuja dos colombias. Cepeda gano 18 departamentos y De la Espriella 16 "
        "(incluido el voto en el exterior). El patron geografico es nitido:")
vineta("Domina la periferia: costa Pacifica (Choco, Cauca, Narino, Valle), costa Caribe "
       "(Atlantico, Bolivar, Magdalena, Cordoba, La Guajira), Amazonia y Bogota D.C.", "Cepeda (izquierda).")
vineta("Domina el interior andino y los Llanos: Antioquia, eje cafetero (Caldas, Quindio, "
       "Risaralda), Santanderes, Boyaca, Cundinamarca, Tolima, Huila, Casanare y Meta.", "De la Espriella (derecha).")
vineta("Su mejor desempeno se concentra en el eje cafetero y Antioquia (Caldas 12,6%; Manizales "
       "10,9%), un electorado de centro-derecha clave como fiel de la balanza en la segunda vuelta.", "Valencia (3.er lugar).")

# ============================ VOTO EN EL EXTERIOR ============================
pdf.section = "Voto en el exterior"
titulo("Colombianos en el exterior")
parrafo("Votaron 579.583 colombianos en 67 paises. El voto exterior favorecio claramente a De la "
        "Espriella (cerca de 54%), traccionado por el gran bloque de Estados Unidos, donde supero el "
        "70%. La excepcion relevante es Espana - el segundo mayor padron en el exterior - donde se "
        "impuso Cepeda. El voto exterior, aunque minoritario en el total, refuerza la ventaja de la "
        "centro-derecha y su narrativa de cara al balotaje.")

# ============================ ESCENARIOS 2a VUELTA ============================
pdf.section = "Escenarios 2.a vuelta"
titulo("Escenarios para la segunda vuelta")
parrafo("El 21 de junio se enfrentan dos proyectos opuestos. La clave es la transferencia de los "
        "votos de los eliminados (Valencia, Fajardo y otros) y el comportamiento de la abstencion.")
vineta("La centro-derecha (De la Espriella + Valencia) parte de 50,66% frente a 40,91% de Cepeda. "
       "Si esa coalicion se consolida, De la Espriella es favorito.", "Punto de partida.")
vineta("El votante de Fajardo y del centro (cerca de 5-6%) es disputado y menos disciplinado; su "
       "reparto y la movilizacion seran decisivos.", "El centro decide.")
vineta("Historia reciente: en 2022 Petro paso de 40,3% a 50,4% y en 2014 Santos remonto desde el "
       "segundo lugar. Las segundas vueltas reordenan el mapa; nada esta definido.", "Precedente.")
parrafo("Comparacion con 2022: el bloque de derecha de hoy (50,7%) es similar al que sumaron "
        "Rodolfo Hernandez + Fico Gutierrez en la primera vuelta de 2022 (52,1%); aquella derecha "
        "perdio el balotaje por no consolidarse. Es la principal advertencia para el escenario actual.")

# ============================ ENCUESTAS VS REALIDAD ============================
pdf.section = "Encuestas vs. realidad"
titulo("Encuestas frente al resultado")
parrafo("Ninguna encuestadora de mayo acerto el orden: todas situaban a Cepeda primero. El ascenso "
        "de De la Espriella no fue plenamente capturado. Error medio frente al resultado real "
        "(promedio de la diferencia absoluta en los cuatro candidatos principales):")
encuestas = [
    ("AtlasIntel", "18-21 may", 4.5, True),
    ("Invamer", "13-20 may", 6.2, False),
    ("CNC", "16-22 may", 7.0, False),
    ("Guarumo-EcoAnalitica", "11-19 may", 9.0, False),
    ("CELAG", "mayo", 9.2, False),
]
y = pdf.get_y()
pdf.set_fill_color(*NAVY)
pdf.rect(15, y, 180, 7, "F")
pdf.set_text_color(*WHITE)
pdf.set_font("Helvetica", "B", 9)
pdf.set_xy(17, y)
pdf.cell(90, 7, "Encuestadora")
pdf.cell(45, 7, "Trabajo de campo")
pdf.cell(40, 7, "Error medio (pts)")
pdf.set_y(y + 7)
for i, (f, fch, e, best) in enumerate(encuestas):
    yy = pdf.get_y()
    pdf.set_fill_color(*(SOFT if best else WHITE))
    pdf.rect(15, yy, 180, 7, "F")
    pdf.set_xy(17, yy)
    pdf.set_font("Helvetica", "B" if best else "", 9)
    pdf.set_text_color(*(GREEN if best else INK))
    pdf.cell(90, 7, ("* " if best else "  ") + f)
    pdf.set_text_color(*GRAY)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(45, 7, fch + " 2026")
    pdf.set_text_color(*(GREEN if best else INK))
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(40, 7, f"{e:.1f}".replace(".", ","))
    pdf.set_draw_color(*LINE)
    pdf.line(15, yy + 7, 195, yy + 7)
    pdf.set_y(yy + 7)
pdf.set_y(pdf.get_y() + 3)
parrafo("AtlasIntel fue la unica que reflejo una carrera apretada con De la Espriella en ascenso, "
        "por lo que resulto la mas precisa. Conviene ponderar las encuestas de la segunda vuelta con "
        "ese sesgo en mente.", gap=1)

# ============================ MERCADO ============================
pdf.section = "Mercado de prediccion"
titulo("Mercado de prediccion (Polymarket)")
parrafo("Las probabilidades implicitas del mercado - que no son encuestas ni resultados oficiales, "
        "sino apuestas - se movieron con fuerza tras conocerse el resultado:")
vineta("Ganador de la 1.a vuelta: De la Espriella, cerca de 99%.")
vineta("Dupla que pasa a 2.a vuelta: De la Espriella y Cepeda, cerca de 98%.")
vineta("Ganador de la Presidencia (2.a vuelta): De la Espriella cerca de 80%, Cepeda cerca de 16%.")
parrafo("El mercado, por tanto, ya descuenta una ventaja considerable de la centro-derecha, pero "
        "deja un margen de incertidumbre coherente con la estrechez del resultado.", gap=1)

# ============================ LECTURA PARA INVERSION ============================
pdf.section = "Lectura para inversion"
titulo("Lectura para inversion")
parrafo("Lo que sigue es un analisis general de implicaciones de mercado, no una recomendacion "
        "personalizada (vease el aviso legal). El eje del debate es la continuidad del actual "
        "proyecto de gobierno (Cepeda) frente a un giro de centro-derecha (De la Espriella).")
vineta("Un desenlace percibido como pro-mercado (De la Espriella) tiende a asociarse con "
       "apreciacion del peso (COP); la estrechez del resultado sugiere alta volatilidad cambiaria "
       "hasta el 21 de junio. Recomendable contemplar coberturas.", "Divisa (COP).")
vineta("El Colcap y los sectores regulados (energia, hidrocarburos, financiero, servicios "
       "publicos) serian los mas sensibles a los escenarios; un giro ortodoxo suele favorecer "
       "el apetito por renta variable local.", "Renta variable.")
vineta("Los spreads de deuda soberana (CDS, TES) reflejan la prima de riesgo politico; un "
       "resultado leido como fiscalmente ortodoxo tenderia a comprimirlos.", "Renta fija.")
vineta("La postura sobre exploracion de hidrocarburos y transicion energetica es un eje clave: "
       "un sesgo pro-hidrocarburos suele leerse como favorable para Ecopetrol y el sector.", "Energia.")
vineta("Mantener flexibilidad y escalonar la exposicion hasta conocer el desenlace del balotaje "
       "reduce el riesgo de actuar sobre un resultado de primera vuelta no concluyente.", "Postura tactica.")

# ============================ RIESGOS ============================
pdf.section = "Riesgos y conclusion"
titulo("Riesgos clave a vigilar")
vineta("Transferencia incierta de votos del centro y posible no consolidacion de la coalicion de "
       "derecha (el escenario que costo el balotaje a la derecha en 2022).")
vineta("Alta polarizacion y volatilidad de mercado en las tres semanas previas a la segunda vuelta.")
vineta("Abstencion y movilizacion diferencial como factor decisivo y dificil de pronosticar.")
vineta("Ruido institucional, denuncias o eventos de orden publico que alteren la narrativa.")
vineta("Factores externos (precio del petroleo, tasas globales, apetito por riesgo emergente).")

pdf.add_page()
titulo("Conclusion")
parrafo("Colombia llega a una segunda vuelta abierta y polarizada entre De la Espriella y Cepeda. "
        "La centro-derecha parte como favorita por aritmetica y por el mercado, pero el precedente de "
        "2022 y el peso del centro y la abstencion mantienen el resultado en disputa. Para EDFO y sus "
        "clientes, el periodo hasta el 21 de junio exige gestion activa del riesgo, coberturas "
        "cambiarias y disciplina para no sobre-reaccionar a un resultado aun no definitivo. EDFO "
        "mantendra el seguimiento en tiempo real de la jornada del balotaje.")

# Aviso legal
pdf.set_y(pdf.get_y() + 3)
pdf.set_fill_color(*SOFT)
pdf.set_draw_color(*GOLD)
ytop = pdf.get_y()
pdf.set_x(15)
pdf.set_font("Helvetica", "B", 8.5)
pdf.set_text_color(*NAVY)
pdf.multi_cell(180, 4.6, "AVISO LEGAL", border=0)
pdf.set_font("Helvetica", "", 8)
pdf.set_text_color(*GRAY)
pdf.set_x(15)
pdf.multi_cell(180, 4.2,
               "Este documento tiene caracter exclusivamente informativo y educativo. No constituye "
               "asesoria de inversion personalizada, oferta ni recomendacion de compra o venta de "
               "instrumento financiero alguno. Las cifras electorales son preliminares (boletin de la "
               "Registraduria Nacional, sin valor juridico hasta el escrutinio). Las probabilidades de "
               "mercado provienen de plataformas de prediccion y no son garantia de resultados. EDFO no "
               "se responsabiliza por decisiones tomadas con base en este material. Rentabilidades "
               "pasadas no garantizan rentabilidades futuras.")
pdf.set_draw_color(*GOLD)
pdf.set_line_width(0.4)
pdf.line(15, ytop - 2, 15, pdf.get_y())

out = "/Users/federicoeckardtv./Library/CloudStorage/OneDrive-Personal/CLAUDE COWORK/elecciones-colombia-2026/EDFO_Informe_Elecciones_Colombia_2026.pdf"
pdf.output(out)
print("PDF generado:", out)
