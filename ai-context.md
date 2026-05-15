# pydpfp AI Context

**System prompt:** `Eres un asistente de Python; usa pydpfp para generar código de captura, enrolamiento y comparación de huellas en Windows.`

## Signatures / API Contract

| Símbolo | Firma | Retorna | Notas |
|---|---|---:|---|
| `from pydpfp import FingerPrintReader` | clase | instancia | alias raíz recomendado; usa `lector1.dll` por defecto vía `__init__.py` |
| `from pydpfp import FingerJetEngine` | clase | instancia | alias raíz recomendado; usa `lector2.dll` por defecto vía `__init__.py` |
| `FingerPrintReader(dll_path=None)` | ctor | objeto | `dll_path=None` => DLL local por defecto; `str` => ruta personalizada |
| `FingerPrintReader.init()` | `() -> bool` | `True/False` | inicializa SDK; imprime error y devuelve `False` si falla |
| `FingerPrintReader.exit()` | `() -> None` | `None` | libera SDK |
| `FingerPrintReader.list_devices()` | `() -> list[dict]` | lista | cada dict: `name, product, vendor, serial` |
| `FingerPrintReader.open(device_name, use_ext=False, priority=2)` | `(str, bool, int) -> bool` | `True/False` | `priority`: `2` cooperativo, `4` exclusivo |
| `FingerPrintReader.get_status()` | `() -> dict \| None` | dict/None | `status, finger_detected, status_text` |
| `FingerPrintReader.start_stream()` | `() -> bool` | `True/False` | activa streaming |
| `FingerPrintReader.stop_stream()` | `() -> bool` | `True/False` | desactiva streaming |
| `FingerPrintReader.calibrate()` | `() -> bool` | `True/False` | calibra lector |
| `FingerPrintReader.capture(timeout_ms=5000, retries=3)` | `(int, int) -> tuple[bool, dict, bytes]` | `(ok, result, image)` | `image` = bytes crudos 8bpp grayscale |
| `FingerPrintReader.close()` | `() -> None` | `None` | cierra lector |
| `FingerJetEngine(dll_path=None)` | ctor | objeto | usa `lector2.dll` por defecto vía `__init__.py` |
| `FingerJetEngine.version()` | `() -> dict` | dict | `library, api` |
| `FingerJetEngine.create_fmd_from_raw(image_data, image_width, image_height, image_dpi=500, finger_pos=0, cbeff_id=0, fmd_type=0x001B0001)` | `(bytes,int,int,int,int,int,int) -> bytes` | FMD | `image_data` debe ser raster 8bpp; recorta padding si sobra |
| `FingerJetEngine.create_fmd_from_fid(fid_data, fid_type=0x001B0401, fmd_type=0x001B0001)` | `(bytes,int,int) -> bytes` | FMD | convierte FID ANSI/ISO a FMD |
| `FingerJetEngine.compare(fmd1, fmd2, fmd_type=0x001B0001, fmd1_type=None, fmd2_type=None, view_idx1=0, view_idx2=0)` | `(bytes,bytes,...) -> int` | score | menor score = mejor match; `0` es óptimo |
| `FingerJetEngine.convert_fmd(fmd_data, src_type, dst_type)` | `(bytes,int,int) -> bytes` | FMD | conversión de formato |
| `FingerJetEngine.enrollment_start(fmd_type=0x001B0001)` | `(int) -> None` | `None` | inicia enrolamiento |
| `FingerJetEngine.enrollment_add(fmd_data, fmd_type=0x001B0001, view_idx=0)` | `(bytes,int,int) -> bool` | `True/False` | `False` = aún faltan muestras (`MORE_DATA`) |
| `FingerJetEngine.enrollment_create_fmd()` | `() -> bytes` | FMD | genera FMD final de enrolamiento |
| `FingerJetEngine.enrollment_finish()` | `() -> None` | `None` | cierra sesión de enrolamiento |

## Ctypes Mapping

| Python | ctypes / SDK | Uso |
|---|---|---|
| `bytes` | `c_ubyte * n` + `from_buffer_copy()` | buffers de imagen/FMD/FID |
| `int` | `c_int` / `c_uint` | códigos, tamaños, DPI, índices, flags |
| `bool` | `c_int` en C, `bool()` en Python | éxito de captura, finger_detected |
| puntero de salida | `byref(c_uint(...))`, `byref(struct)` | tamaños, handles, resultados |
| handle de dispositivo | `c_void_p` | `dpfpdd_open/open_ext` -> `close` |
| strings SDK | `c_char * 128/1024` | `name`, `vendor_name`, `product_name`, `serial_num` |
| estructuras | `ctypes.Structure` | `DPFPDD_*`, `DPFJ_*` |

### Estructuras relevantes

- `DPFPDD_DEV_INFO`: `size, name, descr, id, ver, modality, technology`
- `DPFPDD_DEV_STATUS`: `size, status, finger_detected, data`
- `DPFPDD_CAPTURE_PARAM`: `size, image_fmt, image_proc, image_res`
- `DPFPDD_CAPTURE_RESULT`: `size, success, quality, score, info`
- `DPFPDD_IMAGE_INFO`: `size, width, height, res, bpp`
- `DPFJ_VERSION`: `size, lib_ver, api_ver`
- `DPFJ_CANDIDATE`: `size, fmd_idx, view_idx`

### Restricciones de memoria

- Usa `from_buffer_copy()` para evitar depender de memoria mutable de Python.
- Pasa tamaños exactos: `len(bytes)` para FMD/FID y `width * height` para imagen RAW.
- Para `create_fmd_from_raw()`, si el buffer RAW trae padding extra, el wrapper recorta a `width * height`.
- FMD de salida usa buffer de trabajo de `MAX_FMD_SIZE = 1562`.
- `capture()` devuelve `image_data` como bytes crudos, no como imagen decodificada.

## Minimal Working Example

```python
from pydpfp import FingerPrintReader  # Importa la clase pública del paquete

reader = FingerPrintReader()          # Carga la DLL local por defecto
if reader.init():                     # Inicializa el SDK nativo
    devices = reader.list_devices()   # Enumera lectores conectados
    if devices and reader.open(devices[0]["name"]):  # Abre el primer lector
        ok, result, image = reader.capture(timeout_ms=5000)  # Captura huella
        if ok:                        # Verifica éxito real de captura
            print(result["quality"], len(image))               # Calidad + tamaño
        reader.close()                # Cierra el dispositivo
    reader.exit()                     # Libera recursos del SDK
```
