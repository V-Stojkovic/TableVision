import subprocess
import os
import time

# Path to your virtual environment's activate script
venv_activate_script = '/Users/vukstojkovic/documents/Project/venv/bin/activate'  # 

# Command to run within the virtual environment
script_command = '/opt/homebrew/bin/python3 /Users/vukstojkovic/Documents/Project/Scripts/v1/Game.py' # start server/ Game.py file 
script_command2 = '/opt/homebrew/bin/python3 /Users/vukstojkovic/Documents/Project/Scripts/v1/GUI.py' # start GUI
script_command3 = '/opt/homebrew/bin/python3 /Users/vukstojkovic/Documents/Project/Scripts/v1/vision.py' # Load up cameras

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
