from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsLineItem
from PyQt6.QtGui import QPainter, QPen, QTransform
from PyQt6.QtCore import QRectF, Qt, QPointF, QLineF, QTimer, pyqtSignal, QObject
import sys


class NodeItemSignals(QObject):
    # Define signals here
    childrenChanged = pyqtSignal()


class NodeItem(QGraphicsItem):
    def __init__(self, label, metadata="", parent=None, visualizer=None):
        super().__init__()
        self.signals = NodeItemSignals()
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

        if parent:
            self.setParentItem(parent)

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
        # width = max(100, len(text) * 6)  # Example calculation
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
            # Move the node 20 pixels to the left
            print(self.childItems())
            current_pos = self.stored_pos

            # Update the stored position
            self.setStoredPos(current_pos.x() - 2, current_pos.y())

            # Update edges connected to this node
            for edge in self.edges:
                edge.updatePosition()

            # Optional: Toggle text display
            self.text_displayed = not self.text_displayed
            self.update()  # Trigger a repaint

            # Accept the event to indicate it's been handled
            event.accept()
        else:
            super().mousePressEvent(event)

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


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, visualizer):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.visualizer = visualizer
        self._zoom_factor = 1.15
        self._is_right_mouse_button_pressed = False
        self._last_mouse_position = None

    def mouseMoveEvent(self, event):
        if self._is_right_mouse_button_pressed:
            new_pos = event.position()
            delta = self._last_mouse_position - new_pos
            self._last_mouse_position = new_pos

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

    def zoomInEvent(self):  # Assuming you have a method to handle zoom in
        self.visualizer.update_visible_nodes(action="zoom_in")

    def zoomOutEvent(self):  # Assuming you have a method to handle zoom out
        self.visualizer.update_visible_nodes(action="zoom_out")

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.visualizer.update_visible_nodes(action="pan")

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_W:
            self.showAllNodes()
        else:
            super().keyPressEvent(event)

    def showAllNodes(self):
        for node in self.visualizer.loaded_nodes.values():
            node.setVisible(True)


class CustomGraphicsScene(QGraphicsScene):
    def customAddItem(self, item):
        # Store the original parent of the item
        original_parent = item.parentItem()

        # Print the children of the parent before adding the item
        parent_children_before = original_parent.childItems() if original_parent else []
        if original_parent:
            print(f"Children of Parent ({original_parent}) before adding {item}:")
            for child in parent_children_before:
                print(child)

        # Print the item's own children before adding it
        item_children_before = item.childItems()
        print(f"Children of Item ({item}) before adding:")
        for child in item_children_before:
            print(child)

        # Add the item to the scene
        super().addItem(item)

        # Restore the original parent of the item if it has changed
        if item.parentItem() != original_parent:
            print("Irregularity detected: Parent changed after adding. Restoring original parent.")
            item.setParentItem(original_parent)

        # Print the children of the parent after adding the item
        parent_children_after = original_parent.childItems() if original_parent else []
        if original_parent:
            print(f"Children of Parent ({original_parent}) after adding {item}:")
            for child in parent_children_after:
                print(child)
            if set(parent_children_before) != set(parent_children_after):
                print(f"Parent's children changed after adding {item}.")
            else:
                print("Everything worked fine!")

        # Check and restore the original children of the item if they have changed
        for child in item_children_before:
            if child.parentItem() != item:
                print(f"Irregularity detected: Child {child} lost its parent. Restoring original parent.")
                child.setParentItem(item)

        # Print the item's own children after adding it
        item_children_after = item.childItems()
        print(f"Children of Item ({item}) after adding:")
        for child in item_children_after:
            print(child)
        if set(item_children_before) != set(item_children_after):
            print(f"Item's children changed after adding.")


class DataVisualizer:
    def __init__(self, data):
        self.data = data
        self.app = QApplication(sys.argv)
        self.scene = CustomGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        self.loaded_nodes = {}  # Dictionary to store NodeItem objects
        self.create_nodes(data)  # Create NodeItem objects from the data
        self.updateSceneRect()
        self.nodes_in_view = set()
        self.nodes_not_in_view = set()
        self.last_viewport_rect = None
        self.deleted_edges = []  # List to track deleted edges
        self.edges_are_cleaned = False

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
    def refreshView(self):
        """Refresh the graphics view."""
        self.view.update()  # Assuming the QGraphicsView instance is stored in self.view
        QApplication.processEvents()

    def create_nodes(self, data, parent=None, x_offset=0):
        if not hasattr(self, 'name_counter'):
            self.name_counter = {}  # Initialize a counter for node names

        sibling_offset = 100  # Horizontal space between siblings

        for original_key, value in data.items():
            key = original_key
            # Check if the key already exists and modify it if necessary
            while key in self.loaded_nodes:
                self.name_counter[original_key] = self.name_counter.get(original_key, 1) + 1
                key = f"{original_key}_{self.name_counter[original_key]}"

            metadata = value.get('metadata', '')
            node_item = NodeItem(key, metadata, parent, visualizer=self)
            self.loaded_nodes[key] = node_item

            # Set the position of the node item
            x_position = x_offset if parent is None else parent.x() + x_offset
            node_item.setPos(x_position, 0)

            if parent:
                # Add child and sibling relationships
                parent.addChild(node_item)
                for sibling in parent.children_nodes:
                    if sibling is not node_item:
                        sibling.addSibling(node_item)
                        node_item.addSibling(sibling)

            if 'children' in value:
                # Recursively create child nodes
                self.create_nodes(value['children'], node_item, sibling_offset)

            # Increment the x_offset for the next sibling
            x_offset += sibling_offset

    def visualize_data(self):
        if isinstance(self.data, dict):
            #self.initial_load()
            self.view.show()
            # self.update_all_edges()
            sys.exit(self.app.exec())
        else:
            print("Invalid data format for visualization")

    def update_visible_nodes(self, action):
        visible_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        self._load_nodes(visible_rect, action)
        if not self.edges_are_cleaned:
            # self.cleanup_edges()
            self.edges_are_cleaned = True

    def initial_load(self):
        self.set_up_nodes(self.data, None, 0)

    def set_up_nodes(self, subtree, parent, x_pos):
        if isinstance(subtree, dict):
            for label, children in subtree.items():
                # Create a new NodeItem for each node in the dictionary
                node = NodeItem(label, parent=parent)
                node.setPos(x_pos, 0)  # Set the position of the node

                # Add the node to the scene
                self.scene.addItem(node)

                # Recursively create child nodes
                self.set_up_nodes(children, node, x_pos + 100)  # Increment x_pos for child nodes

                # Increment x_pos for the next sibling
                x_pos += 100

    def _load_nodes(self, visible_rect, action):
        if action == "zoom_in":
            # Check for items to remove
            for node_id, node_item in self.nodes_in_view:
                self.process_node(node_item, visible_rect, remove_only=True)
        elif action == "zoom_out":
            # Check for items to add
            for node_id, node_item in self.nodes_not_in_view:
                self.process_node(node_item, visible_rect, add_only=True)
        else:  # action == "pan"
            # Check for both adding and removing
            for node_id, node_item in self.loaded_nodes.items():
                self.process_node(node_item, visible_rect)

    def process_node(self, node_item, visible_rect, add_only=False, remove_only=False):
        if node_item:
            node_rect = node_item.sceneBoundingRect()

            if node_rect.intersects(visible_rect):
                if not remove_only and node_item not in self.nodes_in_view:
                    self.add_node_to_scene(node_item, visible_rect)
            else:
                if not add_only and node_item in self.nodes_in_view:
                    self.remove_node_from_scene(node_item)

    def add_node_to_scene(self, node_item, visible_rect):
        # Add the node to the scene
        self.scene.customAddItem(node_item)
        self.nodes_in_view.add(node_item)
        self.nodes_not_in_view.discard(node_item)

        # Check and remove direct children that are not in the visible area
        for child in node_item.childItems():
            if not child.sceneBoundingRect().intersects(visible_rect):
                self.scene.removeItem(child)
                self.nodes_not_in_view.add(child)

    def remove_node_from_scene(self, node_item):
        if isinstance(node_item, NodeItem):
            # Remove the node from the scene
            self.scene.removeItem(node_item)
            self.nodes_in_view.discard(node_item)
            self.nodes_not_in_view.add(node_item)

            # Re-add edges if one of the connected nodes is still in view
            for edge in node_item.edges:
                other_node = edge.end_item if edge.start_item == node_item else edge.start_item
                if other_node in self.nodes_in_view and edge not in self.nodes_in_view:
                    self.scene.customAddItem(edge)
                    self.nodes_in_view.add(edge)

            # Handle children independently
            for child in node_item.childItems():
                if child in self.nodes_in_view and isinstance(child, NodeItem):
                    self.remove_node_from_scene(child)


if __name__ == "__main__":
    # Sample data for testing
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

    visualizer = DataVisualizer(data)
    visualizer.visualize_data()
