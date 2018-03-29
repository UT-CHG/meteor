from enum import Enum


class Node:
    def __init__(self, id, c1, c2, c3):
        self.id = id
        self.c1 = c1  # lon/x
        self.c2 = c2  # lat/y
        self.c3 = c3  # bath


class Element:
    def __init__(self, id, el_type, nodes):
        self.id = id
        self.el_type = el_type
        self.nodes = nodes


class ElementType(Enum):
    Triangle = 3
