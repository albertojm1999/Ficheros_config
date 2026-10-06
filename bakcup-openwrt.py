import re
import shlex
import socket
import sys
import time
from netmiko import ConnectHandler, SCPConn

# OpenWrt se maneja en Netmiko como un sistema Linux genérico
dispositivo = {
    'device_type': 'linux',
    'host': '192.168.122.53',
    'username': 'backup',
    'password': '1234'
}

archivo_origen = '/home/alberto/backups/openwrt_network'
# En OpenWrt reemplazamos el archivo del sistema directamente
archivo_destino = '/etc/config/network' 

MASCARA = '255.255.255.0'


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

    if not puerto.isdigit():
        print("El puerto debe ser numérico.")
        sys.exit(1)

    usuario = dispositivo['username']
    password = shlex.quote(dispositivo['password'])
    prompt = r"#\s*$"

    comandos_bootstrap = [
        # Red: IP estática en la interfaz LAN (br-lan)
        "uci set network.lan.proto='static'",
        f"uci set network.lan.ipaddr='{dispositivo['host']}'",
        f"uci set network.lan.netmask='{MASCARA}'",
        "uci commit network",
        "/etc/init.d/network restart",
    ]

    # Usuario de backup con permisos de root (necesario para escribir en /etc/config)
    if usuario != "root":
        comandos_bootstrap += [
            f"grep -q '^{usuario}:' /etc/passwd || echo '{usuario}:x:0:0:{usuario}:/root:/bin/ash' >> /etc/passwd",
            f"grep -q '^{usuario}:' /etc/shadow || echo '{usuario}:*:0:0:99999:7:::' >> /etc/shadow",
        ]
    comandos_bootstrap += [
        f"printf '%s\\n%s\\n' {password} {password} | passwd {usuario}",
        # SSH (dropbear) activo al arrancar
        "/etc/init.d/dropbear enable",
        "/etc/init.d/dropbear restart",
    ]

    consola = None
    try:
        print(f"Conectando al puerto de consola local {puerto}...")
        consola = ConsolaTelnet("127.0.0.1", int(puerto))
        consola.enviar()   # "Please press Enter to activate this console"
        consola.enviar()

        # Normalmente root entra sin contraseña; si ya tiene, se intenta con la del diccionario
        intentos_password = 1
        while True:
            idx, _ = consola.esperar([r"login:\s*$", r"password:\s*$", prompt], timeout=90)
            if idx == 0:
                consola.enviar("root")
            elif idx == 1:
                if intentos_password == 0:
                    raise RuntimeError("Login en consola rechazado: root ya tiene contraseña distinta.")
                intentos_password -= 1
                consola.enviar(dispositivo['password'])
            else:
                break

        print("Inyectando configuración base...")
        for cmd in comandos_bootstrap:
            consola.enviar(cmd)
            _, salida = consola.esperar([prompt], timeout=60)
            if re.search(r"not found|can't|cannot|failed|error", salida, re.I):
                print(f"Aviso del router en '{cmd.split('|')[-1].strip()[:40]}':\n{salida.strip()}")

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
print("=== HERRAMIENTA DE RESTAURACIÓN OPENWRT ===")
es_nuevo = input("¿Es un router nuevo (sin IP/SSH configurado)? (S/N): ").strip().upper()

if es_nuevo == 'S':
    activar_ssh_inicial()

try:
    print(f"Conectando a OpenWrt en {dispositivo['host']}...")
    conexion = ConnectHandler(**dispositivo)
    
    print("Transfiriendo archivo de red vía SCP...")
    scp_client = SCPConn(conexion)
    scp_client.scp_transfer_file(archivo_origen, archivo_destino)
    scp_client.close()
    
    print("Reiniciando el servicio de red para aplicar cambios...")
    salida = conexion.send_command("/etc/init.d/network restart")
    print(salida)
    
    print("¡Configuración de OpenWrt restaurada!")
    conexion.disconnect()

except Exception as e:
    print(f"Error con OpenWrt: {e}")