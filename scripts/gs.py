import pypowsybl as psb

network = psb.network.load('../topo/topo.json')
network.get_generators()