# precios.py — Precios de entradas diarias por instalación y categoría de edad.
#
# Para añadir una nueva instalación: añadir una clave nueva en INSTALACIONES.
# Para modificar precios: editar los valores del dict correspondiente.
# Solo entradas diarias — sin bonos ni abonos anuales.

# Nombre corto que aparece en el ticket impreso (máx ~20 chars)
NOMBRE_TICKET = {
    "Ciudad Deportiva Artica":      "CD Artica",
    "Inst. Deportivas Berrioplano": "ID Berrioplano",
    "Ciudad Deportiva Sarriguren":  "CD Sarriguren",
    "Polideportivo Valle de Egüés": "PM Egüés",
    "CPM Calahorra":                "CPM Calahorra",
    "San Adrian":                   "San Adrian",
}

# Categorías en el orden que aparecen en pantalla
CATEGORIAS = [
    ("bebe",     "Bebé (<4)"),
    ("nino",     "Niño (4-13)"),
    ("joven",    "Joven (14-17)"),
    ("adulto",   "Adulto (18-64)"),
    ("senior",   "Senior (+65)"),
    ("especial", "Especial"),
]

# ── Ciudad Deportiva Artica / Inst. Deportivas Berrioplano ────────────────────
_ARTICA = {
    "bebe":     {"laborable": 0.00,  "festivo": 0.00},
    "nino":     {"laborable": 6.20,  "festivo": 8.25},
    "joven":    {"laborable": 10.30, "festivo": 12.35},
    "adulto":   {"laborable": 12.35, "festivo": 14.40},
    "senior":   {"laborable": 6.20,  "festivo": 8.25},
    "especial": {"laborable": 5.15,  "festivo": 7.20},   # numerosa/monoparental/discap.≥65% — bebé siempre 0 (usar fila Bebé)
}

# ── Precios por instalación ───────────────────────────────────────────────────
INSTALACIONES = {
    "Ciudad Deportiva Artica":      _ARTICA,
    "Inst. Deportivas Berrioplano": _ARTICA,  # mismos precios que Artica

    # ── CD Sarriguren ─────────────────────────────────────────────────────────
    "Ciudad Deportiva Sarriguren": {
        "bebe":     {"laborable": 0.00, "festivo": 0.00},  # TODO — confirmar con Gesport
        "nino":     {"laborable": 0.00, "festivo": 0.00},  # TODO
        "joven":    {"laborable": 0.00, "festivo": 0.00},  # TODO
        "adulto":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "senior":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "especial": {"laborable": 0.00, "festivo": 0.00},  # TODO
    },

    # ── PM Egüés ──────────────────────────────────────────────────────────────
    "Polideportivo Valle de Egüés": {
        "bebe":     {"laborable": 0.00, "festivo": 0.00},  # TODO — confirmar con Gesport
        "nino":     {"laborable": 0.00, "festivo": 0.00},  # TODO
        "joven":    {"laborable": 0.00, "festivo": 0.00},  # TODO
        "adulto":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "senior":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "especial": {"laborable": 0.00, "festivo": 0.00},  # TODO
    },

    "CPM Calahorra": {
        "bebe":     {"laborable": 0.00, "festivo": 0.00},  # TODO
        "nino":     {"laborable": 0.00, "festivo": 0.00},  # TODO
        "joven":    {"laborable": 0.00, "festivo": 0.00},  # TODO
        "adulto":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "senior":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "especial": {"laborable": 0.00, "festivo": 0.00},  # TODO
    },

    "San Adrian": {
        "bebe":     {"laborable": 0.00, "festivo": 0.00},  # TODO
        "nino":     {"laborable": 0.00, "festivo": 0.00},  # TODO
        "joven":    {"laborable": 0.00, "festivo": 0.00},  # TODO
        "adulto":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "senior":   {"laborable": 0.00, "festivo": 0.00},  # TODO
        "especial": {"laborable": 0.00, "festivo": 0.00},  # TODO
    },
}
