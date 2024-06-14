import os
import sys
from importlib import reload

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

def append_to_path(env_var_name, new_paths):
    """
    Add a list of paths to an environment variable, ensuring no duplicates.
    
    Parameters:
    env_var_name (str): The name of the environment variable to modify.
    new_paths (list): A list of paths to add to the environment variable.
    """
    # Retrieve the current value of the environment variable
    env_var_value = os.environ.get(env_var_name, '')

    # Split the current value into a list of paths
    path_list = env_var_value.split(';') if env_var_value else []

    # Add each new path to the list if it doesn't already exist
    for new_path in new_paths:
        if new_path not in path_list:
            path_list.append(new_path)

    # Join the list back into a single string
    updated_env_var_value = ';'.join(path_list)

    # Update the environment variable
    os.environ[env_var_name] = updated_env_var_value

    # Print the result for verification
    print(f"{env_var_name} = {os.environ[env_var_name]}")


append_to_path('MAYA_MODULE_PATH', tests)

import mayatest.mayaunittestui as mayaunittestui

if __name__ == "__main__":
    mayaunittestui.show()
