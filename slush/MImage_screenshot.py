import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint
import time

# Get the main Maya window as a Qt object
main_window_ptr = omui.MQtUtil.mainWindow()
main_window = wrapInstance(int(main_window_ptr), QApplication)

# Get the Maya viewport widget as a QWidget
viewport_widget_ptr = omui.M3dView.active3dView().widget()
viewport_widget = wrapInstance(int(viewport_widget_ptr), QWidget)

start_pos = QPoint(500, 300)
end_pos = QPoint(500, 400)
def moveA():
    QTest.mouseMove(viewport_widget, start_pos)
    time.sleep(.5)

def moveB():   
    QTest.mouseMove(viewport_widget, end_pos)
    time.sleep(.5)
    
import maya.utils
maya.utils.executeInMainThreadWithResult(moveA)
mc.refresh(force=True)
maya.utils.executeInMainThreadWithResult(moveB)

import maya.api.OpenMaya as om

# Define your idle event callback function
def myIdleCallbackStart(clientData):
    print("Maya is idle start.")
    # Perform any other tasks you want to execute during idle time
    # Re-schedule the callback if needed
    om.MMessage.removeCallback(idleCallbackIdStart)

# Define your idle event callback function
def myIdleCallbackEnd(clientData):
    print("Maya is idle end.")
    # Perform any other tasks you want to execute during idle time
    # Re-schedule the callback if needed
    om.MMessage.removeCallback(idleCallbackIdEnd)

# Add the idle event callback
idleCallbackIdStart = om.MEventMessage.addEventCallback("idle", myIdleCallbackStart)
idleCallbackIdEnd = om.MEventMessage.addEventCallback("idle", myIdleCallbackEnd)


# Simulate a left mouse button click at the specified position
QTest.mouseClick(viewport_widget, Qt.LeftButton, Qt.NoModifier, start_pos)


# Move the mouse cursor to the start position
QTest.mouseMove(viewport_widget, start_pos)

# Simulate left mouse button press
QTest.mousePress(viewport_widget, Qt.LeftButton, Qt.NoModifier, start_pos)

# Simulate marquee drag
QTest.mouseMove(viewport_widget, end_pos)

# Simulate left mouse button release
QTest.mouseRelease(viewport_widget, Qt.LeftButton, Qt.NoModifier, end_pos)







# NOTE big struggle here, trying to work around blocking maya drawing updates
# take_screenshot(path, position, 'hover', size)

# print('taking native screenshot')
# image = om.MImage()
# image.create(1920, 1080)

# view = omUI.M3dView.active3dView()
# view.pushViewport(0, 0, view.portWidth(), view.portHeight())


# view.readColorBuffer(image, True)
# target = omr.MRenderTargetManager.acquireRenderTarget()
# target.releaseRenderTarget()

# view.popViewport()

# image.writeToFile(path, outputFormat='png')