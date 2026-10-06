from netmiko import ConnectHandler, SCPConn

dispositivo = {
    'device_type': 'mikrotik_routeros',
    'host': '192.168.122.219',
    'username': 'backup',
    'password': '1234'
}

archivo_origen = '/home/alberto/Escritorio/backups/Ficheros_config/myconfig.rsc'
archivo_destino = 'restore.rsc'

try:
    print(f"Conectando a MikroTik en {dispositivo['host']}...")
    conexion = ConnectHandler(**dispositivo)
    
    print("Transfiriendo archivo .rsc vía SCP...")
    scp_client = SCPConn(conexion)
    scp_client.scp_transfer_file(archivo_origen, archivo_destino)
    scp_client.close()
    
    print("Importando la configuración...")
    # El comando import lee el archivo línea por línea y lo ejecuta
    salida = conexion.send_command(f"/import file-name={archivo_destino}")
    print(salida)
    
    print("¡Configuración de MikroTik restaurada!")
    conexion.disconnect()

except Exception as e:
    print(f"Error con MikroTik: {e}")