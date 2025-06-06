import threading
import subprocess
import sys
import os

def run_flask_server():
    """Run the Flask server from reference.py"""
    subprocess.run([sys.executable, "reference.py"])

def run_sheila():
    """Run Sheila's voice assistant from server.py"""
    subprocess.run([sys.executable, "server.py"])

if __name__ == "__main__":
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Sheila in the main thread
    run_sheila() 