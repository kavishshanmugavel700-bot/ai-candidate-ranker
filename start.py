import subprocess
import os
import sys

# Start Flask backend on port 5000 in the background
print("Starting Flask API backend...")
backend = subprocess.Popen([sys.executable, "-m", "backend.api"])

# Change directory to ui and start the Node server in the foreground
print("Starting Express UI Server...")
os.chdir("ui")
subprocess.run(["npm", "start"])
