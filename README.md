# Gesport — Venta de Entradas

Aplicación de escritorio para la venta de entradas diarias en instalaciones deportivas gestionadas por Gesport. Desarrollada con Python + Tkinter, distribuida como `.exe` sin necesidad de instalación ni permisos de administrador.

## Funcionalidades

- **Selector de instalación** al arrancar — cada PC puede usarlo para cualquier instalación
- **Tipo de día** (Laborable / Festivo) con detección automática del día de la semana
- **Categorías de edad** con contadores `+` / `−` y campo editable (navegable con Tab)
  - Bebé (<4), Niño (4-13), Joven (14-17), Adulto (18-64), Senior (+65), Especial
- **Venta cruzada**: cualquier combinación de categorías en una sola transacción
- **Total en tiempo real** + cálculo de cambio (importe recibido → cambio automático)
- **Registro de trabajador** persistente entre ventas
- **★ Registrar venta**: guarda el registro y ofrece opciones de impresión
  - **Ticket conjunto** — un ticket para todo el grupo
  - **Tickets individuales** — un ticket por persona (precio individual, para identificación nominal)
- **📋 Ver registros**: visor de ventas con búsqueda libre por trabajador, fecha, hora e instalación, con vista previa del ticket y opción de reimpresión (también con elección conjunto/individual)
- **⚙ Configuración**: selección de impresora guardada en la app — **no modifica la impresora predeterminada del sistema**

## Instalaciones soportadas

| Instalación | Ticket |
|---|---|
| Ciudad Deportiva Artica | CD Artica |
| Inst. Deportivas Berrioplano | ID Berrioplano |
| Ciudad Deportiva Sarriguren | CD Sarriguren |
| Polideportivo Valle de Egüés | PM Egüés |
| CPM Calahorra | CPM Calahorra |
| San Adrian | San Adrian |

## Uso

Descarga `Venta de Entradas.exe` desde [Releases](../../releases) y ejecútalo directamente. No requiere instalación ni permisos de administrador.

Los registros de venta se guardan en la carpeta `ventas/` junto al `.exe` (o en `%APPDATA%\GesportVentaEntradas\ventas\` si el `.exe` está en una ubicación de solo lectura).

## Desarrollo

**Requisitos**: Python 3.12+, tkinter (incluido en Python estándar)

```bash
# Ejecutar en desarrollo
python venta_entradas.py

# Compilar exe
pyinstaller "Venta de Entradas.spec"
# El exe queda en dist/Venta de Entradas.exe
```

### Actualizar precios o añadir instalaciones

Editar `precios.py`:
- **Modificar precios**: cambiar los valores `laborable`/`festivo` del dict correspondiente
- **Nueva instalación**: añadir entrada en `INSTALACIONES` y su nombre corto en `NOMBRE_TICKET`
- Recompilar el exe y distribuirlo

## Licencia

MIT
