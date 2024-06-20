import unittest
import maya.cmds as mc
from mayatest.image_utils import get_mesh_component_world_position
from mayatest.image_utils import component_from_string

class TestMeshComponentPosition(unittest.TestCase):
    def setUp(self):
        # Create a polygon cube for testing
        mc.polyCube(name="testCube")
        self.mesh_name = "testCube"

    def tearDown(self):
        # Delete the test cube
        mc.delete(self.mesh_name)

    def test_component_from_string(self):
        self.assertEqual(component_from_string(f"pCube.f[0]"), "face")
        self.assertEqual(component_from_string("pCube.vtx[3]"), "vertex")
        self.assertEqual(component_from_string("pCube.e[1]"), "edge")
        self.assertIsNone(component_from_string("pCube.invalid[0]"))

    def test_get_mesh_component_world_position(self):
        # Test face position
        face_pos = get_mesh_component_world_position(f"{self.mesh_name}.f[0]")
        self.assertAlmostEqual(face_pos[0], .0)
        self.assertAlmostEqual(face_pos[1], .0)
        self.assertAlmostEqual(face_pos[2], 0.5)

        # Test vertex position
        vertex_pos = get_mesh_component_world_position(f"{self.mesh_name}.vtx[3]")
        self.assertAlmostEqual(vertex_pos[0], 0.5)
        self.assertAlmostEqual(vertex_pos[1], 0.5)
        self.assertAlmostEqual(vertex_pos[2], 0.5)

        # Test invalid component
        with self.assertRaises(RuntimeError):
            get_mesh_component_world_position(f"{self.mesh_name}.invalid[0]")

        # Test out-of-range index
        with self.assertRaises(RuntimeError):
            get_mesh_component_world_position(f"{self.mesh_name}.f[100]")

if __name__ == "__main__":
    unittest.main()