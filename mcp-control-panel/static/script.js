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
