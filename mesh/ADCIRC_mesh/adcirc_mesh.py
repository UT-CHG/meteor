import sys

from mesh.mesh_geom import (Node, Element, ElementType)


class AdcirMesh:
    def __init__(self, mesh_file_path):
        with open(mesh_file_path) as mesh_file:
            self.mesh_name = mesh_file.readline()

            num_elements, num_nodes = mesh_file.readline().split()

            self.num_elements = int(num_elements)
            self.num_nodes = int(num_nodes)

            self.nodes = []
            for node_id in range(0, self.num_nodes):
                node_string = mesh_file.readline().split()

                self.nodes.append(
                    Node(int(node_string[0]), float(node_string[1]), float(node_string[2]), float(node_string[3])))

            self.elements = []
            for element_id in range(0, self.num_elements):
                element_string = mesh_file.readline().split()

                if int(element_string[1]) == 3:
                    self.elements.append(
                        Element(
                            int(element_string[0]), ElementType.Triangle,
                            {int(element_string[2]),
                             int(element_string[3]),
                             int(element_string[4])}))
                else:
                    print("Undefined element type: {}. Exiting!".format(element_string[1]))
                    sys.exit()
