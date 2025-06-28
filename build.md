MCP Control Panel: Technical Build Plan & README
This document provides a step-by-step technical guide with the necessary file structure and initial code to create a functional Minecraft Server Control Panel.

1. Project Setup & README
First, we will define the project's directory structure and create a comprehensive README.md file that explains the project to end-users.

1.1. Directory Structure
Create the following folder and file structure for your project. You will need to provide your own server.jar file.

mcp-control-panel/
├── static/
│   └── script.js
├── templates/
│   └── index.html
├── app.py
├── server.jar  <-- (User provides this file)
└── README.md

1.2. README.md
Create a file named README.md in the root of your project directory (mcp-control-panel/) and paste the following content into it. This file is for the end-user.

# MCP Web Control Panel

A simple, lightweight web-based control panel for managing a local Minecraft server. This tool is designed for users who want to run a server without having to use the command line for basic operations.

## Features

* **Server Status:** See at a glance whether your server is `Online` or `Offline`.
* **Simple Controls:** Start, Stop, and Restart your server with the click of a button.
* **Live Console:** View the real-time server console output directly in your browser.
* **Command Execution:** Send commands to your server directly from the web interface.

## System Requirements

* A computer running Windows, macOS, or Linux.
* **Python 3.8+**: This application runs on Python.
* **Java**: Required to run the Minecraft server itself. You can download it from the official Java website.
* **Minecraft Server JAR**: You must have a `server.jar` file. You can download this from the official [Minecraft website](https://www.minecraft.net/en-us/download/server) or use server software like Spigot or Paper.

## Setup Instructions

**Step 1: Prepare the Project Folder**

1.  Place the entire `mcp-control-panel` project folder somewhere on your computer.
2.  Download your desired Minecraft `server.jar` file and place it inside the `mcp-control-panel` folder.

**Step 2: Initial Server Run & EULA Agreement**

The first time you run a Minecraft server, you must agree to the End User License Agreement (EULA).

1.  Open a terminal or command prompt in the `mcp-control-panel` directory.
2.  Run the server manually for the first time with this command (adjust memory as needed):
    ```bash
    java -Xmx1024M -Xms1024M -jar server.jar nogui
    ```
3.  The server will start and then quickly stop, creating a new file called `eula.txt`.
4.  Open `eula.txt` with a text editor and change `eula=false` to `eula=true`. Save and close the file.

**Step 3: Install Dependencies**

This application requires the Flask library for Python.

1.  Open a terminal or command prompt in the `mcp-control-panel` directory.
2.  Install Flask using pip:
    ```bash
    pip install Flask
    ```

**Step 4: Run the Control Panel**

1.  In your terminal (still in the `mcp-control-panel` directory), run the application:
    ```bash
    python app.py
    ```
2.  You will see output indicating that a server is running, usually on `http://127.0.0.1:5000`.

**Step 5: Access the Control Panel**

1.  Open your web browser (like Chrome, Firefox, or Edge).
2.  Navigate to the address: **http://127.0.0.1:5000**
3.  You should now see the MCP Web Control Panel and can use it to start and manage your server.

## Security Warning

This application is designed for **local network use only**. It has no authentication system. Do not expose this application to the public internet unless you know how to secure it properly (e.g., using a reverse proxy with authentication, firewall rules, etc.).

2. Backend Development (Python & Flask)
This section contains the complete starting code for the Flask backend which will manage the server process.

File: app.py
Create a file named app.py in the root of the project directory and paste the following Python code into it. This code sets up the web server and the logic for interacting with the Minecraft server process.

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
            errors='replace', # Handles potential encoding errors
            bufsize=1 # Line-buffered
        )

        # Start a new thread to read the server's console output
        # This prevents the main Flask thread from blocking while waiting for output.
        output_thread = threading.Thread(target=read_server_output, args=(server_process.stdout,))
        output_thread.daemon = True  # Allows the main program to exit even if this thread is running
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
        server_process.wait(timeout=30) # Wait up to 30 seconds

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
        pass  # This is expected if the queue is empty
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

3. Frontend Development (HTML & JavaScript)
This section contains the code for the web interface that users will interact with.

File: templates/index.html
Create this file inside the templates folder. This is the main UI of the control panel.

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Control Panel</title>
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom scrollbar for a cleaner look in the console */
        #console-output::-webkit-scrollbar {
            width: 8px;
        }
        #console-output::-webkit-scrollbar-track {
            background: #2d3748; /* gray-800 */
        }
        #console-output::-webkit-scrollbar-thumb {
            background-color: #4a5568; /* gray-600 */
            border-radius: 4px;
        }
        /* Style for the blinking cursor in the console */
        .console-cursor {
            display: inline-block;
            width: 10px;
            height: 1.2em;
            background-color: #f7fafc; /* gray-100 */
            animation: blink 1s step-end infinite;
        }
        @keyframes blink {
            from, to { background-color: transparent; }
            50% { background-color: #f7fafc; /* gray-100 */ }
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 font-sans">
    <div class="container mx-auto p-4 md:p-8">

        <!-- Header -->
        <header class="flex justify-between items-center mb-6 pb-4 border-b border-gray-700">
            <h1 class="text-3xl font-bold text-white">MCP Control Panel</h1>
            <div class="flex items-center space-x-3">
                <span id="status-indicator" class="h-4 w-4 rounded-full bg-red-500 animate-pulse"></span>
                <span id="status-text" class="font-semibold text-lg">Offline</span>
            </div>
        </header>

        <!-- Main Content -->
        <main class="grid grid-cols-1 md:grid-cols-3 gap-6">

            <!-- Left Column: Controls -->
            <div class="md:col-span-1 bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 class="text-2xl font-semibold mb-4">Server Controls</h2>
                <div class="space-y-3">
                    <button id="start-button" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition duration-300 flex items-center justify-center space-x-2">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span>Start Server</span>
                    </button>
                    <button id="stop-button" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-lg transition duration-300 flex items-center justify-center space-x-2" disabled>
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span>Stop Server</span>
                    </button>
                    <!-- Restart button can be added here later -->
                </div>
            </div>

            <!-- Right Column: Console -->
            <div class="md:col-span-2 bg-gray-800 p-1 rounded-lg shadow-lg">
                <div class="bg-black bg-opacity-50 p-4 rounded-lg h-96 flex flex-col">
                    <h2 class="text-2xl font-semibold mb-4 text-gray-300">Live Console</h2>
                    <div id="console-output" class="flex-grow bg-gray-900 p-4 rounded-md overflow-y-auto font-mono text-sm text-gray-200" style="white-space: pre-wrap;">
                        <!-- Console output will be injected here -->
                    </div>
                    <div class="mt-4 flex">
                        <span class="bg-gray-700 text-gray-400 p-2 rounded-l-md select-none">&gt;</span>
                        <input type="text" id="command-input" class="flex-grow bg-gray-700 p-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter a command and press Enter...">
                        <button id="send-command-button" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r-md transition duration-300">Send</button>
                    </div>
                </div>
            </div>
        </main>
        
        <!-- Toast Notification Area -->
        <div id="toast-container" class="fixed bottom-5 right-5 z-50"></div>

    </div>

    <!-- JavaScript file -->
    <script src="/static/script.js"></script>
</body>
</html>

File: static/script.js
Create this file inside the static folder. This script handles all the frontend logic, such as button clicks and communication with the backend API.

document.addEventListener('DOMContentLoaded', () => {
    // Element References
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const sendCommandButton = document.getElementById('send-command-button');
    const commandInput = document.getElementById('command-input');
    const consoleOutput = document.getElementById('console-output');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const toastContainer = document.getElementById('toast-container');

    // --- State Management ---
    let isServerOnline = false;

    // --- UI Update Functions ---

    /**
     * Updates the UI elements based on the server's online/offline status.
     * @param {boolean} isOnline - True if the server is online, false otherwise.
     */
    function updateUI(isOnline) {
        isServerOnline = isOnline;
        if (isOnline) {
            statusText.textContent = 'Online';
            statusIndicator.classList.remove('bg-red-500', 'animate-pulse');
            statusIndicator.classList.add('bg-green-500');
            startButton.disabled = true;
            stopButton.disabled = false;
            commandInput.disabled = false;
        } else {
            statusText.textContent = 'Offline';
            statusIndicator.classList.remove('bg-green-500');
            statusIndicator.classList.add('bg-red-500', 'animate-pulse');
            startButton.disabled = false;
            stopButton.disabled = true;
            commandInput.disabled = true;
        }
    }

    /**
     * Appends a new line of text to the console output and scrolls to the bottom.
     * @param {string} text - The text to add to the console.
     */
    function appendToConsole(text) {
        consoleOutput.innerHTML += text + '\n';
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
    
    /**
     * Creates and displays a toast notification.
     * @param {string} message - The message to display.
     * @param {string} type - 'success', 'error', or 'info'.
     */
    function showToast(message, type = 'info') {
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
        };
        const toast = document.createElement('div');
        toast.className = `p-4 rounded-lg text-white shadow-lg mb-2 ${colors[type]}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 4000);
    }


    // --- API Communication ---

    /**
     * A generic function to make fetch requests to the backend API.
     * @param {string} url - The API endpoint URL.
     * @param {object} options - The options for the fetch request (e.g., method, headers, body).
     */
    async function apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${error.message}`);
            showToast(error.message, 'error');
            return null; // Return null on failure
        }
    }

    async function handleStartServer() {
        showToast('Sending start command...', 'info');
        const data = await apiRequest('/api/start', { method: 'POST' });
        if (data) {
            showToast(data.message, data.status);
        }
    }

    async function handleStopServer() {
        showToast('Sending stop command...', 'info');
        const data = await apiRequest('/api/stop', { method: 'POST' });
        if (data) {
            showToast(data.message, data.status);
        }
    }

    async function handleSendCommand() {
        const command = commandInput.value.trim();
        if (command) {
            appendToConsole(`> ${command}`); // Echo command to console immediately
            commandInput.value = '';
            const data = await apiRequest('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command }),
            });
            // Don't show a toast for every command, it's too noisy.
            // A success/error is logged to the server console anyway.
        }
    }
    
    // --- Polling for Updates ---

    /**
     * Fetches the server status and updates the UI.
     */
    async function pollStatus() {
        const data = await apiRequest('/api/status');
        if (data) {
            updateUI(data.status === 'Online');
        }
    }

    /**
     * Fetches new console output and appends it to the console view.
     */
    async function pollConsole() {
        if (!isServerOnline) return; // Don't poll console if server is offline
        const data = await apiRequest('/api/console');
        if (data && data.lines && data.lines.length > 0) {
            data.lines.forEach(line => appendToConsole(line));
        }
    }

    // --- Event Listeners ---
    startButton.addEventListener('click', handleStartServer);
    stopButton.addEventListener('click', handleStopServer);
    sendCommandButton.addEventListener('click', handleSendCommand);
    commandInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            handleSendCommand();
        }
    });

    // --- Initialization ---
    function initialize() {
        appendToConsole('Welcome to the MCP Control Panel.');
        appendToConsole('Checking server status...');
        
        // Initial status check
        pollStatus();
        
        // Start polling for status and console updates at regular intervals
        setInterval(pollStatus, 3000); // Check status every 3 seconds
        setInterval(pollConsole, 1000); // Check for console output every 1 second
    }

    initialize();
});

4. How to Run the Application
Follow the instructions in the README.md file (Section 1.2 of this document) to set up and run the control panel. In summary:

Place your server.jar file in the project folder.

Run the server once manually (java -jar server.jar) to generate and accept the EULA (eula.txt).

Install Flask: pip install Flask.

Run the control panel backend: python app.py.

Open a web browser and go to http://127.0.0.1:5000.

You now have a working foundation for the control panel.
