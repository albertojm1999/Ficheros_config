from netmiko import ConnectHandler

new = input("Es un router nuevo: ")

dispositivo_ssh = {
    'device_type': 'cisco_ios',
    'host': '192.168.122.2',
    'username': 'admin',
    'password': '1234'
}

if new.upper() == "S":

    print("\n -------- CONFIGURACIÓN INICIAL SSH --------")
    port = input("Introduce el puerto de Telnet: ")
    interface = input("Introduce la interfaz: ")

    cisco_telnet = {
        'device_type': 'cisco_ios_telnet',
        'host': '127.0.0.1',
        'port': int(port)
    }
    try:
        con_tel = ConnectHandler(**cisco_telnet)
        print("Conexión exitosa. Empezamos la activación SSH")
        command_ssh = [
            f"interface {interface}",
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
        print("Inyectando comandos...")
        con_tel.send_config_set(command_ssh)
        con_tel.save_config()
        con_tel.disconnect()
        print("-------------- Configuración Terminada. --------------")
    except ValueError as e:
        print(f"Error, no ha sido posible la conexión: {e}")
else:
    print("------------ Configuramos por SSH ------------")

try:
    ssh = ConnectHandler(**dispositivo_ssh)
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


