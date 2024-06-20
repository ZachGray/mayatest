"""
Utility functions for working with Maya screen setup and screenshots.

position = screen_utils.get_screen_position(f'{TEST_GEO}.f[1800]')
position = screen_utils.get_screen_position(xform=TEST_GEO)
screen_utils.screenshot(path, region=region, region_mode='center')

"""

import os
from maya import cmds as mc
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
from PIL import ImageGrab  # type: ignore

# pylint: disable=no-name-in-module
from mayatest.Qt import QtCompat, QtWidgets, QtCore, QtGui


def screenshot(path, region=None, img_format="PNG", region_mode="absolute"):
    # Check region mode and adjust region accordingly
    if region_mode == "center":
        if region is not None:
            x, y, width, height = region
            left = x - (width // 2)
            top = y - (height // 2)
            right = x + (width // 2)
            bottom = y + (height // 2)
            region = (left, top, right, bottom)
    elif region_mode == "absolute":
        pass  # No adjustment needed for absolute coordinates
    else:
        raise ValueError(f"Invalid region_mode: {region_mode}")

    # Capture the screen or specified region
    if region is None:
        image = ImageGrab.grab()
    else:
        image = ImageGrab.grab(bbox=region)

    # Save the captured region to a file
    image.save(path, img_format)
    image.close()

    # Confirm the screenshot was saved and return the path
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print(f"Screenshot saved to: {path}")
        return path
    else:
        print(f"Error saving screenshot to: {path}")


def set_maya_window_size_and_position(width=1920, height=1080, x=0, y=0):
    # Get the main Maya window
    main_window = mc.window("MayaWindow", query=True, exists=True)

    if main_window:
        # Set the size of the main Maya window
        mc.window("MayaWindow", edit=True, widthHeight=(width, height))

        # Set the position of the main Maya window
        mc.window("MayaWindow", edit=True, topLeftCorner=(x, y))
    else:
        print("Main Maya window not found.")


# Example usage:
# set_maya_window_size_and_position(1920, 1080)


def set_workspace_to_general_and_reset(workspace="General"):

    # Set the workspace to 'General'
    mc.workspaceLayoutManager(sc=workspace)

    # Reset the 'General' workspace to factory defaults
    mc.workspaceLayoutManager(reset=True)
    print(f"The '{workspace}' workspace has been reset to factory defaults.")


# Example usage:
# set_workspace_to_general_and_reset()


def get_screen_position(component_string="", xform="", world_coords=[0.0, 0.0, 0.0]):
    if component_string:
        point_ws = get_mesh_component_world_position(component_string)
    elif xform:
        if not mc.objExists(xform):
            mc.error(f"Object {xform} does not exist.")
            return
        point_ws = mc.xform(xform, q=True, ws=True, rp=True)
    else:
        point_ws = world_coords

    worldPt2 = om.MPoint(point_ws[0], point_ws[1], point_ws[2])

    view_3d = omui.M3dView().active3dView()
    viewport_position = view_3d.worldToView(worldPt2)

    # Get widget pointer
    ptr = view_3d.widget()

    # Wrap it into PySide2
    viewpane = QtCompat.wrapInstance(int(ptr), QtWidgets.QWidget)

    # Use QWidget::mapToGlobal
    screen_position = viewpane.mapToGlobal(
        QtCore.QPoint(viewport_position[0], viewpane.height() - viewport_position[1])
    )
    # print 'screen_position=', screen_position.x(), screen_position.y()

    return {
        "screen": (screen_position.x(), screen_position.y()),
        "view": (viewport_position[0], view_3d.portHeight() - viewport_position[1]),
    }

    # return viewport_position[0], view_3d.portHeight()-viewport_position[1]


def get_mesh_component_world_position(component_string):

    if not mc.objExists(component_string):
        mc.error(f"Object {component_string} does not exist.")
        return
    elif not any(x in component_string for x in ["vtx", "e", "f"]):
        mc.error(f"Object {component_string} is not a mesh component.")
        return
    elif ":" in component_string:
        mc.error("Multiple components not supported")
        return

    # Extract the index and type
    index = int(component_string.split("[")[-1].split("]")[0])
    mesh = component_string.split(".")[0]
    component_type = component_from_string(component_string)

    # Get the mesh node from the scene
    selection_list = om.MSelectionList()
    selection_list.add(mesh)
    mesh_obj = selection_list.getDependNode(0)
    mesh_path = om.MDagPath.getAPathTo(mesh_obj)
    mesh_path.extendToShape()
    mesh_fn = om.MFnMesh(mesh_path)

    # Get the mesh iterator
    if component_type == "face":
        if index >= mesh_fn.numPolygons:
            mc.error(f"Face index {index} out of range.")
            return
        mesh_iterator = om.MItMeshPolygon(mesh_path)
        mesh_iterator.setIndex(index)
        pos_world = mesh_iterator.center(om.MSpace.kWorld)
    elif component_type == "vertex":
        if index >= mesh_fn.numVertices:
            mc.error(f"Vertex index {index} out of range.")
            return
        mesh_iterator = om.MItMeshVertex(mesh_path)
        mesh_iterator.setIndex(index)
        pos_world = mesh_iterator.position(om.MSpace.kWorld)
    else:
        mc.error(f"Component type {component_type} not supported.")
        return

    return (pos_world.x, pos_world.y, pos_world.z)


def component_from_string(input_str):
    if ".f" in input_str:
        result = "face"
    elif ".e" in input_str:
        result = "edge"
    elif ".vtx" in input_str:
        result = "vertex"
    else:
        result = None

    return result
