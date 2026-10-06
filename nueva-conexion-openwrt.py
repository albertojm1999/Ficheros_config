from netmiko import ConnectHandler

dispositivo = {
    'device_type': 'cisco_ios',
    'host': '192.168.122.131',
    'username': 'root',
    'password': '1234'
}
# podría poner antes de decir las interfaces poner que si quiero ver las interfaces, así vemos cuál tenemos vacías y cuáles no, y ver qué dirección tenemos. (idea)
# quizás también poner el protocolo que queremos usar si static or dinamic (idea)
# también poner que sí queremos aplicar antes de nada, imáginate que me he confundido, pues antes de aplicar le doy que no quiero aplicar pues salgo. (idea)

try:
    ssh = ConnectHandler(**dispositivo)
    print("Conexión exitosa.")
except ValueError as e:
    print(f"Algo salió mal: {e}")

number = int(input("Cuántas interfaces quieres configurar: "))

for i in range(1, number + 1):
    interface = input(f"Dime la interfaz {i}: ")
    address = input(f"Dime la dirección de la interfaz {i}: ")
    netmask = input(f"Dime la máscara de red de la dirección{i}: ")
    commands = [
        f"uci set network.lan.device={interface}",
        "uci set network.lan.proto='static'",
        f"uci set network.lan.ipaddr={address}",
        f"uci set network.lan.netmask={netmask}",
        "uci commit network",
        "/etc/init.d/network restart"
    ]
    try:
        ssh.send_config_set(commands)
        print("Cambios realizado correctamente.")
    except ValueError as e:
        print(f"Algo no salió como debía: {e}")
result = ssh.send_command('ip a')
print("Guardando la configuración en el equipo...")
print(f"¡Configuración guardada correctamente! \n{result}")






