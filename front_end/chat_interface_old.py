import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLineEdit, QLineEdit, \
    QPushButton, QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor


class ChatInterface(QWidget):
    def __init__(self, return_input_to_agent):
        super().__init__()
        self.return_input_to_agent = return_input_to_agent
        self.layout = QVBoxLayout(self)
        self.initUI()

    def initUI(self):
        # Chat display area
        self.chatDisplay = QTextEdit()
        self.chatDisplay.setReadOnly(True)
        self.layout.addWidget(self.chatDisplay)

        # Input area
        inputLayout = QHBoxLayout()
        self.inputBox = QLineEdit()
        self.sendButton = QPushButton('Send')
        inputLayout.addWidget(self.inputBox)
        inputLayout.addWidget(self.sendButton)

        self.layout.addLayout(inputLayout)

        # Connect signals and slots
        self.sendButton.clicked.connect(self.on_send)
        self.inputBox.returnPressed.connect(self.on_send)

        # Set window title and size
        self.setWindowTitle('Spiky Chat')
        self.resize(400, 500)

    def on_send(self):
        user_text = self.inputBox.text().strip()
        if user_text:
            self.display_message(user_text, is_user=True)
            self.inputBox.clear()
            if self.return_input_to_agent:
                self.return_input_to_agent(user_text)

    def display_message(self, message, is_user):
        # Check if the last widget is a QTextEdit and from the same sender
        if self.layout.count() > 0:
            last_widget = self.layout.itemAt(self.layout.count() - 1).widget()
            if isinstance(last_widget, QTextEdit):
                if (is_user and last_widget.alignment() == Qt.AlignmentFlag.AlignRight) or \
                   (not is_user and last_widget.alignment() == Qt.AlignmentFlag.AlignLeft):
                    # Append message to the last widget if it's from the same sender
                    last_widget.setText(last_widget.toPlainText() + "\n" + message)
                    return

        # Create a new message box for a different sender
        message_box = QTextEdit()
        message_box.setReadOnly(True)
        if is_user:
            message_box.setStyleSheet("background-color: lightblue; border: 1px solid blue;")
            message_box.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            message_box.setStyleSheet("background-color: lightgreen; border: 1px solid green;")
            message_box.setAlignment(Qt.AlignmentFlag.AlignLeft)

        message_box.setText(message)
        self.layout.addWidget(message_box)
        self.ensure_visibility()
    def ensure_visibility(self):
        # Make sure all widgets are visible
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_G:
            self.set_all_widgets_visible()

    def set_all_widgets_visible(self):
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(True)

    def print_widget_info(self):
        for i in range(self.layout.count()):
            # Get the layout item at the current index
            layout_item = self.layout.itemAt(i)
            widget = layout_item.widget()

            # Check if the layout item is a widget
            if widget is not None:
                widget_info = f"Widget at index {i}: {widget.__class__.__name__}, Visible: {widget.isVisible()}"

                # Get geometry and position information
                geometry = widget.geometry()
                widget_info += f", Geometry: (x={geometry.x()}, y={geometry.y()}, width={geometry.width()}, height={geometry.height()})"

                # If the widget is a QTextEdit and not visible, print its text content
                if isinstance(widget, QTextEdit):
                    text_content = widget.toPlainText()
                    widget_info += f", Text: '{text_content}'"

                # Print the widget information
                print(widget_info)

    def get_html_content(self):
        return self.chatDisplay.toHtml()
