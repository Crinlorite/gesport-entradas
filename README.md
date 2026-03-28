# Gesport — Venta de Entradas

Aplicación de escritorio para la venta de entradas diarias en instalaciones deportivas gestionadas por Gesport. Desarrollada con Python + Tkinter, distribuida como `.exe` sin necesidad de instalación ni permisos de administrador.

## Funcionalidades

- **Selector de instalación** al arrancar — cada PC puede usarlo para cualquier instalación
- **Tipo de día** (Laborable / Festivo) con detección automática del día de la semana
- **Categorías de edad** con contadores `+` / `−` y campo editable (navegable con Tab)
  - Bebé (<4), Niño (4-13), Joven (14-17), Adulto (18-64), Senior (+65), Especial
- **Venta cruzada**: cualquier combinación de categorías en una sola transacción
- **Total en tiempo real** + cálculo de cambio (importe recibido → cambio automático)
- **★ Registrar venta**: guarda el registro y ofrece opciones de impresión
  - **Ticket conjunto** — un ticket para todo el grupo
  - **Tickets individuales** — un ticket por persona con zona para escribir el nombre, un trabajo de impresión separado por persona (activa el corte automático entre tickets)
- **📋 Ver registros**: visor de ventas con búsqueda libre por fecha, hora e instalación, con vista previa del ticket y opción de reimpresión (también con elección conjunto/individual)
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

> Sarriguren, Egüés, Calahorra y San Adrian tienen los precios pendientes de confirmar con Gesport (todos a 0.00 €). Ver `precios.py`.

## Uso

Descarga `Venta de Entradas.exe` desde [Releases](../../releases) y ejecútalo directamente. No requiere instalación ni permisos de administrador.

Los registros de venta se guardan en la carpeta `ventas/` junto al `.exe` (o en `%APPDATA%\GesportVentaEntradas\ventas\` si el `.exe` está en una ubicación de solo lectura).

## Impresora de tickets

La app imprime en **modo RAW ESC/POS**, sin márgenes GDI. Compatible con impresoras térmicas Epson TM-T20 y similares.

- Impresión directa vía `win32print` — sin Notepad, sin PowerShell
- Encoding **CP858** (variante de CP850 con soporte de `€` y caracteres españoles)
- Comando de corte automático `GS V 0` al final de cada ticket
- Los tickets individuales se envían como **trabajos independientes** para que la cortadora actúe entre cada uno

**Requisito adicional**: `pywin32`

```bash
pip install pywin32
```

## Desarrollo

**Requisitos**: Python 3.12+, tkinter (incluido en Python estándar), pywin32

```bash
# Ejecutar en desarrollo
python venta_entradas.py

# Compilar exe
pyinstaller "Venta de Entradas.spec"
# El exe queda en dist/Venta de Entradas.exe
```

> Al compilar con PyInstaller, asegurarse de que `pywin32` está disponible en el entorno. Si el exe se distribuye sin `pywin32` instalado en el sistema destino, la impresión fallará. Considerar añadir `hiddenimports=['win32print']` al `.spec`.

### Actualizar precios o añadir instalaciones

Editar `precios.py`:
- **Modificar precios**: cambiar los valores `laborable`/`festivo` del dict correspondiente
- **Nueva instalación**: añadir entrada en `INSTALACIONES` y su nombre corto en `NOMBRE_TICKET`
- Recompilar el exe y distribuirlo

## Licencia

MIT
