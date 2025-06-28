import subprocess
import threading
import queue
import time
from flask import Flask, render_template, jsonify, request

# --- Configuration ---
# You can change these settings
SERVER_JAR_FILE = 'server.jar'
INITIAL_MEMORY_MB = 1024
MAX_MEMORY_MB = 2048
FLASK_PORT = 5000

# --- Global State ---
# These variables hold the state of the application
server_process = None
console_output_queue = queue.Queue()

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_change_me'


# --- Server Management Logic ---

def read_server_output(pipe):
    """
    Reads output from the server process's pipe (stdout) line by line
    and puts it into a thread-safe queue.
    This function is meant to be run in a separate thread.
    """
    try:
        # Use iter to read line by line. This blocks until a new line is available.
        for line in iter(pipe.readline, ''):
            # We strip newline characters and decode from bytes to string
            console_output_queue.put(line.strip())
    finally:
        pipe.close()


@app.route('/api/start', methods=['POST'])
def start_server():
    """
    API endpoint to start the Minecraft server.
    It runs the java command in a separate process and starts a thread to read its output.
    """
    global server_process
    if server_process and server_process.poll() is None:
        return jsonify({'status': 'error', 'message': 'Server is already running.'}), 400

    try:
        # Construct the command to run the Minecraft server
        java_command = [
            'java',
            f'-Xms{INITIAL_MEMORY_MB}M',
            f'-Xmx{MAX_MEMORY_MB}M',
            '-jar',
            SERVER_JAR_FILE,
            'nogui'
        ]
        
        # Start the server process.
        # stdout and stdin are piped so we can interact with the server.
        # stderr is redirected to stdout to capture all console output.
        # We use a Popen object to manage the subprocess in a non-blocking way.
        app.logger.info(f"Starting server with command: {' '.join(java_command)}")
        server_process = subprocess.Popen(
            java_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )

        # Start a new thread to read the server's console output
        # This prevents the main Flask thread from blocking while waiting for output.
        output_thread = threading.Thread(target=read_server_output, args=(server_process.stdout,))
        output_thread.daemon = True
        output_thread.start()

        return jsonify({'status': 'success', 'message': 'Server starting...'})
    except FileNotFoundError:
        app.logger.error("server.jar not found!")
        return jsonify({'status': 'error', 'message': f'{SERVER_JAR_FILE} not found. Please place it in the root directory.'}), 500
    except Exception as e:
        app.logger.error(f"Failed to start server: {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500


@app.route('/api/stop', methods=['POST'])
def stop_server():
    """
    API endpoint to stop the Minecraft server gracefully by sending the 'stop' command.
    """
    global server_process
    if not server_process or server_process.poll() is not None:
        return jsonify({'status': 'error', 'message': 'Server is not running.'}), 400

    try:
        # Send the 'stop' command to the server's standard input
        app.logger.info("Sending 'stop' command to server.")
        server_process.stdin.write('stop\n')
        server_process.stdin.flush()
        
        # Wait for the process to terminate
        server_process.wait(timeout=30)

        return jsonify({'status': 'success', 'message': 'Server stopping...'})
    except subprocess.TimeoutExpired:
        app.logger.warning("Server did not stop gracefully in time. Killing process.")
        server_process.kill()
        return jsonify({'status': 'error', 'message': 'Server did not respond to stop command. Process was killed.'}), 500
    except Exception as e:
        app.logger.error(f"Error stopping server: {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500
    finally:
        server_process = None


@app.route('/api/command', methods=['POST'])
def send_command():
    """
    API endpoint to send a custom command to the running server.
    """
    if not server_process or server_process.poll() is not None:
        return jsonify({'status': 'error', 'message': 'Server is not running.'}), 400

    command = request.json.get('command')
    if not command:
        return jsonify({'status': 'error', 'message': 'Command cannot be empty.'}), 400

    try:
        # Write the command to the server's stdin
        app.logger.info(f"Sending command to server: {command}")
        server_process.stdin.write(command + '\n')
        server_process.stdin.flush()
        return jsonify({'status': 'success', 'message': 'Command sent.'})
    except Exception as e:
        app.logger.error(f"Failed to send command: {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500


@app.route('/api/status')
def get_status():
    """
    API endpoint to get the current status of the server (Online/Offline).
    """
    if server_process and server_process.poll() is None:
        status = 'Online'
    else:
        status = 'Offline'
    return jsonify({'status': status})


@app.route('/api/console')
def get_console_output():
    """
    API endpoint to retrieve console output from the queue.
    This is used by the frontend for long-polling.
    """
    lines = []
    try:
        # Get all currently available lines from the queue without blocking
        while not console_output_queue.empty():
            lines.append(console_output_queue.get_nowait())
    except queue.Empty:
        pass
    return jsonify({'lines': lines})


# --- Frontend Route ---

@app.route('/')
def index():
    """
    Serves the main HTML page for the control panel.
    """
    return render_template('index.html')


# --- Main Execution ---

if __name__ == '__main__':
    print("=====================================================")
    print("  MCP Web Control Panel")
    print(f"  Access at: http://127.0.0.1:{FLASK_PORT}")
    print("=====================================================")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)
