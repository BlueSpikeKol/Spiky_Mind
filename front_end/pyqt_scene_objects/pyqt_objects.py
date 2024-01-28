from PyQt6.QtWidgets import QGraphicsItem, QGraphicsLineItem
from PyQt6.QtGui import QPen
from PyQt6.QtCore import QRectF, Qt, QPointF, QLineF, pyqtSignal, QObject


class NodeItemSignals(QObject):
    # Define signals here
    childrenChanged = pyqtSignal()
    positionChanged = pyqtSignal(QPointF)


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
        new_pos = QPointF(x, y)
        if new_pos != self.stored_pos:  # Check if the position actually changes
            if self.label == 'Star System Alpha':
                self.signals.positionChanged.emit(new_pos)
            self.update()  # Update the node's appearance
            self.visualizer.refreshView()
            self.stored_pos = new_pos

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
            print(self.label)
            print(self.stored_pos.x())
            self.visualizer.check_if_node_is_centered(self)
            self.setVisible(not self.isVisible())
            lefta, righta = self.visualizer.findImmediateSiblings(self)
            # Motor requirements assessment, Flux Analysis and Optimization
            self.printNodeStructure()
            # 'Continuous Improvement_2', 'Research motor specifications'
            # 'Core Material Selection', 'Inductance Calculation'

            # Optional: Toggle text display
            #self.text_displayed = not self.text_displayed
            self.update()  # Trigger a repaint

            # Accept the event to indicate it's been handled
            event.accept()
        else:
            super().mousePressEvent(event)

    def printNodeStructure(self):
        # Construct and print the dictionary representation
        node_structure = self.constructNodeDict()
        print(node_structure)

    def constructNodeDict(self):
        # Recursive function to construct the dictionary
        children_dict = {}
        for child in self.children_nodes:
            children_dict[child.label] = child.constructNodeDict()

        return {
            "metadata": self.metadata,
            "children": children_dict
        }

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
    def __init__(self, start_item, end_item):
        # Set start_item as the parent of the edge
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.start_point = None
        self.end_point = None
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setArrow()

    def setArrow(self):
        # Calculate start point at the bottom center of the start_item
        start_point = QPointF(
            self.start_item.stored_pos.x() + self.start_item.boundingRect().width() / 2,
            self.start_item.stored_pos.y() + self.start_item.boundingRect().height()
        )

        # Calculate end point at the top center of the end_item
        # Since EdgeItem is a child of start_item, convert end_point to start_item's coordinate system
        end_point_local = QPointF(
            self.end_item.stored_pos.x() + self.end_item.boundingRect().width() / 2,
            self.end_item.stored_pos.y()
        )
        end_point = self.mapFromItem(self.end_item, end_point_local)
        self.start_point = start_point
        self.end_point = end_point
        self.setLine(QLineF(start_point, end_point))

    def updatePosition(self):
        # Update the position of the edge based on the nodes it connects
        self.setArrow()

