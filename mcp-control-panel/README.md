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
