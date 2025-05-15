from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch, Host
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def nationalWanNetwork():
    "Crea una red WAN nacional con Casa Matriz y dos sucursales."

    net = Mininet(topo=None, build=False, controller=None) # Sin controlador por defecto, IPs manuales

    info('*** Agregando Routers (Nodos Linux con reenvío IP)\n')
    # Router Casa Matriz
    r0 = net.addHost('r0', cls=Node, ip=None) # IP principal no es crucial, las interfaces sí
    r0.cmd('sysctl -w net.ipv4.ip_forward=1')

    # Router Sucursal 1
    r1 = net.addHost('r1', cls=Node, ip=None)
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')

    # Router Sucursal 2
    r2 = net.addHost('r2', cls=Node, ip=None)
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')

    info('*** Agregando Hosts de Sucursales\n')
    # Host en Sucursal 1
    # La IP se asigna con máscara y la ruta por defecto a través del router de su LAN
    h1 = net.addHost('h1', cls=Host, ip='10.0.1.254/24', defaultRoute='via 10.0.1.1')

    # Host en Sucursal 2
    h2 = net.addHost('h2', cls=Host, ip='10.0.2.254/24', defaultRoute='via 10.0.2.1')

    info('*** Agregando Switches\n')
    # Switches para enlaces WAN (simulando el medio físico)
    s1_wan = net.addSwitch('s1_wan', cls=OVSKernelSwitch, failMode='standalone')
    s2_wan = net.addSwitch('s2_wan', cls=OVSKernelSwitch, failMode='standalone')

    # Switches para LANs de sucursales
    s1_lan = net.addSwitch('s1_lan', cls=OVSKernelSwitch, failMode='standalone')
    s2_lan = net.addSwitch('s2_lan', cls=OVSKernelSwitch, failMode='standalone')

    info('*** Creando Enlaces WAN y asignando IPs\n')
    # Enlace WAN Sucursal 1: r0 <-> s1_wan <-> r1
    net.addLink(r0, s1_wan, intfName1='r0-eth0', params1={'ip': '192.168.100.6/29'})
    net.addLink(r1, s1_wan, intfName1='r1-wan0', params1={'ip': '192.168.100.1/29'})

    # Enlace WAN Sucursal 2: r0 <-> s2_wan <-> r2
    net.addLink(r0, s2_wan, intfName1='r0-eth1', params1={'ip': '192.168.100.14/29'})
    net.addLink(r2, s2_wan, intfName1='r2-wan0', params1={'ip': '192.168.100.9/29'})

    info('*** Creando Enlaces LAN y asignando IPs\n')
    # LAN Sucursal 1: r1 <-> s1_lan <-> h1
    net.addLink(r1, s1_lan, intfName1='r1-lan0', params1={'ip': '10.0.1.1/24'})
    net.addLink(h1, s1_lan, intfName1='h1-eth0') # IP ya definida en addHost

    # LAN Sucursal 2: r2 <-> s2_lan <-> h2
    net.addLink(r2, s2_lan, intfName1='r2-lan0', params1={'ip': '10.0.2.1/24'})
    net.addLink(h2, s2_lan, intfName1='h2-eth0') # IP ya definida en addHost

    info('*** Iniciando Red\n')
    net.build()

    info('*** Iniciando Switches\n')
    net.get('s1_wan').start([])
    net.get('s2_wan').start([])
    net.get('s1_lan').start([])
    net.get('s2_lan').start([])

    info('*** Configurando Rutas Estáticas en Routers\n')
    # Rutas en Router Casa Matriz (r0)
    # Hacia LAN de Sucursal 1 a través del IP WAN de r1
    r0.cmd('ip route add 10.0.1.0/24 via 192.168.100.1 dev r0-eth0')
    # Hacia LAN de Sucursal 2 a través del IP WAN de r2
    r0.cmd('ip route add 10.0.2.0/24 via 192.168.100.9 dev r0-eth1')

    # Rutas en Router Sucursal 1 (r1)
    # Ruta por defecto hacia Casa Matriz (r0) para alcanzar otras sucursales o "internet"
    r1.cmd('ip route add default via 192.168.100.6 dev r1-wan0')

    # Rutas en Router Sucursal 2 (r2)
    # Ruta por defecto hacia Casa Matriz (r0)
    r2.cmd('ip route add default via 192.168.100.14 dev r2-wan0')

    # Las rutas por defecto de h1 y h2 ya se configuraron al crear los hosts.

    info('*** ¡Red Lista! Iniciando CLI de Mininet...\n')
    CLI(net)

    info('*** Deteniendo Red\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    nationalWanNetwork()