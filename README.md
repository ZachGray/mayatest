## Maya Unit Test

### 2024 update
Requires pillow/PIL

- Added additional functionality for image capture in maya using PIL  
- Added a contact sheet utility for displaying comparison images
- Added image comparision utility using PIL
- Added various utilities for determining screen location in maya.

Use this decorator for any tests that require the UI 
```python
@unittest.skipUnless(om.MGlobal.mayaState() == 0, "Not running in Maya")
    def test_example(self):
        pass
```


### Vendored
> https://github.com/abstractfactory/maya-capture
Bundled a slightly modified version of capture.py to support plugin shapes
https://github.com/mottosso/Qt.py/blob/master/Qt.py
Bundled a slightly modified Qt.py  
These should eventually be decoupled and installed in pipe instead of being vendored.


Original work by [Chad Vernon](https://github.com/chadmv) as part of his CMT toolset: https://github.com/chadmv/cmt

Python unit testing inside of Autodesk Maya. Unit testing is a good thing. This tool makes it easier to test your VFX and game tools inside of Autodesk Maya. This tool could also be modified to run in Nuke to unit test python scripts in that DCC package.

![GUI](https://github.com/bhowiebkr/mayatest/blob/master/gui.PNG)

This one has just the unit testing part and works on regular python modules loaded into Maya.

