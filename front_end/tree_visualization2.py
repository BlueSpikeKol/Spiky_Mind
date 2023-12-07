from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsLineItem
from PyQt6.QtCore import QPointF, QRectF, Qt, QLineF
from PyQt6.QtGui import QPainter, QPen

class NodeItem(QGraphicsItem):
    def __init__(self, label, metadata="", parent=None, dynamically_loaded=False):
        super().__init__(parent)
        self.label = label
        self.metadata = metadata
        self.parent_node = parent
        self.children_nodes = []
        self.sibling_nodes = []
        self.edges = []
        self.text_displayed = False
        self.dynamically_loaded = dynamically_loaded
        self.prepareGeometryChange()
        self.updateSize()
        self.stored_pos = QPointF(0, 0)  # Initialize stored position

    def addChild(self, child_node):
        """Add a child to this node."""
        self.children_nodes.append(child_node)

    def addSibling(self, sibling_node):
        """Add a sibling to this node."""
        self.sibling_nodes.append(sibling_node)

    def updateSize(self):
        # Calculate the required size based on the label and metadata
        text = self.label + (": " + self.metadata if self.metadata else "")
        # Adjust the logic for size calculation as needed
        width = max(100, len(text) * 6)  # Example calculation
        height = 50  # Adjust as needed
        self.rect = QRectF(0, 0, width, height)

    def setStoredPos(self, x, y):
        """Set the stored position of the node."""
        self.stored_pos = QPointF(x, y)

    def updateEdges(self):
        """Update the position of all edges connected to this node."""
        for edge in self.edges:
            edge.updatePosition()

    def setLabel(self, label):
        self.label = label
        self.updateSize()

    def setMetadata(self, metadata):
        self.metadata = metadata
        self.updateSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.text_displayed = not self.text_displayed
            self.update()  # Trigger a repaint to show/hide metadata

    def boundingRect(self):
        """Return the bounding rectangle of the item based on stored position and size."""
        return QRectF(self.stored_pos.x(), self.stored_pos.y(), self.rect.width(), self.rect.height())

    def paint(self, painter, option, widget=None):
        # Set brush color based on dynamic loading
        brush_color = Qt.GlobalColor.green if self.dynamically_loaded else Qt.GlobalColor.green
        painter.setBrush(brush_color)
        # Set pen to black for the border of the rectangle
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawRect(self.boundingRect())

        # Set pen to black for the text
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self.label)

        if self.text_displayed and self.metadata:
            # Display metadata (optional)
            # This will also be in black. Adjust as needed.
            painter.drawText(self.boundingRect().adjusted(0, 20, 0, 0), Qt.AlignmentFlag.AlignCenter, self.metadata)
class EdgeItem(QGraphicsLineItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.updatePosition()

    def updatePosition(self):
        start_point = self.start_item.stored_pos + QPointF(self.start_item.rect.width() / 2, self.start_item.rect.height())
        end_point = self.end_item.stored_pos + QPointF(self.end_item.rect.width() / 2, 0)
        self.setLine(QLineF(start_point, end_point))

def build_tree_levels(data, depth=0, tree_levels=None, parent=None, loaded_nodes=None):
    if tree_levels is None:
        tree_levels = []
    if loaded_nodes is None:
        loaded_nodes = {}

    while len(tree_levels) <= depth:
        tree_levels.append([])

    sibling_groups = {}
    for key, value in data.items():
        if key not in loaded_nodes:
            loaded_nodes[key] = NodeItem(key)
            if parent:
                parent.children_nodes.append(loaded_nodes[key])
                loaded_nodes[key].parent_node = parent
            scene.addItem(loaded_nodes[key])

        node_item = loaded_nodes[key]
        parent_key = parent.label if parent else 'root'
        if parent_key not in sibling_groups:
            sibling_groups[parent_key] = {'nodes': [], 'total_width': 0}

        sibling_groups[parent_key]['nodes'].append(node_item)
        node_item_width = node_item.boundingRect().width()
        sibling_groups[parent_key]['total_width'] += node_item_width

        if 'children' in value:
            build_tree_levels(value['children'], depth + 1, tree_levels, node_item, loaded_nodes)

    for group in sibling_groups.values():
        tree_levels[depth].append(group)

    return tree_levels

def position_and_create_edges(tree_levels, sibling_offset=20, y_offset=100):
    for depth, groups in enumerate(tree_levels):
        y = depth * y_offset
        for group in groups:
            total_width = group['total_width']
            x = 0  # Starting x position for each level
            for node in group['nodes']:
                node.setStoredPos(x, y)
                x += node.boundingRect().width() + sibling_offset
                if node.parent_node:
                    edge = EdgeItem(node.parent_node, node)
                    scene.addItem(edge)

data = {
    "Universe": {
        "metadata": "Level 1",
        "children": {
            "Galaxy Milky Way": {
                "metadata": "Level 2",
                "children": {
                    "Solar System": {
                        "metadata": "Level 3",
                        "children": {
                            "Planet Earth": {
                                "metadata": "Level 4",
                                "children": {
                                    "Continent Africa": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    },
                                    "Continent Asia": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    }
                                }
                            },
                            "Planet Mars": {
                                "metadata": "Level 4",
                                "children": {
                                    "Moon Phobos": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    },
                                    "Moon Deimos": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    }
                                }
                            },
                            "Planet Venus": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    },
                    "Andromeda Galaxy": {
                        "metadata": "Level 3",
                        "children": {
                            "Star System Alpha": {
                                "metadata": "Level 4",
                                "children": {}
                            },
                            "Star System Beta": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    },
                    "Black Hole": {
                        "metadata": "Level 3",
                        "children": {
                            "Event Horizon": {
                                "metadata": "Level 4",
                                "children": {
                                    "Singularity Point": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    },
                                    "Photon Sphere": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    }
                                }
                            },
                            "Accretion Disk": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    }
                }
            },
            "Galaxy Andromeda": {
                "metadata": "Level 2",
                "children": {
                    "Star System Gamma": {
                        "metadata": "Level 3",
                        "children": {}
                    },
                    "Star System Delta": {
                        "metadata": "Level 3",
                        "children": {
                            "Planet Omega": {
                                "metadata": "Level 4",
                                "children": {}
                            },
                            "Planet Sigma": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    },
                    "Nebula Epsilon": {
                        "metadata": "Level 3",
                        "children": {}
                    }
                }
            },
            "Intergalactic Space": {
                "metadata": "Level 2",
                "children": {}
            }
        }
    }
}

app = QApplication([])
scene = QGraphicsScene()
view = QGraphicsView(scene)
view.setRenderHint(QPainter.RenderHint.Antialiasing)

root_node = NodeItem("Universe")
scene.addItem(root_node)
loaded_nodes = {"Universe": root_node}
tree_levels = build_tree_levels(data, 0, None, root_node, loaded_nodes)
position_and_create_edges(tree_levels)

view.show()
app.exec()
