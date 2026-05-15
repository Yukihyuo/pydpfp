# pydpfp

Wrapper de Python para lectores de huella DigitalPersona, construido sobre el SDK U.are.U para facilitar captura, extracción y comparación biométrica desde aplicaciones Python en Windows.

## Características

- Inicialización dinámica de los wrappers y carga de bibliotecas nativas en tiempo de ejecución.
- Soporte para DLLs personalizadas mediante parámetro opcional dll_path al crear instancias.
- Manejo nativo de estructuras y tipos C/C++ con ctypes para interoperabilidad directa con el SDK.

## Instalación

### Instalación local

```bash
pip install .
```

### Instalación directa desde GitHub

```bash
pip install git+https://github.com/USUARIO/REPOSITORIO.git
```

## Uso Rápido (Quickstart)

```python
from pydpfp import FingerPrintReader

reader = FingerPrintReader()  # Usa la DLL por defecto del paquete
if reader.init():
    devices = reader.list_devices()
    if devices and reader.open(devices[0]["name"]):
        ok, result, image = reader.capture(timeout_ms=5000)
        if ok:
            print("Huella capturada:", result["quality"], len(image))
        reader.close()
    reader.exit()
```

## Estructura del Proyecto

```text
FingerPrint/
├── pydpfp/
│   ├── __init__.py
│   ├── dpfpdd_wrapper.py
│   ├── dpfj_wrapper.py
│   ├── lector1.dll
│   └── lector2.dll
├── native_reference/
│   └── *.h
├── examples/
│   └── ...
├── setup.py
└── README.md
```

## Notas de Compatibilidad

- Requiere tener instalados en el sistema los drivers oficiales de DigitalPersona.
- Verifica que la arquitectura de Python, DLLs y drivers coincida (32 bits con 32 bits, 64 bits con 64 bits).
- El soporte está orientado a Microsoft Windows, en línea con el SDK U.are.U.
