"""
Contains a user interface for the CMT testing framework.

The dialog will display all tests found in MAYA_MODULE_PATH and allow the user to
selectively run the tests.  The dialog will also automatically get any code updates
without any need to reload if the dialog is opened before any other tools have been
run.

To open the dialog run the menu item: CMT > Utility > Unit Test Runner.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import sys
import traceback
import unittest
import webbrowser


from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

from mayatest.Qt import QtGui, QtWidgets, QtCore

# from mayatest.Qt.QtCore import *
# from mayatest.Qt.QtGui import *
# from mayatest.Qt.QtWidgets import *

from mayatest import mayaunittest as mayaunittest
from mayatest.mayaunittest import new_scene

from mayatest.FileLine import FileLine


logger = logging.getLogger(__name__)

ICON_DIR = os.path.join(os.path.dirname(__file__), 'icons')

_win = None


def show():
    """Shows the browser window."""
    global _win
    if _win:
        _win.close()
    _win = MayaTestRunnerDialog()
    _win.show()


def documentation():
    raise NotImplementedError


class BaseTreeNode(object):
    """Base tree node that contains hierarchical functionality for use in a
    QAbstractItemModel"""

    def __init__(self, parent=None):
        self.children = []
        self._parent = parent

        if parent is not None:
            parent.add_child(self)

    def add_child(self, child):
        """Add a child to the node.

        :param child: Child node to add."""
        if child not in self.children:
            self.children.append(child)

    def remove(self):
        """Remove this node and all its children from the tree."""
        if self._parent:
            row = self.row()
            self._parent.children.pop(row)
            self._parent = None
        for child in self.children:
            child.remove()

    def child(self, row):
        """Get the child at the specified index.

        :param row: The child index.
        :return: The tree node at the given index or None if the index was out of
        bounds.
        """
        try:
            return self.children[row]
        except IndexError:
            return None

    def child_count(self):
        """Get the number of children in the node"""
        return len(self.children)

    def parent(self):
        """Get the parent of node"""
        return self._parent

    def row(self):
        """Get the index of the node relative to the parent"""
        if self._parent is not None:
            return self._parent.children.index(self)
        return 0

    def data(self, column):
        """Get the table display data"""
        return ""


class MayaTestRunnerDialog(MayaQWidgetBaseMixin, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MayaTestRunnerDialog, self).__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Maya Unit Test Runner")
        self.resize(1000, 600)
        self.rollback_importer = RollbackImporter()

        toolbar = self.addToolBar("Tools")
        action = toolbar.addAction("Run All Tests")
        action.setIcon(
            QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_run_all_tests.png"))))
        action.triggered.connect(self.run_all_tests)
        action.setToolTip("Run all tests.")

        action = toolbar.addAction("Run Selected Tests")
        action.setIcon(
            QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_run_selected_tests.png")))
        )
        action.setToolTip("Run all selected tests.")
        action.triggered.connect(self.run_selected_tests)

        action = toolbar.addAction("Run Failed Tests")
        action.setIcon(
            QtGui.QIcon(QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_run_failed_tests.png")))
        )
        action.setToolTip("Run all failed tests.")
        action.triggered.connect(self.run_failed_tests)

        action = toolbar.addAction("Refresh Tests")
        action.setIcon(QtGui.QIcon(QtGui.QPixmap(":/refresh.png")))
        action.setToolTip("Refresh the test list all failed tests.")
        action.triggered.connect(self.refresh_tests)

        self.module_line = FileLine()
        toolbar.addWidget(QtWidgets.QLabel('Module Test Path:'))
        spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum,
                             QtWidgets.QSizePolicy.Expanding)
        toolbar.addWidget(QtWidgets.QLabel())
        toolbar.addWidget(self.module_line)

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        vbox = QtWidgets.QVBoxLayout(widget)

        # Settings
        self.new_scene_checkbox = QtWidgets.QCheckBox('New Scene Between Tests')
        self.new_scene_checkbox.setChecked(mayaunittest.Settings.file_new)
        self.new_scene_checkbox.toggled.connect(mayaunittest.set_file_new)
        self.new_scene_checkbox.setToolTip(
            "Creates a new scene file after each test.")

        self.buffer_checkbox = QtWidgets.QCheckBox('Buffer Output')
        self.buffer_checkbox.setChecked(mayaunittest.Settings.buffer_output)
        self.buffer_checkbox.toggled.connect(mayaunittest.set_buffer_output)
        self.buffer_checkbox.setToolTip(
            "Only display output during a failed test.")

        self.new_scene_btn = QtWidgets.QPushButton('New Scene')
        self.new_scene_btn.clicked.connect(new_scene)

        settings_layout = QtWidgets.QHBoxLayout()
        settings_layout.addWidget(self.buffer_checkbox)
        settings_layout.addWidget(self.new_scene_checkbox)
        settings_layout.addWidget(self.new_scene_btn)

        settings_layout.addStretch()

        splitter = QtWidgets.QSplitter(orientation=QtCore.Qt.Horizontal)
        self.test_view = QtWidgets.QTreeView()
        self.test_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        splitter.addWidget(self.test_view)
        self.output_console = QtWidgets.QTextEdit()
        self.output_console.setReadOnly(True)
        vbox.addLayout(settings_layout)
        splitter.addWidget(self.output_console)
        vbox.addWidget(splitter)
        splitter.setStretchFactor(1, 4)
        self.stream = TestCaptureStream(self.output_console)

        self.refresh_tests()
        self.init_gui()

    def refresh_tests(self):
        self.reset_rollback_importer()

        test_suite = mayaunittest.get_module_tests(
            module_root=self.module_line.path)

        root_node = TestNode(test_suite)
        self.model = TestTreeModel(root_node, self)
        self.test_view.setModel(self.model)
        self.expand_tree(root_node)

    def expand_tree(self, root_node):
        """Expands all the collapsed elements in a tree starting at the root_node"""
        parent = root_node.parent()
        parent_idx = (
            self.model.createIndex(
                parent.row(), 0, parent) if parent else QtCore.QModelIndex()
        )
        index = self.model.index(root_node.row(), 0, parent_idx)
        self.test_view.setExpanded(index, True)
        for child in root_node.children:
            self.expand_tree(child)

    def run_all_tests(self):
        """Callback method to run all the tests found in MAYA_MODULE_PATH."""
        self.reset_rollback_importer()
        test_suite = unittest.TestSuite()

        # Module test path
        print('module test path: {}'.format(self.module_line.path))

        # Get all the tests
        test_suite = mayaunittest.get_module_tests(
            module_root=self.module_line.path)

        self.output_console.clear()
        self.model.run_tests(self.stream, test_suite)

    def run_selected_tests(self):
        """Callback method to run the selected tests in the UI."""
        self.reset_rollback_importer()
        test_suite = unittest.TestSuite()

        indices = self.test_view.selectedIndexes()
        if not indices:
            return

        # Remove any child nodes if parent nodes are in the list.  This will prevent duplicate
        # tests from being run.
        paths = [index.internalPointer().path() for index in indices]
        test_paths = []
        for path in paths:
            tokens = path.split(".")
            for i in range(len(tokens) - 1):
                p = ".".join(tokens[0: i + 1])
                if p in paths:
                    break
            else:
                test_paths.append(path)

        # Now get the tests with the pruned paths
        for path in test_paths:
            mayaunittest.get_tests(test=path, test_suite=test_suite)

        self.output_console.clear()
        self.model.run_tests(self.stream, test_suite)

    def run_failed_tests(self):
        """Callback method to run all the tests with fail or error statuses."""
        self.reset_rollback_importer()
        test_suite = unittest.TestSuite()
        for node in self.model.node_lookup.values():
            if isinstance(node.test, unittest.TestCase) and node.get_status() in {
                TestStatus.fail,
                TestStatus.error,
            }:
                mayaunittest.get_tests(test=node.path(), test_suite=test_suite)
        self.output_console.clear()
        self.model.run_tests(self.stream, test_suite)

    def reset_rollback_importer(self):
        """Resets the RollbackImporter which allows the test runner to pick up code
        updates without having to reload anything."""
        if self.rollback_importer:
            self.rollback_importer.uninstall()
        # Create a new rollback importer to pick up any code updates
        self.rollback_importer = RollbackImporter()

    def init_gui(self):
        settings = QtCore.QSettings('AutodeskMaya', 'Unit Test Runner')

        try:
            self.restoreGeometry(settings.value('geometry'))
        except AttributeError:
            pass

        try:
            module_path = settings.value('module_path')
            self.module_line.path = module_path
        except Exception as e:
            print(e)

    def closeEvent(self, event):
        """Close event to clean up everything."""
        global _win
        self.rollback_importer.uninstall()
        self.deleteLater()
        _win = None

        # Save the module path and widget position
        self.settings = QtCore.QSettings("AutodeskMaya", "Unit Test Runner")
        self.settings.setValue('module_path', self.module_line.path)
        self.settings.setValue("geometry", self.saveGeometry())
        QtWidgets.QWidget.closeEvent(self, event)


class TestCaptureStream(object):
    """Allows the output of the tests to be displayed in a QTextEdit."""

    success_color = QtGui.QColor(92, 184, 92)
    fail_color = QtGui.QColor(240, 173, 78)
    error_color = QtGui.QColor(217, 83, 79)
    skip_color = QtGui.QColor(88, 165, 204)
    normal_color = QtGui.QColor(200, 200, 200)

    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        """Write text into the QTextEdit."""
        # Color the output
        if text.startswith("ok"):
            self.text_edit.setTextColor(TestCaptureStream.success_color)
        elif text.startswith("FAIL"):
            self.text_edit.setTextColor(TestCaptureStream.fail_color)
        elif text.startswith("ERROR"):
            self.text_edit.setTextColor(TestCaptureStream.error_color)
        elif text.startswith("skipped"):
            self.text_edit.setTextColor(TestCaptureStream.skip_color)

        self.text_edit.insertPlainText(text)
        self.text_edit.setTextColor(TestCaptureStream.normal_color)

    def flush(self):
        pass


class TestStatus:
    """The possible status values of a test."""

    not_run = 0
    success = 1
    fail = 2
    error = 3
    skipped = 4


class TestNode(BaseTreeNode):
    """A node representing a Test, TestCase, or TestSuite for display in a QTreeView."""

    success_icon = QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_test_success.png"))
    fail_icon = QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_test_fail.png"))
    error_icon = QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_test_error.png"))
    skip_icon = QtGui.QPixmap(os.path.join(ICON_DIR, "cmt_test_skip.png"))

    def __init__(self, test, parent=None):
        super(TestNode, self).__init__(parent)
        self.test = test
        self.tool_tip = str(test)
        self.status = TestStatus.not_run
        if isinstance(self.test, unittest.TestSuite):
            for test_ in self.test:
                if isinstance(test_, unittest.TestCase) or test_.countTestCases():
                    self.add_child(TestNode(test_, self))
        if "ModuleImportFailure" == self.test.__class__.__name__:
            try:
                getattr(self.test, self.name())()
            except ImportError:
                self.tool_tip = traceback.format_exc()
                logger.warning(self.tool_tip)

    def name(self):
        """Get the name to print in the view."""
        if isinstance(self.test, unittest.TestCase):
            return self.test._testMethodName
        elif isinstance(self.child(0).test, unittest.TestCase):
            return self.child(0).test.__class__.__name__
        else:
            return self.child(0).child(0).test.__class__.__module__

    def path(self):
        """Gets the import path of the test.  Used for finding the test by name."""
        if self.parent() and self.parent().parent():
            return "{0}.{1}".format(self.parent().path(), self.name())
        else:
            return self.name()

    def get_status(self):
        """Get the status of the TestNode.

        Nodes with children like the TestSuites, will get their status based on the
        status of the leaf nodes (the TestCases).

        :return: A status value from TestStatus.
        """
        if "ModuleImportFailure" in [self.name(), self.test.__class__.__name__]:
            return TestStatus.error
        if not self.children:
            return self.status
        result = TestStatus.not_run
        for child in self.children:
            child_status = child.get_status()
            if child_status == TestStatus.error:
                # Error status has highest priority so propagate that up to the parent
                return child_status
            elif child_status == TestStatus.fail:
                result = child_status
            elif child_status == TestStatus.success and result != TestStatus.fail:
                result = child_status
            elif child_status == TestStatus.skipped and result != TestStatus.fail:
                result = child_status
        return result

    def get_icon(self):
        """Get the status icon to display with the Test."""
        status = self.get_status()
        return [
            None,
            TestNode.success_icon,
            TestNode.fail_icon,
            TestNode.error_icon,
            TestNode.skip_icon,
        ][status]


class TestTreeModel(QtCore.QAbstractItemModel):
    """The model used to populate the test tree view."""

    def __init__(self, root, parent=None):
        super(TestTreeModel, self).__init__(parent)
        self._root_node = root
        self.node_lookup = {}
        # Create a lookup so we can find the TestNode given a TestCase or TestSuite
        self.create_node_lookup(self._root_node)

    def create_node_lookup(self, node):
        """Create a lookup so we can find the TestNode given a TestCase or TestSuite.  The lookup will be used to set
        test statuses and tool tips after a test run.

        :param node: Node to add to the map.
        """
        self.node_lookup[str(node.test)] = node
        for child in node.children:
            self.create_node_lookup(child)

    def rowCount(self, parent):
        """Return the number of rows with this parent."""
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()
        return parent_node.child_count()

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return node.name()
        elif role == QtCore.Qt.DecorationRole:
            return node.get_icon()
        elif role == QtCore.Qt.ToolTipRole:
            return node.tool_tip

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        node = index.internalPointer()

        data_changed_kwargs = [index, index, []]

        if role == QtCore.Qt.EditRole:
            self.dataChanged.emit(*data_changed_kwargs)
        if role == QtCore.Qt.DecorationRole:
            node.status = value
            self.dataChanged.emit(*data_changed_kwargs)
            if node.parent() is not self._root_node:
                self.setData(self.parent(index), value, role)
        elif role == QtCore.Qt.ToolTipRole:
            node.tool_tip = value
            self.dataChanged.emit(*data_changed_kwargs)

    def headerData(self, section, orientation, role):
        return "Tests"

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def parent(self, index):
        node = index.internalPointer()
        parent_node = node.parent()
        if parent_node == self._root_node:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()

        child_item = parent_node.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def get_index_of_node(self, node):
        if node is self._root_node:
            return QtCore.QModelIndex()
        return self.index(node.row(), 0, self.get_index_of_node(node.parent()))

    def run_tests(self, stream, test_suite):
        """Runs the given TestSuite.

        :param stream: A stream object with write functionality to capture the test output.
        :param test_suite: The TestSuite to run.
        """
        runner = unittest.TextTestRunner(
            stream=stream, verbosity=2, resultclass=mayaunittest.TestResult
        )
        runner.failfast = False
        runner.buffer = mayaunittest.Settings.buffer_output
        result = runner.run(test_suite)

        self._set_test_result_data(result.failures, TestStatus.fail)
        self._set_test_result_data(result.errors, TestStatus.error)
        self._set_test_result_data(result.skipped, TestStatus.skipped)

        for test in result.successes:
            node = self.node_lookup[str(test)]
            index = self.get_index_of_node(node)
            self.setData(index, "Test Passed", QtCore.Qt.ToolTipRole)
            self.setData(index, TestStatus.success, QtCore.Qt.DecorationRole)

    def _set_test_result_data(self, test_list, status):
        """Store the test result data in model.

        :param test_list: A list of tuples of test results.
        :param status: A TestStatus value."""
        for test, reason in test_list:
            node = self.node_lookup[str(test)]
            index = self.get_index_of_node(node)
            self.setData(index, reason, QtCore.Qt.ToolTipRole)
            self.setData(index, status, QtCore.Qt.DecorationRole)


class RollbackImporter(object):
    """Used to remove imported modules from the module list.

    This allows tests to be rerun after code updates without doing any reloads.
    Original idea from: http://pyunit.sourceforge.net/notes/reloading.html

    Usage:
    def run_tests(self):
        if self.rollback_importer:
            self.rollback_importer.uninstall()
        self.rollback_importer = RollbackImporter()
        self.load_and_execute_tests()
    """

    def __init__(self):
        """Creates an instance and installs as the global importer."""
        self.previous_modules = set(sys.modules.keys())

    # def uninstall(self):
    #     for modname in sys.modules.keys():
    #         if modname not in self.previous_modules:
    #             # Force reload when modname next imported
    #             del (sys.modules[modname])
    
    def uninstall(self):
        # Collect module names to delete
        to_delete = [modname for modname in sys.modules.keys() if modname not in self.previous_modules]

        # Delete the collected module names from sys.modules
        for modname in to_delete:
            del sys.modules[modname]