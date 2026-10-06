from netmiko import ConnectHandler

dispositivo = {
    'device_type': 'mikrotik_routeros',
    'host': '192.168.122.33',
    'username': 'admin',
    'password': '1234'
}

try:
    ssh = ConnectHandler(**dispositivo)
    print("Conexión establecida de manera exitosa.")
except ValueError as e:
    print(f"Error. Algo salió mal: {e}")

numero = int(input("Cuántas interfaces quieres configurar: "))

for i in range (1, numero + 1):
    interface = input(f"Dime la interfaz {i}: ")
    address = input(f"Dime la dirección de la interfaz {i}: ")
    netmask = input(f"Dime la máscara de la dirección {i}: ")
    commands = [
        f'/ip address add address={address}/{netmask} interface={interface}'
    ]
    try:
        ssh.send_config_set(commands)
        print("Configuración realizada exitósamente")
    except ValueError as e:
        print(f"Error. Algo salió mal : {e}")

result = ssh.send_command('ip addres print')
print("Guardando la configuración en el equipo...")
print(f"¡Configuración guardada correctamente! \n{result}")