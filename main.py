import subprocess
import os
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to virtual environment's activate script
venv_activate_script = CURRENT_DIR+'/venv/bin/activate'  

# Command to run within the virtual environment
script_command = f'{CURRENT_DIR}/venv/bin/pyhton3 {CURRENT_DIR}/Game.py' # start server/ Game.py file 
script_command2 = f'{CURRENT_DIR}/venv/bin/python3 {CURRENT_DIR}/GUI.py' # start GUI
script_command3 = f'{CURRENT_DIR}/venv/bin/python3 {CURRENT_DIR}/vision.py' # Load up cameras

# Build the command to activate the virtual environment and run the script
activate_cmd = f'source {venv_activate_script} && {script_command}'
activate_cmd2 = f'source {venv_activate_script} && {script_command2}'
activate_cmd3 = f'{script_command3}'
# Open a new terminal and run the command
try:
    osascript_cmd = f"osascript -e 'tell application \"Terminal\" to do script \"{activate_cmd}\"'"
    osascript_cmd2 = f"osascript -e 'tell application \"Terminal\" to do script \"{activate_cmd2}\"'"
    osascript_cmd3 = f"osascript -e 'tell application \"Terminal\" to do script \"{activate_cmd3}\"'"
    subprocess.run(osascript_cmd, shell=True, check=True)
    time.sleep(1)
    subprocess.run(osascript_cmd2, shell=True, check=True)
    time.sleep(1)
    subprocess.run(osascript_cmd3, shell=True, check=True)
    

except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
