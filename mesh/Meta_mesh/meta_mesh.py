class MetaMesh:
    def __init__(self, mesh_file_path):
        with open(mesh_file_path) as mesh_file:
            self.mesh_name = mesh_file.readline()
