"""
Studium Cyber Security Dashboard

Dieses Skript erstellt ein Dashboard zur Visualisierung des Studienfortschritts.
Es berechnet verdiente und benötigte ECTS, stellt Kurse in einer Netzwerkgrafik dar und
liefert diverse relevante Kennzahlen, um einen Überblick über Fortschritt und Notendurchschnitte
zu gewährleisten.

Mai 2026
"""

# Debugging und System-Informationen
import os
print("Aktuelles Verzeichnis:", os.getcwd())
print("Dateien im Verzeichnis:", os.listdir())

# Bibliotheken importieren
import tkinter as tk
from tkinter import ttk
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

# Hauptfenster für das Dashboard erstellen und anpassen
dashboard = tk.Tk()
dashboard.title("Dashboard Studium - Cyber Security")

width = dashboard.winfo_screenwidth()
height = dashboard.winfo_screenheight()
dashboard.state("zoomed")

# Datenimport und -bereinigung
try:
    # Laden der Kursdaten aus der lokalen CSV-Datei
    kurse = pd.read_csv("kurse_cyber_security.csv", delimiter=";", encoding="utf8")

    # Datenbereinigung: Umwandeln von europäischen Dezimalzahlen in Floats
    for col in ["ects", "note"]:
        if col in kurse.columns:
            kurse[col] = kurse[col].astype(str).str.replace(",", ".")
            kurse[col] = pd.to_numeric(kurse[col], errors="coerce").fillna(0.0)

    # Absicherung für die Spalten-Datentypen
    if kurse["ects"].dtype == "object":
        kurse["ects"] = kurse["ects"].astype(str).str.strip().str.replace(",", ".")
        kurse["ects"] = pd.to_numeric(kurse["ects"], errors="coerce").fillna(0)

    if kurse["note"].dtype == "object":
        kurse["note"] = kurse["note"].astype(str).str.strip().str.replace(",", ".")
        kurse["note"] = pd.to_numeric(kurse["note"], errors="coerce").fillna(0)

except FileNotFoundError:
    # Fallback-Daten, falls die CSV-Datei nicht am angegebenen Pfad existiert
    kurse = pd.DataFrame({
        "kurs": ["Demo Einführung", "Demo Programmieren", "Demo Netzwerke", "Demo Recht"],
        "status": ["bestanden", "bestanden", "belegt", "belegt"],
        "ects": [5.0, 6.0, 5.0, 5.0],
        "note": [1.3, 1.7, 0.0, 0.0]
    })


# Kennzahlen berechnen

# Zeitliche Berechnungen
jetzt = date.today()
heute_str = jetzt.strftime("%d.%m.%Y")
studienbeginn = date(2025, 3, 1)
studienbeginn_str = studienbeginn.strftime("%d.%m.%Y")
studienende = date(2028, 2, 28)
studienende_str = studienende.strftime("%d.%m.%Y")

gesamtdauer_tage = (studienende - studienbeginn).days
tage_seit_start = (jetzt - studienbeginn).days

if tage_seit_start < 0:
    ects_soll_heute = 0.0
elif tage_seit_start > gesamtdauer_tage:
    ects_soll_heute = 180.0
else:
    fortschritt_zeit_faktor = tage_seit_start / gesamtdauer_tage
    ects_soll_heute = 180 * fortschritt_zeit_faktor

# Semester berechnen (auf Basis von 182 Tagen/Halbjahr)
tage_vergangen = (jetzt - studienbeginn).days
semester = (tage_vergangen // 182) + 1
if tage_vergangen < 0:
    semester = "Noch nicht gestartet"

# Status-Typen definieren, die als erfolgreich gelten
erfolgreich = ["bestanden", "anerkannt"]

# ECTS berechnen
verdiente_ects = kurse[kurse["status"].isin(erfolgreich)]["ects"].sum()
gesamt_ects_ziel = 180
offene_ects = gesamt_ects_ziel - verdiente_ects

# Notendurchschnitt berechnen (nur Kurse mit Note > 0)
benotete_kurse = kurse[(kurse["status"].isin(erfolgreich)) & (kurse["note"] > 0)]
if not benotete_kurse.empty:
    notendurchschnitt = benotete_kurse["note"].mean()
else:
    notendurchschnitt = 0.0

# Fortschritt berechnen
fortschritt_prozent = (verdiente_ects / gesamt_ects_ziel) * 100

differenz_zum_soll = float(verdiente_ects) - float(ects_soll_heute)

# Status-Indikator
status_symbol = "✅" if differenz_zum_soll >= 0 else "⚠️"

# Netzwerkgrafik
# Standard-Kategorien hinzufügen, falls in .csv nicht vorhanden
if "kategorie" not in kurse.columns:
    kurse["kategorie"] = ["IT", "Organisatorisch", "Cyber Security", "IT"]

def create_mindmap(df):
    """ Erstellt eine Netzwerkgrafik der Kurse """
    G = nx.Graph()
    root = "Cyber Security"

    # Zentralen Knoten definieren
    G.add_node(root, color="#2790D2", size=3000, s_color="#2c3e50")

    # Farbschema für die unterschiedlichen Status
    status_farben_map = {
        "bestanden": "#2ecc71",
        "anerkannt": "#2ecc71",
        "belegt": "#f1c40f",
        "offen": "#bdc3c7"
    }

    # Kurse hinzufügen
    for _, row in df.iterrows():
        aktueller_status = row["status"].lower()
        node_color = status_farben_map.get(aktueller_status, "#bdc3c7")

        G.add_node(row["kurs"],
                   color=node_color,
                   category=row["kategorie"])

    # Beziehungen definieren
    for _, row in df.iterrows():
        # Jedes Modul mit dem Zentrum verbinden
        G.add_edge(root, row["kurs"], weight=0.1)

        # Module der gleichen Kategorie untereinander stärker gewichten (Clustering)
        selbe_kat = df[df["kategorie"] == row["kategorie"]]["kurs"].tolist()
        for nachbar in selbe_kat:
            if nachbar != row["kurs"]:
                G.add_edge(row["kurs"], nachbar, weight=5.0)

    # Matplotlib Figur für die Grafik erstellen
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="none")
    pos = nx.spring_layout(G, k=1.5, weight="weight", iterations=100, seed=42)

    # Verbindungen Zeichnen
    nx.draw_networkx_edges(G, pos, alpha=0.1, edge_color="grey", ax=ax)

    # Knoten mit individueller Größe und Farbe zeichnen
    for node in G.nodes:
        n_size = 3000 if node == root else 1200
        n_color = G.nodes[node].get("color", "#bdc3c7")

        nx.draw_networkx_nodes(
            G, pos,
            nodelist=[node],
            node_color=n_color,
            node_size=n_size,
            linewidths=0,
            edgecolors="none",
            ax=ax
        )

    # Beschriftungen hinzufügen
    nx.draw_networkx_labels(G, pos, font_size=7, ax=ax)

    ax.set_axis_off()
    plt.tight_layout()
    return fig


def make_canvas(figure, master):
    """ Integriert eine Matplotlib Figur in ein Tkinter Widget. """
    c = FigureCanvasTkAgg(figure, master=master)
    w = c.get_tk_widget()
    w.config(bg="#f0f0f0", highlightthickness=0)
    return w


# Netzwerkgrafik generieren und Widget erstellen
fig_map = create_mindmap(kurse)
canvas_map = make_canvas(fig_map, dashboard)


# Ringdiagramme erstellen

# Diagramm 1: IST-Stand
if differenz_zum_soll >= 0:
    hauptfarbe_ist = "#2ecc71"  # Grün bei planmäßigem oder besserem Fortschritt
else:
    hauptfarbe_ist = "#e74c3c"  # Rot bei Verzug

chart_daten = [verdiente_ects, max(0, offene_ects)]
chart_farben = [hauptfarbe_ist, "#ffffff"]
fig, ax = plt.subplots(figsize=(3, 3), dpi=100, facecolor="none")
ax.pie(chart_daten, colors=chart_farben, startangle=90, counterclock=False,
       wedgeprops={'edgecolor': hauptfarbe_ist, 'linewidth': 1} if offene_ects > 0 else {})

# Loch in die Mitte zeichnen
centre_circle = plt.Circle((0, 0), 0.70, fc="#f0f0f0")
fig.gca().add_artist(centre_circle)
ax.set_title("Aktueller Stand", fontdict={"fontsize": 10, "fontweight": "bold"})
ax.axis('equal')
plt.tight_layout()

canvas = FigureCanvasTkAgg(fig, master=dashboard)
canvas_widget = canvas.get_tk_widget()
canvas_widget.config(bg="#f0f0f0", highlightthickness=0)

# Diagramm 2: SOLL-Zeitplan
soll_offen = max(0, gesamt_ects_ziel - ects_soll_heute)
chart_daten_soll = [ects_soll_heute, soll_offen]
chart_farben_soll = ["#3498db", "#ffffff"]

fig_soll, ax_soll = plt.subplots(figsize=(3, 3), dpi=100, facecolor="none")
ax_soll.pie(chart_daten_soll, colors=chart_farben_soll, startangle=90, counterclock=False,
            wedgeprops={'edgecolor': '#3498db', 'linewidth': 1})

# Loch in die Mitte zeichnen
centre_circle_soll = plt.Circle((0, 0), 0.70, fc="#f0f0f0")
fig_soll.gca().add_artist(centre_circle_soll)
ax_soll.set_title("Soll-Zeitplan", fontdict={"fontsize": 10, "fontweight": "bold"})
ax_soll.axis('equal')
plt.tight_layout()

canvas_soll = FigureCanvasTkAgg(fig_soll, master=dashboard)
canvas_widget_soll = canvas_soll.get_tk_widget()
canvas_widget_soll.config(bg="#f0f0f0", highlightthickness=0)


# Kennzahlen darstellen
fortschritt_titel = ttk.Label(dashboard, text="Fortschritt", font=("Arial", 12, "bold"))
fortschritt_text = (
    f"Aktuelles Semester: {semester}\n"
    f"Studiumsbeginn: {studienbeginn_str}\n"
    f"Stand: {heute_str}\n"
    f"Geplantes Ende: {studienende_str}\n"
    f"\n"
    f"Verdiente ECTS: {verdiente_ects} / {gesamt_ects_ziel}\n"
    f"Soll ECTS: {ects_soll_heute:.1f}\n"
    f"{status_symbol} ({differenz_zum_soll:+.1f} ECTS)\n"
    f"Fortschritt: {fortschritt_prozent:.1f} %"
)
fortschritt_inhalte = ttk.Label(dashboard, text=fortschritt_text, justify="center", font=("Arial", 10))

notendurchschnitt_titel = ttk.Label(dashboard, text="Notenschnitt", font=("Arial", 12, "bold"))
notendurchschnitt_label = ttk.Label(dashboard, text=f"{notendurchschnitt:.2f}", justify="center",
                                    font=("Arial", 36, "bold"), foreground="#2980b9")


# Grid definieren

# Spalten- und Zeilengewichtung
dashboard.columnconfigure(0, weight=3, uniform="a")
dashboard.columnconfigure((1, 2), weight=1, uniform="a")
dashboard.rowconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="a")
dashboard.rowconfigure(6, minsize=20)

# Im Raster platzieren
canvas_map.grid(row=0, column=0, rowspan=4, sticky="nwes", padx=10, pady=10)

fortschritt_titel.grid(row=0, column=1, sticky="s", pady=(10, 0))
fortschritt_inhalte.grid(row=1, rowspan=2, column=1, sticky="n")

notendurchschnitt_titel.grid(row=1, column=2, sticky="n")
notendurchschnitt_label.grid(row=1, column=2)

canvas_widget.grid(row=2, column=1, rowspan=2, sticky="nwes", padx=20, pady=20)
canvas_widget_soll.grid(row=2, column=2, rowspan=2, sticky="nwes", padx=20, pady=20)

# Mainloop starten
dashboard.mainloop()