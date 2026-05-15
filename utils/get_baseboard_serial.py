import subprocess

def get_baseboard_serial():
    try:
        # Ejecuta el comando de Windows Management Instrumentation
        cmd = "wmic baseboard get serialnumber"
        output = subprocess.check_output(cmd, shell=True).decode().split('\n')
        # Limpiamos el resultado para obtener solo el string del serial
        serial = output[1].strip()
        return serial
    except Exception as e:
        print(f"Error obteniendo HWID: {e}")
        return "UUID-GENERICO-DEBUG"