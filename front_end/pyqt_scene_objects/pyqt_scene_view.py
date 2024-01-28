from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt

from front_end.pyqt_scene_objects.pyqt_objects import NodeItem

class TreeSceneView(QGraphicsView):
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

    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key.Key_P:  # Check if 'P' key is pressed
    #         self.printVisibleNodes()
    #     elif event.key() == Qt.Key.Key_O:
    #         self.removeSpecificNode("Planet Earth")
    #     if event.key() == Qt.Key.Key_Y:
    #         self.toggleVisibilityOfSpecificNode("Planet Earth")
    #     if event.key() == Qt.Key.Key_T:  # Check if 'T' key is pressed
    #         self.makeAllNodesVisible()
    #         self.zoomOnTestingNode()

    def zoomOnTestingNode(self):
        # Search for the node with the label "Testing"
        testing_node = None
        for item in self.scene().items():
            if isinstance(item, NodeItem) and item.label == 'Wiring Connections':
                testing_node = item
                break

        if testing_node:
            print(testing_node.isVisible())
            # Center the view on the "Testing" node
            self.centerOn(testing_node)

            # Apply zoom
            zoom_factor = 2  # Adjust zoom factor as needed
            self.scale(zoom_factor, zoom_factor)
            # Optionally, adjust the view's rectangle to ensure the node is fully visible
            # self.ensureVisible(testing_node)
        else:
            print("Node 'Testing' not found.")

    def makeAllNodesVisible(self):
        for node in self.visualizer.loaded_nodes.values():
            node.setVisible(True)

        # Print all elements in the scene
        print("All elements in the scene:")
        for item in self.scene().items():
            print(f"Item: {item}, Type: {type(item).__name__}, Position: {item.pos()}")

        self.visualizer.refreshView()

    def toggleVisibilityOfSpecificNode(self, label):
        for node in self.visualizer.nodes_in_view:
            if isinstance(node, NodeItem) and node.label == label:
                node.setVisible(not node.isVisible())  # Toggle visibility
                print(f"Node '{label}' visibility toggled.")
                break  # Remove this line if there can be multiple nodes with the same label

    def printVisibleNodes(self):
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        for node in self.visualizer.nodes_in_view:
            if isinstance(node, NodeItem):
                if node.sceneBoundingRect().intersects(visible_rect):
                    if node.scene() != self.visualizer.scene:
                        print(
                            f"Node '{node.label}' is in the visible area but not in the scene. Adding it to the scene.")
                        self.visualizer.scene.customAddItem(node)
                    else:
                        print(node.label)

    def removeSpecificNode(self, label):
        for node in self.visualizer.nodes_in_view:
            if isinstance(node, NodeItem) and node.label == label:
                self.visualizer.scene.customRemoveItem(node)
                # Check if the node is still in the scene
                if node.scene() == self.visualizer.scene:
                    print(f"Removal failed: Node '{label}' is still in the scene.")
                else:
                    print(f"Node '{label}' removed from the scene.")
                break  # Remove this line if there can be multiple nodes with the same label


# class CustomGraphicsScene(QGraphicsScene):
#     def customAddItem(self, item):
#         # Store the original parent of the item
#         original_parent = item.parentItem()
#
#         # Add the item to the scene
#         super().addItem(item)
#
#         # Restore the original parent of the item if it has changed
#         if item.parentItem() != original_parent:
#             item.setParentItem(original_parent)
#
#     def customRemoveItem(self, item):
#         # Store the original parent of the item
#         original_parent = item.parentItem()
#
#         # Remove the item from the scene
#         super().removeItem(item)
#
#         if item.parentItem() != original_parent:
#             item.setParentItem(original_parent)