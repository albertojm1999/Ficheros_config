# 2026-10-04 14:15:26 by RouterOS 7.23.7
# system id = DWSfmFJK5XA
#
/interface bridge
add name=loopback0
/interface ethernet
set [ find default-name=ether1 ] disable-running-check=no
set [ find default-name=ether2 ] disable-running-check=no
set [ find default-name=ether3 ] disable-running-check=no
set [ find default-name=ether4 ] disable-running-check=no
set [ find default-name=ether5 ] disable-running-check=no
/routing ospf instance
add name=default router-id=172.16.0.2
/routing ospf area
add instance=default name=backbone
/ip address
add address=172.16.0.2 interface=loopback0 network=172.16.0.2
add address=172.16.20.1/24 interface=ether3 network=172.16.20.0
add address=172.16.1.2/30 interface=ether2 network=172.16.1.0
add address=172.16.1.9/30 interface=ether1 network=172.16.1.8
/ip dhcp-client
add interface=ether1 name=client1
add interface=ether4 name=client2
/ip dns
set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1
/ip firewall filter
add action=accept chain=input comment="Permitir Ping" protocol=icmp
add action=accept chain=input dst-port=22 protocol=tcp
/ip firewall nat
add action=masquerade chain=srcnat out-interface=ether4
add action=masquerade chain=srcnat out-interface=ether4
/ip route
add gateway=10.0.0.1
add gateway=192.168.1.1
add gateway=192.168.1.1
add gateway=192.168.1.1
add gateway=192.168.1.1
/routing ospf interface-template
add area=backbone networks=172.16.0.0/16
