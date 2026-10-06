from netmiko import ConnectHandler

dispositivo = {
    'device_type': 'cisco_ios',
    'host': '192.168.122.32',
    'username': 'admin',
    'password': '1234'
}

try:
    ssh = ConnectHandler(**dispositivo)
    print("Conexión establecida.")
except ValueError as e:
    print(f"Error al establecer conexión: {e}")

numbers = int(input("Cuántas interfaces quieres configurar: "))

for i in range(1, numbers + 1):
    interface = input(f"Valor de la interfaz {i}: ")
    address = input(f"Valor de la dirección {i}: ")
    netmask = input(f"Máscara de red la dirección {i}: ")
    commands = [
    f'int {interface}',
    f'ip address {address} {netmask}',
    'no sh'
    ]
    try:
        result = ssh.send_config_set(commands)
        print("Enviando configuración.")
        print(f"Interfaz {interface} configurada con la dirección {address}.")
    except ValueError as e:
        print(f"Error al escribir configuración: {e}")
print("Guardando la configuración en el equipo...")
ssh.save_config()
print("¡Configuración guardada correctamente!")


