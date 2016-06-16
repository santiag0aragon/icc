from collections import deque
from icc.aux import TowerRank


class Mesh:
    def __init__(self):
        self.edges = {}

    def add_vertex(self, vertex):
        if vertex not in self.edges:
            self.edges[vertex] = set()

    def add_edge(self, edge):
        (src, dst) = edge
        assert src in self.edges
        self.edges[src].add(dst)

    def vertices(self):
        return self.edges.keys()

    def size(self):
        return len(self.edges)

    def find_submesh(self, start):
        submesh = Mesh()
        vertex_queue = deque([start])
        while len(vertex_queue) != 0:
            current_vertex = vertex_queue.pop()
            submesh.add_vertex(current_vertex)
            if current_vertex in self.edges:
                for next_vertex in self.edges[current_vertex]:
                    submesh.add_edge((current_vertex, next_vertex))
                    if next_vertex in self.edges and next_vertex not in submesh.edges:
                        vertex_queue.append(next_vertex)
        return submesh

    def find_edges_from(self, vertex):
        edges = set()
        for dst in self.edges[vertex]:
            edges.add((vertex, dst))
        return edges

    def find_edges_to(self, vertex):
        edges = set()
        for src in self.edges:
            for dst in self.edges[src]:
                if dst == vertex:
                    edges.add((src, dst))
        return edges

    def __repr__(self):
        return "<Mesh(edges='%s')>" % str(self.edges)


min_submash_size = 3


def neighbours(found_list):
    ranks = []
    info_map = {}
    mesh = Mesh()
    for info in sorted(found_list):
        info_map[info.arfcn] = info
        mesh.add_vertex(info.arfcn)
        for neighbour in info.neighbours:
            mesh.add_edge((info.arfcn, neighbour))
    for vertex in mesh.vertices():
        rank = 0
        comment = None
        if len(mesh.find_edges_from(vertex)) == 0:  # TODO: can be 0 due to inconsistent tower scan
            rank = 2
            comment = "Cell '%s' has no neighbours" % vertex
        elif len(mesh.find_edges_to(vertex)) == 0:
            rank = 2
            comment = "Cell '%s' is not referenced in the network" % vertex
        elif mesh.find_submesh(vertex).size() < min_submash_size:
            rank = 1
            comment = "Cell only has few neighbours"
        else:
            comment = "Cell has neighbours and is referenced in the network"
        ranks.append(TowerRank(rank, 'neighbours', comment, info_map[vertex].cellobservation_id))
    return ranks
