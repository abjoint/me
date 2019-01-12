def is_two_ip_in_same_subnet(self, ip1, ip2, netmask):
    iptoint = lambda ip:sum([256**j*int(i) for j,i in enumerate(ip.split('.')[::-1])])
    ip1_int = iptoint(str(ip1))
    ip2_int = iptoint(str(ip2))
    netmask_int = iptoint(str(netmask))
    if ((ip1_int & netmask_int) == (ip2_int & netmask_int)):
        return True
    else:
        return False