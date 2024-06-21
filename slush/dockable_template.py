from shiboken6 import wrapInstance
from builtins import int
import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide6 import QtWidgets

WORKSPACE_CTRL_NAME = 'MyDockableWidgetWorkspaceControl'
WIDGET_OBJECT_NAME = 'MyDockableWidget'

class MyDockableWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MyDockableWidget, self).__init__(parent=parent)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
        # Create a basic layout
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        
        # Add a button to the layout
        button = QtWidgets.QPushButton("Close Window")
        layout.addWidget(button)
        
        # Connect the button to the close function
        button.clicked.connect(self.close_window)
        
    def close_window(self):
        cmds.warning("Button clicked!")
        
        deleteInstances()

        # Close the workspace control
        #if cmds.workspaceControl(WORKSPACE_CTRL_NAME, exists=True):
        #    cmds.deleteUI(WORKSPACE_CTRL_NAME)

def deleteInstances():
    for ctrlName in [WIDGET_OBJECT_NAME, WORKSPACE_CTRL_NAME]:
        ctrl = OpenMayaUI.MQtUtil.findControl(ctrlName)
        if ctrl:
            widget = wrapInstance(int(ctrl), QtWidgets.QWidget)
            widget.close()
    try:
        cmds.deleteUI(WORKSPACE_CTRL_NAME)
    except:
        pass

def show():
    deleteInstances()
    global _DOCKWIDGET
    _DOCKWIDGET = MyDockableWidget()
    _DOCKWIDGET.setObjectName(WIDGET_OBJECT_NAME)
    _DOCKWIDGET.show(dockable=False, dup=False)

    # this auto docks the widget
    # cmds.workspaceControl(WORKSPACE_CTRL_NAME, e=True, dockToMainWindow=["right", 1], wp="preferred", retain=False)

# Call this function to create and show the dockable widget
show()