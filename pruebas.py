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

counter = 0
interfaces = int(input("Cuántas interfaces quieres configurar: "))
while counter <= interfaces:
    interface = input("Valor de la interfaz: ")
    address = input("Valor de la dirección : ")
    netmask = input("Máscara de red la dirección: ")
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


uci set network.lan.proto='static'
uci set network.lan.ipaddr='192.168.1.10'
uci set network.lan.netmask='255.255.255.0'
uci commit network
/etc/init.d/network restart