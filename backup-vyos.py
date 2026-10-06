import re
import socket
import sys
import time
from netmiko import ConnectHandler, SCPConn

# Definimos el router (ejemplo con VyOS)
dispositivo = {
    'device_type': 'vyos', 
    'host': '192.168.122.44',
    'username': 'backup',
    'password': '1234'
}

# Rutas de los archivos
archivo_origen = '/home/alberto/Escritorio/backups/Ficheros_config/config.boot'
archivo_destino = '/config/config.boot'

PREFIJO = 24  # /24 = 255.255.255.0


# ==========================================
# CONFIGURACIÓN INICIAL POR CONSOLA (SSH)
# ==========================================
class ConsolaTelnet:
    """Cliente mínimo para la consola Telnet de GNS3 (sin telnetlib)."""
    ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[=>]|\x1b\][^\x07]*\x07")
    IAC = re.compile(rb"\xff[\xfb-\xfe].|\xff.")

    def __init__(self, host, puerto):
        self.sock = socket.create_connection((host, puerto), timeout=10)
        self.sock.settimeout(1)
        self.buffer = ""

    def _leer(self):
        try:
            datos = self.sock.recv(4096)
        except socket.timeout:
            return ""
        datos = self.IAC.sub(b"", datos)
        return self.ANSI.sub("", datos.decode("utf-8", errors="ignore")).replace("\r", "")

    def enviar(self, texto=""):
        self.sock.sendall((texto + "\r\n").encode())

    def esperar(self, patrones, timeout=30):
        limite = time.time() + timeout
        while time.time() < limite:
            self.buffer += self._leer()
            for i, patron in enumerate(patrones):
                if re.search(patron, self.buffer, re.I):
                    salida, self.buffer = self.buffer, ""
                    return i, salida
        raise TimeoutError(f"Timeout esperando la consola. Último contenido:\n{self.buffer[-300:]}")

    def cerrar(self):
        try:
            self.sock.close()
        except Exception:
            pass


def activar_ssh_inicial():
    print("\n--- CONFIGURACIÓN INICIAL POR CONSOLA ---")
    puerto = input("Introduce el puerto Telnet de la consola en GNS3 (ej. 5001): ").strip()
    interfaz = input("Introduce la interfaz conectada a virbr0 (ej. eth0): ").strip() or "eth0"

    if not puerto.isdigit():
        print("El puerto debe ser numérico.")
        sys.exit(1)

    prompt = r"[$#]\s*$"
    consola = None
    try:
        print(f"Conectando al puerto de consola local {puerto}...")
        consola = ConsolaTelnet("127.0.0.1", int(puerto))
        consola.enviar()
        consola.enviar()

        # Login en la consola (VyOS nuevo: vyos/vyos)
        intentos_password = 1
        while True:
            idx, _ = consola.esperar([r"login:\s*$", r"password:\s*$", prompt], timeout=90)
            if idx == 0:
                consola.enviar(dispositivo['username'])
            elif idx == 1:
                if intentos_password == 0:
                    raise RuntimeError("Login en consola rechazado: revisa usuario y contraseña.")
                intentos_password -= 1
                consola.enviar(dispositivo['password'])
            else:
                break

        comandos_bootstrap = [
            "configure",
            f"set interfaces ethernet {interfaz} address {dispositivo['host']}/{PREFIJO}",
            "set service ssh port 22",
            "commit",
            "save",
            "exit",   # sale del modo configuración
            "exit",   # cierra la sesión de consola
        ]

        print("Inyectando configuración base...")
        for cmd in comandos_bootstrap:
            consola.enviar(cmd)
            try:
                _, salida = consola.esperar([prompt, r"login:\s*$"], timeout=60)
            except TimeoutError:
                continue
            if re.search(r"commit failed|invalid|error", salida, re.I):
                print(f"Aviso del router en '{cmd}':\n{salida.strip()}")

        print("¡Consola configurada! Esperando 10 segundos...")
        time.sleep(10)
        print("-----------------------------------------\n")

    except Exception as e:
        print(f"Error al configurar por consola: {e}")
        sys.exit(1)
    finally:
        if consola:
            consola.cerrar()


# ==========================================
# FLUJO PRINCIPAL
# ==========================================
print("=== HERRAMIENTA DE RESTAURACIÓN VYOS ===")
es_nuevo = input("¿Es un router nuevo (sin IP/SSH configurado)? (S/N): ").strip().upper()

if es_nuevo == 'S':
    activar_ssh_inicial()

try:
    print(f"1. Estableciendo conexión SSH con {dispositivo['host']}...")
    conexion_ssh = ConnectHandler(**dispositivo)
    
    print("2. Abriendo túnel SCP...")
    # Le pasamos la conexión SSH existente al manejador SCP
    scp_client = SCPConn(conexion_ssh)
    
    print(f"3. Transfiriendo archivo desde {archivo_origen}...")
    # Transferencia del archivo (origen local, destino remoto)
    scp_client.scp_transfer_file(archivo_origen, archivo_destino)
    
    print("¡Archivo transferido con éxito!")
    scp_client.close()
    
    # 4. (Opcional) Aplicar la configuración si es necesario
    print("4. Aplicando cambios en el router...")
    conexion_ssh.config_mode()
    conexion_ssh.send_command("load /config/config.boot")
    conexion_ssh.send_command("commit")
    conexion_ssh.exit_config_mode()
    print("Router actualizado.")

    conexion_ssh.disconnect()

except Exception as e:
    print(f"Error en el proceso: {e}")