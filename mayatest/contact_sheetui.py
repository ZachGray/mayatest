"""
Contact Sheet UI
A tool to compare images in a directory and display them in a contact sheet.
"""

import os
import maya.OpenMayaUI as omui
# pylint: disable=no-name-in-module
from mayatest.Qt import (
    QtCore,
    QtGui,
    QtWidgets,
    QtCompat,
) 
from mayatest.image_utils import compare_images

SORT_KEY = "ACTUAL"


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return QtCompat.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class CustomImageWidget(QtWidgets.QWidget):
    """
    A custom widget to display an image with a background color
    """

    def __init__(self, width, height, image_path, parent=None):
        super(CustomImageWidget, self).__init__(parent)
        self.set_size(width, height)
        self.set_image(image_path)
        self.set_background_color(QtCore.Qt.black)

    def set_size(self, width, height):
        self.setFixedSize(width, height)

    def set_image(self, image_path):
        image = QtGui.QImage(image_path)

        # Calculate scaled image size while preserving aspect ratio
        scaled_image = image.scaled(
            self.width(),
            self.height(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )

        self.pixmap = QtGui.QPixmap.fromImage(scaled_image)
        self.update()

    def set_background_color(self, color):
        self.background_color = color
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # Fill background with background_color
        painter.fillRect(0, 0, self.width(), self.height(), self.background_color)

        # Calculate centering offsets
        x_offset = (self.width() - self.pixmap.width()) // 2
        y_offset = (self.height() - self.pixmap.height()) // 2

        # Draw pixmap centered
        painter.drawPixmap(x_offset, y_offset, self.pixmap)


class ContactSheetDialog(QtWidgets.QDialog):
    # def __init__(self, parent=maya_main_window()):
    def __init__(
        self,
        image_dir,
        img_width=200,
        img_height=200,
        threshold=0.1,
        parent=maya_main_window(),
    ):

        super(ContactSheetDialog, self).__init__(parent)
        self.setWindowTitle("Contact Sheet")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.img_width = img_width
        self.img_height = img_height
        self.image_dir = image_dir
        self.threshold = threshold

        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_column_headers()
        self.load_images()

    def create_widgets(self):
        self.close_btn = QtWidgets.QPushButton("Close")

        # Create a header layout
        self.header_layout = QtWidgets.QHBoxLayout()

        # Create a scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create a widget to contain the grid layout
        self.scroll_widget = QtWidgets.QWidget()

        # Create the grid layout and set it on the scroll widget
        self.image_layout = QtWidgets.QGridLayout(self.scroll_widget)

        # Set the scroll widget as the widget for the scroll area
        self.scroll_area.setWidget(self.scroll_widget)

    def create_layout(self):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.close_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(self.header_layout)
        main_layout.addWidget(
            self.scroll_area
        )  # Add the scroll area to the main layout
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.close_btn.clicked.connect(self.close)

    def create_column_headers(self):
        # Create headers for 'Actual' and 'Expected'
        self.header_layout.addStretch()  # Add stretch before the label
        headers = ["Actual", "Expected"]
        for header in headers:
            header_label = QtWidgets.QLabel(header)
            header_label.setFixedWidth(self.img_width)  # Set fixed width
            header_label.setAlignment(QtCore.Qt.AlignCenter)

            # Add stretch to push headers to the right side
            self.header_layout.addWidget(header_label, alignment=QtCore.Qt.AlignCenter)

    def load_images(self):
        image_pairs = self.find_image_pairs(self.image_dir)
        if not image_pairs:
            label = QtWidgets.QLabel("No image pairs found in the directory")
            self.image_layout.addWidget(label, 0, 1, QtCore.Qt.AlignCenter)
            return

        row = 0
        for pair in image_pairs:
            # Create the color indicator
            color_indicator = QtWidgets.QWidget()
            color_indicator.setFixedSize(
                10, self.img_height
            )  # Set fixed size for the indicator

            # Compare images and set background color
            if len(pair) > 1:  # Ensure there are at least two images to compare
                threshold = compare_images(pair[0], pair[1])
                if threshold < self.threshold:
                    color_indicator.setStyleSheet("background-color: green;")
                else:
                    color_indicator.setStyleSheet("background-color: red;")
            else:
                color_indicator.setStyleSheet("background-color: none;")

            label = QtWidgets.QLabel(os.path.basename(pair[0]).split("_")[0])
            # Set a fixed width for the label to make it much smaller
            label.setFixedWidth(50)

            # Add the color indicator to the layout
            self.image_layout.addWidget(color_indicator, row, 0)
            self.image_layout.addWidget(label, row, 1, QtCore.Qt.AlignCenter)

            col = 2
            for image_path in pair:
                image_widget = CustomImageWidget(
                    self.img_width, self.img_height, image_path
                )
                self.image_layout.addWidget(image_widget, row, col)
                col += 1

            row += 1

        # Adjust column stretch factors to make sure the label and indicator columns stay small
        self.image_layout.setColumnStretch(0, 0)
        self.image_layout.setColumnStretch(1, 0)
        self.image_layout.setColumnStretch(2, 1)

    def find_image_pairs(self, directory):
        # Check if directory exists
        if not os.path.isdir(directory):
            print(f"Error: Directory '{directory}' does not exist.")
            return []

        image_pairs = []
        image_files = os.listdir(directory)
        image_files = [
            f for f in image_files if os.path.isfile(os.path.join(directory, f))
        ]

        # Define a function to extract the basename and check if it contains 'ACTUAL'
        def sort_key(filepath):
            basename = os.path.basename(filepath)
            return SORT_KEY not in basename, basename

        while image_files:
            file1 = image_files.pop(0)
            for file2 in image_files[:]:
                if file1.split("_")[0] == file2.split("_")[0]:
                    image_pair = [
                        os.path.join(directory, file1),
                        os.path.join(directory, file2),
                    ]
                    # Sort image_pair based on custom sort key
                    sorted_image_pair = sorted(image_pair, key=sort_key)
                    image_pairs.append(sorted_image_pair)
                    image_files.remove(file2)

        return image_pairs


if __name__ == "__main__":
    #pylint: disable=E0601
    img_width = 200
    img_height = 200
    image_dir = "Z:/sb/touchpose/scripts/touchpose/tests/assets/reference_images/draw"
    threshold = 0.01

    try:
        contact_sheet_dialog.close()  # type: ignore
        contact_sheet_dialog.deleteLater()  # type: ignore
    except ValueError:
        pass

    contact_sheet_dialog = ContactSheetDialog(
        image_dir, img_width, img_height, threshold
    )
    contact_sheet_dialog.show()
