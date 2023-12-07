from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsLineItem
from PyQt6.QtGui import QPainter, QPen, QTransform
from PyQt6.QtCore import QRectF, Qt, QPointF, QLineF, QTimer
import sys


class NodeItem(QGraphicsItem):
    def __init__(self, label, metadata="", parent=None, visualizer=None):
        super().__init__(parent)
        self.label = label
        self.metadata = metadata
        self.parent_node = parent
        self.visualizer = visualizer
        self.children_nodes = []
        self.sibling_nodes = []
        self.edges = []
        self.text_displayed = False
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
        #width = max(100, len(text) * 6)  # Example calculation
        width = 60
        height = 40
        self.rect = QRectF(0, 0, width, height)

    def setStoredPos(self, x, y):
        """Set the stored position of the node."""
        self.stored_pos = QPointF(x, y)
        self.update()  # Update the node's appearance
        # Assuming DataVisualizer instance is accessible via self.visualizer
        self.visualizer.refreshView()

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
            #self.text_displayed = not self.text_displayed
            #self.update()  # Trigger a repaint to show/hide metadata
            # Toggle visibility of other nodes
            self.toggleOtherNodesVisibility()
            self.printSameLabelNodePositions()
            self.update()  # Trigger a repaint


    def toggleOtherNodesVisibility(self):
        for node in self.visualizer.loaded_nodes.values():
            if node.label != self.label:
                node.setVisible(not node.isVisible())

    def printSameLabelNodePositions(self):
        print(f"Positions of nodes with label '{self.label}':")
        for node in self.visualizer.loaded_nodes.values():
            if node.label == self.label:
                print(f"- Node '{node.label}' at position {node.stored_pos}")

    def boundingRect(self):
        """Return the bounding rectangle of the item based on stored position and size."""
        return QRectF(self.stored_pos.x(), self.stored_pos.y(), self.rect.width(), self.rect.height())

    def paint(self, painter, option, widget=None):
        # Set brush color based on dynamic loading
        brush_color = Qt.GlobalColor.green
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
    def __init__(self, start_item, end_item, parent=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setArrow()

    def setArrow(self):
        start_rect = self.start_item.boundingRect()
        end_rect = self.end_item.boundingRect()

        # Calculate start and end points using stored_pos
        start_point = QPointF(
            self.start_item.stored_pos.x() + start_rect.width() / 2,
            self.start_item.stored_pos.y() + start_rect.height()
        )
        end_point = QPointF(
            self.end_item.stored_pos.x() + end_rect.width() / 2,
            self.end_item.stored_pos.y()
        )

        self.setLine(QLineF(start_point, end_point))

    def updatePosition(self):
        # Update the position of the edge based on the nodes it connects
        self.setArrow()


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, visualizer):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.visualizer = visualizer
        self._zoom_factor = 1.15
        self._is_right_mouse_button_pressed = False
        self._last_mouse_position = None

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.visualizer.load_visible_nodes_with_buffer()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = self._zoom_factor if event.angleDelta().y() > 0 else 1 / self._zoom_factor
            self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._is_right_mouse_button_pressed = True
            self._last_mouse_position = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_right_mouse_button_pressed:
            new_pos = event.position()
            delta = self._last_mouse_position - new_pos
            self._last_mouse_position = new_pos

            # Convert delta.x() and delta.y() to integers
            delta_x = int(delta.x())
            delta_y = int(delta.y())

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta_x)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta_y)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._is_right_mouse_button_pressed = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_W:
            self.showAllNodes()
        else:
            super().keyPressEvent(event)

    def showAllNodes(self):
        for node in self.visualizer.loaded_nodes.values():
            node.setVisible(True)


class DataVisualizer:
    def __init__(self, data):
        self.data = data
        self.app = QApplication(sys.argv)
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        self.loaded_nodes = {}  # Dictionary to store NodeItem objects
        self.create_nodes(data)  # Create NodeItem objects from the data
        self.updateSceneRect()

    def refreshView(self):
        """Refresh the graphics view."""
        self.view.update()  # Assuming the QGraphicsView instance is stored in self.view
        QApplication.processEvents()

    def updateSceneRect(self):
        # Calculate the bounding box of all nodes
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        border_padding = 200  # Extra space around the nodes

        for node in self.loaded_nodes.values():
            rect = node.sceneBoundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())

        # Set scene dimensions based on nodes' positions
        scene_width = max_x - min_x + 2 * border_padding
        scene_height = max_y - min_y + 2 * border_padding
        self.scene.setSceneRect(min_x - border_padding, min_y - border_padding, scene_width, scene_height)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def updateAllEdges(self):
        for node_item in self.loaded_nodes.values():
            node_item.updateEdges()

    def load_visible_nodes_with_buffer(self):
        # Define a buffer zone around the visible area
        buffer = 50
        extended_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect().adjusted(-buffer, -buffer,
                                                                                                  buffer, buffer)
        self._load_nodes(self.data, extended_rect)
        self.updateAllEdges()

    def create_nodes(self, data, parent=None):
        for key, value in data.items():
            metadata = value.get('metadata', '')
            # Pass self (DataVisualizer instance) to NodeItem
            node_item = NodeItem(key, metadata, parent, visualizer=self)
            self.loaded_nodes[key] = node_item

            if parent:
                edge = EdgeItem(parent, node_item)
                self.scene.addItem(edge)
                parent.edges.append(edge)
                node_item.edges.append(edge)

                parent.addChild(node_item)
                for sibling in parent.children_nodes:
                    if sibling is not node_item:
                        sibling.addSibling(node_item)
                        node_item.addSibling(sibling)

            if 'children' in value:
                self.create_nodes(value['children'], node_item)

    def initial_load(self, data):

        # Build the tree structure as a list of levels with sibling groups
        self.tree_levels = self.build_tree_levels(data)

        # Position nodes based on the tree structure
        self.position_nodes()

        # Update the scene boundary to encompass all nodes
        self.updateSceneRect()

    def build_tree_levels(self, data, depth=0, tree_levels=None, parent=None):
        if tree_levels is None:
            tree_levels = []

        while len(tree_levels) <= depth:
            tree_levels.append([])

        sibling_groups = {}
        for key, value in data.items():
            parent_key = parent.label if parent else 'root'
            if parent_key not in sibling_groups:
                sibling_groups[parent_key] = {'nodes': [], 'total_width': 0}

            node_item = self.loaded_nodes[key]
            sibling_groups[parent_key]['nodes'].append(node_item)
            node_item_width = node_item.boundingRect().width()
            sibling_groups[parent_key]['total_width'] += node_item_width

            if 'children' in value:
                self.build_tree_levels(value['children'], depth + 1, tree_levels, node_item)

        for group in sibling_groups.values():
            tree_levels[depth].append(group)

        return tree_levels

    def position_nodes(self):
        """
        Position nodes based on their level in the tree and adjust to prevent overlaps.
        Each level is separated by 100 units on the y-axis.
        """
        self.position_nodes_flat()
        self.center_children_below_parents()
        self.adjust_positions_to_prevent_overlaps()
        self.recenter_parents_above_children()
        self.check_doubles()

    def check_doubles(self):
        """
        Check for nodes on the same level as the root and identify duplicates.
        """
        root_level_nodes = []  # Nodes on the same level as the root
        duplicate_nodes = []   # Nodes without duplicates
        duplicate_check = {}   # Dictionary to track duplicates

        for node in self.loaded_nodes.values():
            if node.stored_pos.y() == 0:
                root_level_nodes.append(node)

        for node in root_level_nodes:
            node_label = node.label
            if node_label in duplicate_check:
                # Node is a duplicate
                duplicate_nodes.append(node_label)
            else:
                # Node is not a duplicate
                duplicate_check[node_label] = True

        # Print the results
        print("Nodes on the same level as the root:")
        for node in root_level_nodes:
            print(f"- {node.label}")

        print("\nDuplicate nodes on the same level:")
        for node_label in duplicate_nodes:
            print(f"- {node_label}")

        unique_root_level_nodes = [node.label for node in root_level_nodes if node.label not in duplicate_nodes]
        print("\nNodes on the same level without duplicates:")
        for node_label in unique_root_level_nodes:
            print(f"- {node_label}")

    def position_nodes_flat(self):
        """
        Position nodes in a flat structure based on their level, only adjusting the y-axis.
        """
        y_spacing = 100  # Vertical spacing between levels

        for level_index, level in enumerate(self.tree_levels):
            y_position = level_index * y_spacing

            for sibling_group in level:
                for node in sibling_group['nodes']:
                    # Keep the current x position, only update the y position
                    current_x = node.stored_pos.x()
                    node.setStoredPos(current_x, y_position)

    def center_children_below_parents(self):
        """
        Center each group of sibling nodes below their parent node.
        """
        for level in self.tree_levels:
            for sibling_group in level:
                for node in sibling_group['nodes']:
                    if node.children_nodes:
                        self.center_children_group_below_parent(node)

    def center_children_group_below_parent(self, parent_node):
        """
        Center a group of sibling nodes (children of the same parent) below their parent node.
        """
        if not parent_node.children_nodes:
            return

        total_children_width = sum(child.boundingRect().width() for child in parent_node.children_nodes)
        total_spacing = len(parent_node.children_nodes) - 1
        group_width = total_children_width + total_spacing

        parent_center_x = parent_node.stored_pos.x() + parent_node.boundingRect().width() / 2
        leftmost_x = parent_center_x - group_width / 2

        current_x = leftmost_x
        for child in parent_node.children_nodes:
            child.setStoredPos(current_x, child.stored_pos.y())
            current_x += child.boundingRect().width()

    def adjust_positions_to_prevent_overlaps(self):
        """
        Adjust positions of nodes to prevent overlaps by shifting the current group.
        """
        overlap = True
        max_iterations = 1  # Set the maximum number of iterations

        iteration = 0
        while overlap and iteration < max_iterations:
            overlap = False
            for level_index, level in enumerate(self.tree_levels):
                for i in range(len(level) - 1):
                    if not level[i]['nodes'] or not level[i + 1]['nodes']:
                        continue

                    rightmost_node = level[i]['nodes'][-1]
                    leftmost_node_next_group = level[i + 1]['nodes'][0]
                    if iteration == 1:
                        print('nothing')

                    if rightmost_node.stored_pos.x() + rightmost_node.boundingRect().width() > leftmost_node_next_group.stored_pos.x():
                        shift_amount = leftmost_node_next_group.stored_pos.x() - (
                                rightmost_node.stored_pos.x() + rightmost_node.boundingRect().width())
                        parent_of_current_group = rightmost_node.parent_node
                        if parent_of_current_group:
                            print(f"Shifting level {level_index}, group {i} leftward by {shift_amount}")
                            self.shift_sibling_group(parent_of_current_group, shift_amount)
                            overlap = True

            iteration += 1

    def shift_sibling_group(self, parent_node, shift_amount):
        """
        Shift an entire sibling group (all children of a common parent) by a specified amount.
        """
        for child in parent_node.children_nodes:
            child.setStoredPos(child.stored_pos.x() + shift_amount, child.stored_pos.y())
            self.shift_subtree(child, shift_amount)

    def shift_subtree(self, node, shift_amount):
        """
        Recursively shift a node and its descendants.
        """
        for child in node.children_nodes:
            child.setStoredPos(child.stored_pos.x() + shift_amount, child.stored_pos.y())
            self.shift_subtree(child, shift_amount)

    def recenter_parents_above_children(self):
        """
        Recenter each parent node above its children.
        """
        for level in self.tree_levels:
            for sibling_group in level:
                for node in sibling_group['nodes']:
                    if node.children_nodes:
                        self.center_parent_above_children(node)

    def center_parent_above_children(self, parent_node):
        """
        Center a parent node above its children.
        """
        if not parent_node.children_nodes:
            return

        children_leftmost_x = min(child.stored_pos.x() for child in parent_node.children_nodes)
        children_rightmost_x = max(child.stored_pos.x() + child.boundingRect().width() for child in parent_node.children_nodes)
        children_center_x = (children_leftmost_x + children_rightmost_x) / 2

        # Set the parent node's x-coordinate to center it above the children
        parent_x = children_center_x - parent_node.boundingRect().width() / 2
        parent_node.setStoredPos(parent_x, parent_node.stored_pos.y())

    def visualize_data(self):
        if isinstance(self.data, dict):
            self.initial_load(self.data)
            self.view.show()
            sys.exit(self.app.exec())
        else:
            print("Invalid data format for visualization")

    def _load_nodes(self, data, visible_rect, depth=0):

        for key, value in data.items():
            self.process_node(key, visible_rect)
            if 'children' in value:
                self._load_nodes(value['children'], visible_rect, depth + 1)

    def process_node(self, key, visible_rect):
        node_item = self.loaded_nodes.get(key)
        if node_item:
            node_x, node_y = node_item.stored_pos.x(), node_item.stored_pos.y()
            node_width = node_item.rect.width()
            node_height = node_item.rect.height()
            node_rect = QRectF(node_x, node_y, node_width, node_height)

            if node_rect.intersects(visible_rect):
                if node_item not in self.scene.items():
                    self.scene.addItem(node_item)
                    print(f"Debug: Added node '{key}' to the scene")
            else:
                if node_item in self.scene.items():
                    self.scene.removeItem(node_item)
                    print(f"Warning: Node '{key}' removed from the scene")


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

#visualizer = DataVisualizer(data)
#visualizer.visualize_data()
