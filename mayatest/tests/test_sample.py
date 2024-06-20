# test_sample.py
from mayatest.mayaunittest import TestCase
import maya.cmds as mc
class SampleTests(TestCase):
    def test_create_sphere(self):
        sphere = mc.polySphere(n='mySphere')[0]
        self.assertEqual('mySphere', sphere)