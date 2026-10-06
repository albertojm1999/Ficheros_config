import time
from netmiko import ConnectHandler, file_transfer

# Datos de la conexión SSH
dispositivo_ssh = {
    'device_type': 'cisco_ios',
    'host': '192.168.122.143',
    'username': 'backup',
    'password': '1234'
}

# Rutas del archivo local y cómo se llamará en la flash del router
archivo_origen = '/home/alberto/Escritorio/backups/Ficheros_config/r1-confg.txt'
archivo_destino = 'backup_gns3.cfg' 

def activar_ssh_inicial():
    print("\n--- CONFIGURACIÓN INICIAL POR CONSOLA ---")
    puerto = input("Introduce el puerto Telnet de la consola en GNS3 (ej. 5001): ")
    interfaz = input("Introduce la interfaz conectada a virbr0 (ej. f0/0 o g0/0): ")
    
    cisco_telnet = {
        'device_type': 'cisco_ios_telnet',
        'host': '127.0.0.1',
        'port': int(puerto),
    }
    
    try:
        print(f"Conectando al puerto de consola local {puerto}...")
        conexion_consola = ConnectHandler(**cisco_telnet)
        
        conexion_consola.write_channel("\r\n")
        time.sleep(1)
        
        comandos_bootstrap = [
            f"interface {interfaz}",
            f"ip address {dispositivo_ssh['host']} 255.255.255.0",
            "no shutdown",
            "exit",
            "ip domain-name gns3.local",
            "crypto key generate rsa modulus 2048",
            f"username {dispositivo_ssh['username']} privilege 15 secret {dispositivo_ssh['password']}",
            "aaa new-model",
            "aaa authentication login default local",
            "aaa authorization exec default local",
            "line vty 0 4",
            "login local",
            "transport input ssh",
            "exit",
            "ip scp server enable"
        ]
        
        print("Inyectando configuración base...")
        conexion_consola.send_config_set(comandos_bootstrap)
        conexion_consola.save_config()
        conexion_consola.disconnect()
        
        print("¡Consola configurada! Esperando 10 segundos...")
        time.sleep(10)
        print("-----------------------------------------\n")
        
    except Exception as e:
        print(f"Error al configurar por consola: {e}")
        exit()

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

print("=== HERRAMIENTA DE RESTAURACIÓN CISCO ===")
es_nuevo = input("¿Es un router nuevo (sin IP/SSH configurado)? (S/N): ").strip().upper()

if es_nuevo == 'S':
    activar_ssh_inicial()

try:
    print(f"Conectando vía SSH a Cisco en {dispositivo_ssh['host']}...")
    conexion = ConnectHandler(**dispositivo_ssh)
    
    print("Transfiriendo archivo de backup mediante file_transfer de Netmiko...")
    # file_transfer gestiona automáticamente el almacenamiento en la flash de Cisco
    resultado_transferencia = file_transfer(
        conexion,
        source_file=archivo_origen,
        dest_file=archivo_destino,
        file_system="flash:",
        direction="put",
        overwrite_file=True
    )
    
    print(f"Resultado de la transferencia: {resultado_transferencia}")
    
    if resultado_transferencia.get('file_transferred') or resultado_transferencia.get('file_exists'):
        print("Aplicando el archivo de respaldo al startup-config...")
        conexion.send_command(
            f"copy flash:{archivo_destino} startup-config", 
            expect_string=r"Destination filename", 
            delay_factor=2
        )
        conexion.send_command("\n") 
        
        print("Reiniciando el router para cargar la topología limpia...")
        conexion.send_command("reload", expect_string=r"Proceed with reload", delay_factor=2)
        conexion.send_command("\n")
        
        print("¡Restauración completada con éxito!")
    else:
        print("La transferencia falló o el archivo no pudo ser verificado.")
        
    conexion.disconnect()

except Exception as e:
    print(f"Error en la conexión SSH o transferencia: {e}")