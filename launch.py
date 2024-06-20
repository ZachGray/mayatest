""" 
Quick bootstrap to launch mayatest
update REPO to the base path of the repo
"""

import os
import sys

REPO = "Z:/sb"
MAYATEST = 'mayatest'


envs = [
    os.path.join(REPO, MAYATEST),
]

tests = [
    os.path.join(REPO, MAYATEST),
    os.path.join(REPO, 'touchpose', 'touchpose', 'tests'),
]

print("Appending env")
for env in envs:
    if env not in sys.path:
        print(f"Appending {env}")
        sys.path.append(os.path.expanduser(env))
    else:
        print(f"Already in path: {env}")



import mayatest.mayaunittestui as mayaunittestui

if __name__ == "__main__":
    mayaunittestui.show()
