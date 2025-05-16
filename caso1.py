from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()

def dynamicNationalWanNetwork():
    num_sucursales = int(input("Ingrese la cantidad de sucursales a conectar (mínimo 1): "))
    print(f"*** Creando red para {num_sucursales} sucursal(es) ***")

    net = Mininet(link=TCLink, switch=OVSKernelSwitch, controller=None)

    routers = []
    switches_wan = []
    switches_lan = []
    hosts = []

    # Router principal
    r0 = net.addHost('r0', cls=LinuxRouter, ip=None)
    print("*** Agregando Router Casa Matriz (r0)")
    routers.append(r0)

    for i in range(1, num_sucursales + 1):
        ri = net.addHost(f'r{i}', cls=LinuxRouter, ip=None)
        hi = net.addHost(f'h{i}', ip=f'10.0.{i}.254/24', defaultRoute=f'via 10.0.{i}.1')
        swi_wan = net.addSwitch(f's{i}_wan')
        swi_lan = net.addSwitch(f's{i}_lan')

        print(f"    Agregado Router Sucursal: r{i}")
        print(f"    Agregado Host Sucursal: h{i} (IP: 10.0.{i}.254/24)")
        print(f"    Agregado Switch WAN: s{i}_wan")
        print(f"    Agregado Switch LAN: s{i}_lan")

        routers.append(ri)
        hosts.append(hi)
        switches_wan.append(swi_wan)
        switches_lan.append(swi_lan)

    print("*** Creando Enlaces y asignando IPs")

    for i in range(1, num_sucursales + 1):
        wan_net_base = 192 + i  # puede ser 192.168.100.X + offset
        wan_prefix = f"192.168.100.{8*i - 1}/29"
        wan_r0_ip = f"192.168.100.{8*i - 2}/29"
        wan_rn_ip = f"192.168.100.{8*i - 3}/29"

        # WAN
        net.addLink(routers[0], switches_wan[i - 1])
        net.addLink(routers[i], switches_wan[i - 1])
        routers[0].cmd(f'ip addr add {wan_r0_ip} dev r0-eth{i - 1}')
        routers[i].cmd(f'ip addr add {wan_rn_ip} dev r{i}-eth0')

        print(f"    Enlace WAN Suc.{i}: r0(r0-eth{i - 1} [{wan_r0_ip}]) <-> s{i}_wan <-> r{i}(r{i}-wan0 [{wan_rn_ip}])")

        # LAN
        net.addLink(routers[i], switches_lan[i - 1])
        net.addLink(hosts[i - 1], switches_lan[i - 1])

        routers[i].cmd(f'ip addr add 10.0.{i}.1/24 dev r{i}-eth1')
        print(f"    Enlace LAN Suc.{i}: r{i}(r{i}-lan0 [10.0.{i}.1/24]) <-> s{i}_lan <-> h{i}(h{i}-eth0 [10.0.{i}.254/24])")

    print("*** Iniciando Red")
    net.start()

    print("*** Configuring hosts")
    for host in hosts:
        host.cmd('ip route add default via 10.0.%d.1' % (hosts.index(host)+1))

    print("*** Iniciando CLI")
    CLI(net)

    print("*** Deteniendo red")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    dynamicNationalWanNetwork()
