import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import subprocess
import time
from datetime import datetime

from precios import INSTALACIONES, CATEGORIAS, NOMBRE_TICKET

CONFIG_FILE = "entradas_config.json"
VENTAS_DIR = "ventas"


# ── Rutas ─────────────────────────────────────────────────────────────────────

def get_base_dir():
    """Carpeta donde se guardan config y ventas. Sin requerir admin."""
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    # Comprobar si podemos escribir en la carpeta del exe
    test = os.path.join(exe_dir, ".wtest")
    try:
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return exe_dir
    except (PermissionError, OSError):
        # Fallback a AppData — siempre escribible sin admin
        d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                         "GesportVentaEntradas")
        os.makedirs(d, exist_ok=True)
        return d


def get_config_path():
    return os.path.join(get_base_dir(), CONFIG_FILE)


def load_config():
    try:
        with open(get_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"impresora": ""}


def save_config(data):
    with open(get_config_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def es_festivo_hoy():
    return datetime.now().weekday() >= 5  # sábado=5, domingo=6


# ── App principal ─────────────────────────────────────────────────────────────

class VentaEntradas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesport — Venta de Entradas")
        self.root.resizable(True, True)
        self.root.configure(bg="#f5f5f5")

        self._setup_styles()
        self.config = load_config()
        self.instalacion_actual = None
        self._clock_job = None

        self.container = ttk.Frame(root, padding=0)
        self.container.pack(fill="both", expand=True)

        self._show_selector()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame",       background="#f5f5f5")
        s.configure("TLabel",       font=("Segoe UI", 10),            background="#f5f5f5")
        s.configure("Bold.TLabel",  font=("Segoe UI", 10, "bold"),    background="#f5f5f5")
        s.configure("Muted.TLabel", font=("Segoe UI", 9),             background="#f5f5f5", foreground="#7f8c8d")
        s.configure("Title.TLabel", font=("Segoe UI", 13, "bold"),    background="#f5f5f5", foreground="#2c3e50")
        s.configure("Total.TLabel", font=("Segoe UI", 13, "bold"),    background="#f5f5f5")
        s.configure("Sep.TFrame",   background="#bdc3c7")
        s.configure("TButton",      font=("Segoe UI", 10))
        s.configure("Big.TButton",  font=("Segoe UI", 11),  padding=10)
        s.configure("Star.TButton", font=("Segoe UI", 11, "bold"), padding=(16, 8))
        s.map("Star.TButton",
              background=[("active", "#1a6b3a"), ("!active", "#27ae60")],
              foreground=[("active", "white"),   ("!active", "white")])

    def _clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()
        if self._clock_job:
            self.root.after_cancel(self._clock_job)
            self._clock_job = None

    # ── Pantalla 1: selector de instalación ───────────────────────────────────

    def _show_selector(self):
        self._clear_container()
        self.root.geometry("")

        f = ttk.Frame(self.container, padding=28)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Gesport",
                  font=("Segoe UI", 20, "bold"), background="#f5f5f5",
                  foreground="#2c3e50").pack(pady=(0, 2))
        ttk.Label(f, text="Venta de Entradas",
                  style="Muted.TLabel",
                  font=("Segoe UI", 12)).pack(pady=(0, 18))

        ttk.Frame(f, style="Sep.TFrame", height=1).pack(fill="x", pady=(0, 18))
        ttk.Label(f, text="Selecciona la instalación:", style="Bold.TLabel").pack(pady=(0, 10))

        grid = ttk.Frame(f)
        grid.pack()

        names = list(INSTALACIONES.keys())
        for i, nombre in enumerate(names):
            row, col = divmod(i, 2)
            ttk.Button(grid, text=nombre, style="Big.TButton", width=32,
                       command=lambda n=nombre: self._select_instalacion(n)
                       ).grid(row=row, column=col, padx=6, pady=5, sticky="ew")

    def _select_instalacion(self, nombre):
        self.instalacion_actual = nombre
        self._show_venta()

    # ── Pantalla 2: venta ─────────────────────────────────────────────────────

    def _show_venta(self):
        self._clear_container()

        # Inicializar todas las variables ANTES de construir widgets
        # (evita AttributeError en _recalcular() cuando se llama durante la construcción)
        self.tipo_dia       = tk.StringVar(value="festivo" if es_festivo_hoy() else "laborable")
        self.clock_var      = tk.StringVar()
        self.total_var      = tk.StringVar(value="0.00 €")
        self.importe_var    = tk.StringVar()
        self.cambio_var     = tk.StringVar()
        self.cantidad_vars   = {}
        self.precio_labels   = {}
        self.subtotal_labels = {}
        self._entries        = []

        f = ttk.Frame(self.container, padding=16)
        f.pack(fill="x")

        # --- Cabecera ---
        hdr = ttk.Frame(f)
        hdr.pack(fill="x", pady=(0, 6))

        ttk.Button(hdr, text="← Cambiar",
                   command=self._show_selector).pack(side="left")
        ttk.Label(hdr, text=self.instalacion_actual,
                  style="Title.TLabel").pack(side="left", padx=10)

        ttk.Label(hdr, textvariable=self.clock_var,
                  style="Muted.TLabel").pack(side="right")
        self._tick_clock()

        ttk.Frame(f, style="Sep.TFrame", height=1).pack(fill="x", pady=(4, 8))

        # --- Tipo de día ---
        day_f = ttk.Frame(f)
        day_f.pack(fill="x", pady=(0, 6))

        ttk.Label(day_f, text="Tipo de día:", style="Bold.TLabel").pack(side="left", padx=(0, 10))

        # tk.Button (no ttk) para poder colorear el activo
        self.btn_lab = tk.Button(day_f, text="LABORABLE",
                                  font=("Segoe UI", 10, "bold"), bd=1, padx=12, pady=4,
                                  command=lambda: self._set_tipo_dia("laborable"))
        self.btn_lab.pack(side="left", padx=(0, 4))

        self.btn_fes = tk.Button(day_f, text="FESTIVO / FIN DE SEMANA",
                                  font=("Segoe UI", 10, "bold"), bd=1, padx=12, pady=4,
                                  command=lambda: self._set_tipo_dia("festivo"))
        self.btn_fes.pack(side="left")

        self._pintar_dia_buttons()

        ttk.Frame(f, style="Sep.TFrame", height=1).pack(fill="x", pady=(8, 4))

        # --- Tabla de categorías ---
        tbl = ttk.Frame(f)
        tbl.pack(fill="x", pady=4)

        for col, (text, width, anchor) in enumerate([
            ("Categoría",  15, "w"),
            ("",            2, "center"),   # −
            ("Cant.",       5, "center"),
            ("",            2, "center"),   # +
            ("Precio",      9, "e"),
            ("Subtotal",   10, "e"),
        ]):
            ttk.Label(tbl, text=text, style="Bold.TLabel",
                      width=width, anchor=anchor).grid(row=0, column=col, padx=4, pady=2)

        ttk.Frame(tbl, style="Sep.TFrame", height=1).grid(
            row=1, column=0, columnspan=6, sticky="ew", pady=3)

        for i, (key, label) in enumerate(CATEGORIAS):
            r = i + 2
            ttk.Label(tbl, text=label, width=15).grid(row=r, column=0, padx=4, pady=3, sticky="w")

            ttk.Button(tbl, text="−", width=2,
                       command=lambda k=key: self._dec(k)).grid(row=r, column=1, padx=2)

            var = tk.StringVar(value="0")
            var.trace_add("write", lambda *_, k=key: self._recalcular())
            entry = ttk.Entry(tbl, textvariable=var, width=6,
                              font=("Segoe UI", 10), justify="center")
            entry.grid(row=r, column=2, padx=4)
            # Seleccionar todo al ganar foco (cómodo para sobreescribir con teclado)
            entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, "end"))
            self._entries.append(entry)

            ttk.Button(tbl, text="+", width=2,
                       command=lambda k=key: self._inc(k)).grid(row=r, column=3, padx=2)

            pl = ttk.Label(tbl, text="0.00 €", width=9, anchor="e")
            pl.grid(row=r, column=4, padx=4, sticky="e")

            sl = ttk.Label(tbl, text="0.00 €", width=10, anchor="e")
            sl.grid(row=r, column=5, padx=4, sticky="e")

            self.cantidad_vars[key]   = var
            self.precio_labels[key]   = pl
            self.subtotal_labels[key] = sl

        self._actualizar_precios()

        ttk.Frame(f, style="Sep.TFrame", height=2).pack(fill="x", pady=(10, 4))

        # --- Total ---
        tot_f = ttk.Frame(f)
        tot_f.pack(fill="x")
        ttk.Label(tot_f, text="TOTAL:", style="Total.TLabel").pack(side="left")
        ttk.Label(tot_f, textvariable=self.total_var, style="Total.TLabel").pack(side="right")

        ttk.Frame(f, style="Sep.TFrame", height=1).pack(fill="x", pady=6)

        # --- Importe recibido / cambio ---
        pago_f = ttk.Frame(f)
        pago_f.pack(fill="x", pady=(0, 4))

        ttk.Label(pago_f, text="Importe recibido:", style="Bold.TLabel").pack(side="left")
        self.importe_var.trace_add("write", lambda *_: self._actualizar_cambio())
        importe_e = ttk.Entry(pago_f, textvariable=self.importe_var, width=10,
                               font=("Segoe UI", 10), justify="right")
        importe_e.pack(side="left", padx=6)
        ttk.Label(pago_f, text="€").pack(side="left")

        self.cambio_lbl = tk.Label(pago_f, textvariable=self.cambio_var,
                                    font=("Segoe UI", 10, "bold"),
                                    bg="#f5f5f5", fg="#2c3e50")
        self.cambio_lbl.pack(side="left", padx=(18, 0))

        ttk.Frame(f, style="Sep.TFrame", height=1).pack(fill="x", pady=(0, 8))

        # --- Botones ---
        btn_f = ttk.Frame(f)
        btn_f.pack(fill="x")
        ttk.Button(btn_f, text="★  REGISTRAR VENTA", style="Star.TButton",
                   command=self._registrar_venta).pack(side="left", padx=(0, 12))
        ttk.Button(btn_f, text="📋  Ver registros",
                   command=self._show_registros).pack(side="left", padx=(0, 8))
        ttk.Button(btn_f, text="⚙  Configuración",
                   command=self._show_config).pack(side="left")

        # Dejar que tkinter calcule el tamaño correcto una vez colocados todos los widgets
        self.root.after(10, lambda: self.root.geometry(""))

    # ── Reloj ─────────────────────────────────────────────────────────────────

    def _tick_clock(self):
        now = datetime.now()
        dia = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][now.weekday()]
        self.clock_var.set(f"{dia} {now.strftime('%d/%m/%Y  %H:%M:%S')}")
        self._clock_job = self.root.after(1000, self._tick_clock)

    # ── Tipo de día ───────────────────────────────────────────────────────────

    def _set_tipo_dia(self, tipo):
        self.tipo_dia.set(tipo)
        self._pintar_dia_buttons()
        self._actualizar_precios()

    def _pintar_dia_buttons(self):
        if self.tipo_dia.get() == "laborable":
            self.btn_lab.configure(bg="#2c3e50", fg="white",   relief="sunken")
            self.btn_fes.configure(bg="#dfe6e9", fg="#2c3e50", relief="raised")
        else:
            self.btn_lab.configure(bg="#dfe6e9", fg="#2c3e50", relief="raised")
            self.btn_fes.configure(bg="#2c3e50", fg="white",   relief="sunken")

    # ── Precios y cálculos ────────────────────────────────────────────────────

    def _precio(self, key):
        return INSTALACIONES[self.instalacion_actual][key][self.tipo_dia.get()]

    def _actualizar_precios(self):
        for key, _ in CATEGORIAS:
            self.precio_labels[key].configure(text=f"{self._precio(key):.2f} €")
        self._recalcular()

    def _cantidad(self, key):
        try:
            return max(0, int(self.cantidad_vars[key].get()))
        except ValueError:
            return 0

    def _inc(self, key):
        self.cantidad_vars[key].set(str(self._cantidad(key) + 1))

    def _dec(self, key):
        v = self._cantidad(key)
        if v > 0:
            self.cantidad_vars[key].set(str(v - 1))

    def _recalcular(self):
        total = 0.0
        for key, _ in CATEGORIAS:
            sub = self._precio(key) * self._cantidad(key)
            total += sub
            self.subtotal_labels[key].configure(text=f"{sub:.2f} €")
        self.total_var.set(f"{total:.2f} €")
        self._actualizar_cambio()
        return total

    def _total_float(self):
        try:
            return float(self.total_var.get().replace(" €", "").replace(",", "."))
        except ValueError:
            return 0.0

    def _actualizar_cambio(self):
        try:
            recibido = float(self.importe_var.get().replace(",", "."))
            cambio = recibido - self._total_float()
            signo = "+" if cambio >= 0 else ""
            color = "#27ae60" if cambio >= 0 else "#c0392b"
            self.cambio_var.set(f"   Cambio: {signo}{cambio:.2f} €")
            self.cambio_lbl.configure(fg=color)
        except ValueError:
            self.cambio_var.set("")

    # ── Ticket ────────────────────────────────────────────────────────────────

    def _build_ticket(self):
        now = datetime.now()
        nombre = self.instalacion_actual
        tipo = "LABORABLE" if self.tipo_dia.get() == "laborable" else "FESTIVO/FIN SEMANA"
        nombre_corto = NOMBRE_TICKET.get(nombre, nombre)
        lines = [
            "====================",
            "  VENTA DE ENTRADA",
            "====================",
            f"Fecha: {now.strftime('%d/%m/%Y')}",
            f"Hora:  {now.strftime('%H:%M:%S')}",
            f"Inst:  {nombre_corto}",
            f"Dia:   {tipo}",
            "--------------------",
        ]

        total = 0.0
        for key, label in CATEGORIAS:
            cant = self._cantidad(key)
            if cant == 0:
                continue
            precio = self._precio(key)
            sub = precio * cant
            total += sub
            cat = label.split("(")[0].strip()
            lines.append(f" {cat:<11} x{cant:<3} {sub:>7.2f}€")

        lines.append("--------------------")
        lines.append(f" TOTAL:        {total:>7.2f}€")

        try:
            recibido = float(self.importe_var.get().replace(",", "."))
            cambio = recibido - total
            lines.append(f" Recibido:     {recibido:>7.2f}€")
            lines.append(f" Cambio:       {cambio:>7.2f}€")
        except ValueError:
            pass

        lines.append("====================")
        return "\n".join(lines), now

    def _get_ventas_dir(self):
        d = os.path.join(get_base_dir(), VENTAS_DIR)
        os.makedirs(d, exist_ok=True)
        return d

    def _guardar_venta(self):
        texto, now = self._build_ticket()
        ts = now.strftime("%Y-%m-%d_%H-%M-%S")
        safe = (self.instalacion_actual
                .replace(" ", "_")
                .encode("ascii", "ignore").decode())[:20]
        filepath = os.path.join(self._get_ventas_dir(), f"venta_{ts}_{safe}.txt")
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(texto)
            fh.flush()
            os.fsync(fh.fileno())   # garantiza escritura en disco antes de imprimir
        return filepath, now

    def _hay_entradas(self):
        return any(self._cantidad(k) > 0 for k, _ in CATEGORIAS)

    def _resetear(self):
        for key, _ in CATEGORIAS:
            self.cantidad_vars[key].set("0")
        self.importe_var.set("")

    # ── Registrar venta ───────────────────────────────────────────────────────

    def _registrar_venta(self):
        if not self._hay_entradas():
            messagebox.showwarning("Sin entradas", "No hay entradas seleccionadas.")
            return
        printer = self.config.get("impresora", "")
        self._elegir_impresion(printer)

    def _elegir_impresion(self, printer):
        """Diálogo de confirmación: guarda y resetea SOLO si el usuario elige imprimir."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Registrar venta")
        dlg.resizable(False, False)
        dlg.configure(bg="#f5f5f5")
        dlg.grab_set()

        ttk.Label(dlg, text="¿Cómo imprimir el ticket?",
                  style="Bold.TLabel").pack(padx=24, pady=(18, 8))

        if not printer:
            ttk.Label(dlg, text="⚠ Sin impresora configurada — se registrará sin imprimir",
                      style="Muted.TLabel").pack(padx=24, pady=(0, 8))

        ttk.Frame(dlg, style="Sep.TFrame", height=1).pack(fill="x", padx=16, pady=(0, 10))

        btn_f = ttk.Frame(dlg)
        btn_f.pack(padx=24, pady=(0, 6))

        def confirmar(modo):
            # Capturar datos ANTES de resetear
            items = [
                (label.split("(")[0].strip(), self._cantidad(key), self._precio(key))
                for key, label in CATEGORIAS
                if self._cantidad(key) > 0
            ]
            filepath, now = self._guardar_venta()
            self._resetear()
            dlg.destroy()
            if printer:
                try:
                    if modo == "individual":
                        self._print_individual_tickets(items, now, printer)
                    else:
                        self._print_to_printer(filepath, printer)
                except Exception as e:
                    messagebox.showerror("Error al imprimir", str(e))

        ttk.Button(btn_f, text="🖨  Ticket conjunto\n(un ticket para todo el grupo)",
                   command=lambda: confirmar("conjunto"), width=34).pack(pady=4)
        ttk.Button(btn_f, text="🖨  Tickets individuales\n(un ticket por persona)",
                   command=lambda: confirmar("individual"), width=34).pack(pady=4)

        ttk.Frame(dlg, style="Sep.TFrame", height=1).pack(fill="x", padx=16, pady=(8, 0))
        ttk.Button(dlg, text="← Volver (no registrar)",
                   command=dlg.destroy).pack(pady=(6, 14))

    def _dialogo_modo_impresion(self, filepath, printer, parent=None):
        """Diálogo conjunto/individual para un archivo ya guardado (ej: reimprimir)."""
        win = parent or self.root
        dlg = tk.Toplevel(win)
        dlg.title("Imprimir")
        dlg.resizable(False, False)
        dlg.configure(bg="#f5f5f5")
        dlg.grab_set()

        ttk.Label(dlg, text="¿Cómo imprimir el ticket?",
                  style="Bold.TLabel").pack(padx=24, pady=(18, 8))
        ttk.Frame(dlg, style="Sep.TFrame", height=1).pack(fill="x", padx=16, pady=(0, 10))

        btn_f = ttk.Frame(dlg)
        btn_f.pack(padx=24, pady=(0, 6))

        def imprimir(modo):
            dlg.destroy()
            try:
                if modo == "individual":
                    for ticket in self._build_tickets_individuales(filepath):
                        self._print_ticket(ticket, printer, suffix=self._NOMBRE_SUFFIX)
                else:
                    self._print_to_printer(filepath, printer)
            except Exception as e:
                messagebox.showerror("Error al imprimir", str(e), parent=win)

        ttk.Button(btn_f, text="🖨  Ticket conjunto\n(un ticket para todo el grupo)",
                   command=lambda: imprimir("conjunto"), width=34).pack(pady=4)
        ttk.Button(btn_f, text="🖨  Tickets individuales\n(un ticket por persona)",
                   command=lambda: imprimir("individual"), width=34).pack(pady=4)
        ttk.Frame(dlg, style="Sep.TFrame", height=1).pack(fill="x", padx=16, pady=(8, 0))
        ttk.Button(dlg, text="← Volver",
                   command=dlg.destroy).pack(pady=(6, 14))

    def _build_tickets_individuales(self, filepath_conjunto):
        """Parsea el ticket conjunto guardado y devuelve lista de strings (uno por persona)."""
        with open(filepath_conjunto, "r", encoding="utf-8") as fh:
            lines = fh.readlines()

        fecha = hora = inst = dia = ""
        for l in lines:
            s = l.strip()
            if s.startswith("Fecha:"): fecha = s.split(":", 1)[1].strip()
            elif s.startswith("Hora:"): hora  = s.split(":", 1)[1].strip()
            elif s.startswith("Inst:"): inst  = s.split(":", 1)[1].strip()
            elif s.startswith("Dia:"):  dia   = s.split(":", 1)[1].strip()

        import re
        pat = re.compile(r"^\s+(.+?)\s+x(\d+)\s+([\d.]+)\s*€\s*$")
        sep = "====================\n"
        mid = "--------------------\n"
        bloques = []
        for l in lines:
            m = pat.match(l)
            if m:
                cat   = m.group(1).strip()
                cant  = int(m.group(2))
                precio = round(float(m.group(3)) / cant, 2) if cant else 0.0
                for _ in range(cant):
                    t  = sep + "  VENTA DE ENTRADA\n" + sep
                    t += f"Fecha: {fecha}\n"
                    t += f"Hora:  {hora}\n"
                    t += f"Inst:  {inst}\n"
                    t += f"Dia:   {dia}\n"
                    t += mid
                    t += f" {cat}\n"
                    t += f"       {precio:.2f} €\n"
                    t += sep
                    bloques.append(t)
        return bloques

    def _print_individual_tickets(self, items, now, printer):
        """Un trabajo de impresión RAW por persona — activa el corte automático entre tickets."""
        nombre_corto = NOMBRE_TICKET.get(self.instalacion_actual, self.instalacion_actual)
        tipo = "LABORABLE" if self.tipo_dia.get() == "laborable" else "FESTIVO/FIN SEMANA"
        sep = "====================\n"
        mid = "--------------------\n"
        for cat, cant, precio in items:
            for _ in range(cant):
                t  = sep + "  VENTA DE ENTRADA\n" + sep
                t += f"Fecha: {now.strftime('%d/%m/%Y')}\n"
                t += f"Hora:  {now.strftime('%H:%M:%S')}\n"
                t += f"Inst:  {nombre_corto}\n"
                t += f"Dia:   {tipo}\n"
                t += mid
                t += f" {cat}\n"
                t += f"       {precio:.2f} €\n"
                t += sep
                self._print_ticket(t, printer, suffix=self._NOMBRE_SUFFIX)

    # ── ESC/POS — Epson TM-T20 ────────────────────────────────────────────────

    _ESC_INIT     = b'\x1b\x40'             # ESC @ — inicializar impresora
    _ESC_CP858    = b'\x1b\x74\x13'        # ESC t 19 — CP858 (español + € incluido)
    _ESC_CENTER   = b'\x1b\x61\x01'        # ESC a 1 — centrado
    _ESC_BOLD_ON  = b'\x1b\x45\x01'        # ESC E 1 — negrita on
    _ESC_BOLD_OFF = b'\x1b\x45\x00'        # ESC E 0 — negrita off
    _CUT_FULL     = b'\n\n\n\n\n\n\n\n\x1d\x56\x00'  # avance + GS V 0 — corte completo

    _NOMBRE_SUFFIX = (                     # bloque "escribe tu nombre" + zona para escribir
        b'\n'
        + b'\x1b\x45\x01'               # negrita on
        + b'====================\n'
        + 'ESCRIBE TU NOMBRE COMPLETO DEBAJO\n'.encode("cp858")
        + b'====================\n'
        + b'\x1b\x45\x00'               # negrita off
        + b'==                ==\n'
        + b'\n'
        + b'\n'
        + b'\n'
        + b'==                ==\n'
    )

    def _raw_print(self, data: bytes, printer: str):
        """Envía bytes RAW directamente a la impresora (sin GDI ni márgenes)."""
        import win32print
        h = win32print.OpenPrinter(printer)
        try:
            win32print.StartDocPrinter(h, 1, ("Ticket", None, "RAW"))
            try:
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, data)
                win32print.EndPagePrinter(h)
            finally:
                win32print.EndDocPrinter(h)
        finally:
            win32print.ClosePrinter(h)

    def _print_ticket(self, text: str, printer: str, suffix: bytes = b''):
        """Envía un ticket con cabecera ESC/POS y comando de corte al final."""
        payload = (
            self._ESC_INIT
            + self._ESC_CP858
            + self._ESC_CENTER
            + text.encode("cp858", errors="replace")
            + suffix
            + self._CUT_FULL
        )
        self._raw_print(payload, printer)

    def _print_to_printer(self, filepath, printer):
        """Imprime el archivo de ticket conjunto como un único trabajo RAW."""
        for _ in range(20):
            if os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
                break
            time.sleep(0.1)
        else:
            messagebox.showerror("Error al imprimir",
                                 f"No se encontró el archivo de ticket:\n{filepath}")
            return
        with open(filepath, "r", encoding="utf-8") as fh:
            text = fh.read()
        self._print_ticket(text, printer)

    # ── Configuración ─────────────────────────────────────────────────────────

    def _get_printers(self):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Printer | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
        except Exception:
            return []

    def _show_config(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configuración — Impresora")
        dlg.resizable(False, False)
        dlg.configure(bg="#f5f5f5")
        dlg.grab_set()

        ttk.Label(dlg, text="Impresora para tickets:", style="Bold.TLabel").pack(
            padx=16, pady=(14, 6), anchor="w")
        ttk.Label(dlg, text="(Se guardará en la app — no afecta a la impresora del sistema)",
                  style="Muted.TLabel").pack(padx=16, anchor="w")

        frm = ttk.Frame(dlg)
        frm.pack(padx=16, pady=8, fill="both", expand=True)

        lb = tk.Listbox(frm, font=("Segoe UI", 10), width=48, height=9)
        sb = ttk.Scrollbar(frm, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        printers = self._get_printers()
        current  = self.config.get("impresora", "")

        if not printers:
            lb.insert("end", "(No se encontraron impresoras)")
        else:
            for i, name in enumerate(printers):
                prefix = "✔  " if name == current else "    "
                lb.insert("end", f"{prefix}{name}")
                if name == current:
                    lb.selection_set(i)

        status = tk.StringVar(value=f"Actual: {current}" if current else "Actual: (ninguna)")
        ttk.Label(dlg, textvariable=status, style="Muted.TLabel").pack(padx=16, anchor="w")

        def on_save():
            sel = lb.curselection()
            if not sel or not printers:
                return
            selected = printers[sel[0]]
            self.config["impresora"] = selected
            save_config(self.config)
            dlg.destroy()
            messagebox.showinfo("Configuración", f"Impresora guardada:\n{selected}")

        bf = ttk.Frame(dlg)
        bf.pack(pady=(6, 14))
        ttk.Button(bf, text="Guardar",   command=on_save).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Cancelar",  command=dlg.destroy).pack(side="left")


    # ── Visor de registros ────────────────────────────────────────────────────

    def _scan_ventas(self):
        """Devuelve lista de (label, filepath) ordenada más reciente primero."""
        ventas_dir = self._get_ventas_dir()
        results = []
        for fname in sorted(os.listdir(ventas_dir), reverse=True):
            if not fname.startswith("venta_") or not fname.endswith(".txt"):
                continue
            fpath = os.path.join(ventas_dir, fname)
            fecha = hora = instalacion = total = ""
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    for line in fh:
                        l = line.strip()
                        if l.startswith("Fecha:"):
                            fecha = l.split(":", 1)[1].strip()
                        elif l.startswith("Hora:"):
                            hora = l.split(":", 1)[1].strip()
                        elif l.startswith("Inst:"):
                            instalacion = l.split(":", 1)[1].strip()
                        elif l.strip().startswith("TOTAL:"):
                            total = l.split("TOTAL:", 1)[1].strip()
            except Exception:
                continue

            label = f"{fecha}  {hora}"
            if instalacion:
                label += f"  —  {instalacion}"
            if total:
                label += f"  —  {total}"
            results.append((label, fpath))
        return results

    def _show_registros(self):
        all_ventas = self._scan_ventas()

        dlg = tk.Toplevel(self.root)
        dlg.title("Registros de venta")
        dlg.resizable(True, True)
        dlg.configure(bg="#f5f5f5")
        dlg.grab_set()

        # --- Filtro ---
        filter_f = ttk.Frame(dlg)
        filter_f.pack(padx=16, pady=(12, 6), fill="x")
        ttk.Label(filter_f, text="Buscar:", style="Bold.TLabel").pack(side="left")
        filter_var = tk.StringVar()
        ttk.Entry(filter_f, textvariable=filter_var, width=40,
                  font=("Segoe UI", 10)).pack(side="left", padx=8)
        ttk.Label(filter_f, text="(fecha, hora, instalación…)",
                  style="Muted.TLabel").pack(side="left")

        # --- Lista ---
        list_f = ttk.Frame(dlg)
        list_f.pack(padx=16, fill="both", expand=True)

        lb = tk.Listbox(list_f, font=("Segoe UI", 10), width=72, height=12,
                        activestyle="dotbox")
        sb = ttk.Scrollbar(list_f, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # --- Vista previa del ticket ---
        ttk.Frame(dlg, style="Sep.TFrame", height=1).pack(fill="x", padx=16, pady=(8, 4))

        prev_f = ttk.Frame(dlg)
        prev_f.pack(padx=16, fill="both", expand=True)
        txt = tk.Text(prev_f, font=("Courier New", 9), width=44, height=18,
                      state="disabled", bg="#fafafa", relief="flat", bd=1)
        txt_sb = ttk.Scrollbar(prev_f, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=txt_sb.set)
        txt.pack(side="left", fill="both", expand=True)
        txt_sb.pack(side="right", fill="y")

        filtered = []

        def refresh(*_):
            nonlocal filtered
            lb.delete(0, "end")
            filtered.clear()
            query = filter_var.get().strip().lower()
            for label, fpath in all_ventas:
                if query:
                    if not all(w in label.lower() for w in query.split()):
                        continue
                filtered.append((label, fpath))
                lb.insert("end", label)
            if filtered:
                lb.selection_set(0)
                show_preview()

        def show_preview(*_):
            sel = lb.curselection()
            if not sel or sel[0] >= len(filtered):
                return
            _, fpath = filtered[sel[0]]
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception:
                content = "(No se pudo leer el archivo)"
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.insert("end", content)
            txt.configure(state="disabled")

        def reimprimir():
            sel = lb.curselection()
            if not sel or sel[0] >= len(filtered):
                return
            printer = self.config.get("impresora", "")
            if not printer:
                messagebox.showwarning("Sin impresora",
                                       "No hay impresora configurada.\nVe a ⚙ Configuración.",
                                       parent=dlg)
                return
            _, fpath = filtered[sel[0]]
            self._dialogo_modo_impresion(fpath, printer, parent=dlg)

        filter_var.trace_add("write", refresh)
        lb.bind("<<ListboxSelect>>", show_preview)
        lb.bind("<Double-1>", show_preview)

        # --- Botones ---
        bf = ttk.Frame(dlg)
        bf.pack(pady=(8, 12))
        ttk.Button(bf, text="🖨  Reimprimir seleccionado",
                   command=reimprimir).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Cerrar", command=dlg.destroy).pack(side="left")

        if not all_ventas:
            lb.insert("end", "(No hay registros de venta)")
        else:
            refresh()

        dlg.update_idletasks()
        dlg.geometry(f"{dlg.winfo_reqwidth()}x{dlg.winfo_reqheight()}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    root.configure(bg="#f5f5f5")
    VentaEntradas(root)
    root.mainloop()


if __name__ == "__main__":
    main()
