from collections import deque


class Mesh:
    def __init__(self):
        self.edges = {}

    def add_vertex(self, vertex):
        assert vertex not in self.edges
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
            for next_vertex in self.edges[current_vertex]:
                submesh.add_edge((current_vertex, next_vertex))
                if next_vertex not in submesh.edges:
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


def neighbours(found_list, verbose=True):
    mesh = Mesh()
    for info in sorted(found_list):
        if info.arfcn not in mesh.vertices():
            mesh.add_vertex(info.arfcn)
            for neighbour in info.neighbours:
                mesh.add_edge((info.arfcn, neighbour))
    for vertex in mesh.vertices():
        if len(mesh.find_edges_from(vertex)) == 0:
            print "Cell '%s' has no neighbours" % vertex
        # submesh = mesh.find_submesh(vertex)
        # if submesh.size() < 3: # TODO: heuristics
        #     print "Cell only has few neighbours"
        if len(mesh.find_edges_to(vertex)) == 0:
            print "Cell '%s' is not referenced in the network" % vertex
