/**
 * RMITBOT Teleop Web Application
 * Uses roslibjs to communicate with ROS2 via rosbridge
 */

// ============================================
// Configuration
// ============================================
const CONFIG = {
    defaultRobotIp: 'localhost',
    rosbridgePort: 9090,
    cameraPort: 8080,
    cameraTopic: '/camera/image_raw',
    publishRate: 50, // ms between velocity publishes
    topicName: '/cmd_vel',
    messageType: 'geometry_msgs/msg/TwistStamped',
    defaultSpeed: 0.1,
    angularSpeed: 0.5,
};

// ============================================
// Application State
// ============================================
const state = {
    ros: null,
    cmdVelPub: null,
    isConnected: false,
    isHolonomicMode: false,
    currentSpeed: CONFIG.defaultSpeed,
    angularSpeed: CONFIG.angularSpeed,
    activeCommand: null,
    publishInterval: null,
};

// ============================================
// Velocity Commands
// ============================================
function getVelocityCommand(command) {
    const speed = state.currentSpeed;
    const angular = state.angularSpeed;

    // Define commands for both modes
    const commands = {
        // Normal Mode: left/right = rotation
        normal: {
            'forward': { x: speed, y: 0, z: 0 },
            'backward': { x: -speed, y: 0, z: 0 },
            'left': { x: 0, y: 0, z: angular },
            'right': { x: 0, y: 0, z: -angular },
            'forward-left': { x: speed, y: 0, z: angular * 0.5 },
            'forward-right': { x: speed, y: 0, z: -angular * 0.5 },
            'backward-left': { x: -speed, y: 0, z: angular * 0.5 },
            'backward-right': { x: -speed, y: 0, z: -angular * 0.5 },
            'stop': { x: 0, y: 0, z: 0 },
        },
        // Holonomic Mode: left/right = strafe
        holonomic: {
            'forward': { x: speed, y: 0, z: 0 },
            'backward': { x: -speed, y: 0, z: 0 },
            'left': { x: 0, y: speed, z: 0 },
            'right': { x: 0, y: -speed, z: 0 },
            'forward-left': { x: speed * 0.707, y: speed * 0.707, z: 0 },
            'forward-right': { x: speed * 0.707, y: -speed * 0.707, z: 0 },
            'backward-left': { x: -speed * 0.707, y: speed * 0.707, z: 0 },
            'backward-right': { x: -speed * 0.707, y: -speed * 0.707, z: 0 },
            'stop': { x: 0, y: 0, z: 0 },
        }
    };

    const mode = state.isHolonomicMode ? 'holonomic' : 'normal';
    return commands[mode][command] || commands[mode]['stop'];
}

// ============================================
// ROS Connection
// ============================================
function connect() {
    const robotIp = document.getElementById('robot-ip').value || CONFIG.defaultRobotIp;
    const wsUrl = `ws://${robotIp}:${CONFIG.rosbridgePort}`;

    console.log(`Connecting to ${wsUrl}...`);
    updateConnectionStatus('connecting');

    // Create ROS connection
    state.ros = new ROSLIB.Ros({ url: wsUrl });

    state.ros.on('connection', () => {
        console.log('Connected to rosbridge!');
        state.isConnected = true;
        updateConnectionStatus('connected');

        // Create publisher
        state.cmdVelPub = new ROSLIB.Topic({
            ros: state.ros,
            name: CONFIG.topicName,
            messageType: CONFIG.messageType,
        });

        console.log(`Publishing to ${CONFIG.topicName}`);

        // Start camera stream
        startCameraStream(robotIp);
    });

    state.ros.on('error', (error) => {
        console.error('ROS connection error:', error);
        updateConnectionStatus('error');
    });

    state.ros.on('close', () => {
        console.log('Connection closed');
        state.isConnected = false;
        state.cmdVelPub = null;
        updateConnectionStatus('disconnected');
        stopPublishing();
    });
}

function disconnect() {
    if (state.ros) {
        state.ros.close();
        state.ros = null;
    }
}

function updateConnectionStatus(status) {
    const statusEl = document.getElementById('connection-status');
    const textEl = statusEl.querySelector('.status-text');

    statusEl.className = 'status ' + status;

    switch (status) {
        case 'connected':
            textEl.textContent = 'Connected';
            break;
        case 'connecting':
            textEl.textContent = 'Connecting...';
            break;
        case 'error':
            textEl.textContent = 'Error';
            break;
        default:
            textEl.textContent = 'Disconnected';
    }
}

// ============================================
// Velocity Publishing
// ============================================
function publishVelocity(command) {
    if (!state.isConnected || !state.cmdVelPub) {
        console.warn('Not connected to ROS');
        return;
    }

    const vel = getVelocityCommand(command);

    // Create TwistStamped message
    const msg = new ROSLIB.Message({
        header: {
            stamp: {
                sec: Math.floor(Date.now() / 1000),
                nanosec: (Date.now() % 1000) * 1000000,
            },
            frame_id: 'base_link',
        },
        twist: {
            linear: { x: vel.x, y: vel.y, z: 0 },
            angular: { x: 0, y: 0, z: vel.z },
        }
    });

    state.cmdVelPub.publish(msg);
}

function startPublishing(command) {
    // Immediately publish once
    publishVelocity(command);

    // Continue publishing at regular intervals
    state.activeCommand = command;
    if (state.publishInterval) {
        clearInterval(state.publishInterval);
    }
    state.publishInterval = setInterval(() => {
        if (state.activeCommand) {
            publishVelocity(state.activeCommand);
        }
    }, CONFIG.publishRate);
}

function stopPublishing() {
    if (state.publishInterval) {
        clearInterval(state.publishInterval);
        state.publishInterval = null;
    }
    state.activeCommand = null;

    // Send stop command
    if (state.isConnected) {
        publishVelocity('stop');
    }
}

// ============================================
// UI Event Handlers
// ============================================
function setupEventListeners() {
    const modal = document.getElementById('connect-modal');
    const statusEl = document.getElementById('connection-status');

    // Click status to open modal or disconnect
    statusEl.addEventListener('click', () => {
        if (state.isConnected) {
            disconnect();
        } else {
            modal.classList.add('show');
        }
    });

    // Modal cancel button
    document.getElementById('modal-cancel').addEventListener('click', () => {
        modal.classList.remove('show');
    });

    // Modal connect button
    document.getElementById('modal-connect').addEventListener('click', () => {
        modal.classList.remove('show');
        connect();
    });

    // Close modal on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });

    // Handle Enter key on IP input
    document.getElementById('robot-ip').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            modal.classList.remove('show');
            connect();
        }
    });

    // Mode toggle
    const modeSwitch = document.getElementById('mode-switch');
    modeSwitch.addEventListener('change', () => {
        state.isHolonomicMode = modeSwitch.checked;
        updateModeUI();
    });

    // Speed slider
    const speedSlider = document.getElementById('speed-slider');
    speedSlider.addEventListener('input', () => {
        state.currentSpeed = parseFloat(speedSlider.value);
        document.getElementById('speed-value').textContent = state.currentSpeed.toFixed(1);
    });

    // Angular speed slider
    const angularSlider = document.getElementById('angular-slider');
    angularSlider.addEventListener('input', () => {
        state.angularSpeed = parseFloat(angularSlider.value);
        document.getElementById('angular-value').textContent = state.angularSpeed.toFixed(1);
    });

    // Control buttons - touch and mouse events
    const buttons = document.querySelectorAll('.control-btn');
    buttons.forEach(btn => {
        const command = btn.dataset.cmd;

        // Touch events
        btn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            btn.classList.add('active');
            if (command === 'stop') {
                stopPublishing();
            } else {
                startPublishing(command);
            }
        }, { passive: false });

        btn.addEventListener('touchend', (e) => {
            e.preventDefault();
            btn.classList.remove('active');
            if (command !== 'stop') {
                stopPublishing();
            }
        });

        btn.addEventListener('touchcancel', (e) => {
            btn.classList.remove('active');
            stopPublishing();
        });

        // Mouse events (for desktop testing)
        btn.addEventListener('mousedown', (e) => {
            btn.classList.add('active');
            if (command === 'stop') {
                stopPublishing();
            } else {
                startPublishing(command);
            }
        });

        btn.addEventListener('mouseup', () => {
            btn.classList.remove('active');
            if (command !== 'stop') {
                stopPublishing();
            }
        });

        btn.addEventListener('mouseleave', () => {
            btn.classList.remove('active');
            if (state.activeCommand === command) {
                stopPublishing();
            }
        });
    });

    // Prevent context menu on long press
    document.addEventListener('contextmenu', (e) => {
        if (e.target.closest('.control-btn')) {
            e.preventDefault();
        }
    });
}

function updateModeUI() {
    const normalLabel = document.getElementById('mode-normal');
    const holoLabel = document.getElementById('mode-holonomic');
    const description = document.getElementById('mode-description');
    const leftLabel = document.getElementById('left-label');
    const rightLabel = document.getElementById('right-label');

    if (state.isHolonomicMode) {
        normalLabel.classList.remove('active');
        holoLabel.classList.add('active');
        description.textContent = 'Left/Right buttons strafe sideways';
        leftLabel.textContent = '←';
        rightLabel.textContent = '→';
    } else {
        normalLabel.classList.add('active');
        holoLabel.classList.remove('active');
        description.textContent = 'Left/Right buttons rotate the robot';
        leftLabel.textContent = '↺';
        rightLabel.textContent = '↻';
    }
}

// ============================================
// Camera Stream
// ============================================
function startCameraStream(robotIp) {
    const cameraImg = document.getElementById('camera-stream');
    const placeholder = document.getElementById('camera-placeholder');

    // web_video_server stream URL
    const streamUrl = `http://${robotIp}:${CONFIG.cameraPort}/stream?topic=${CONFIG.cameraTopic}&type=mjpeg&quality=50`;

    cameraImg.src = streamUrl;

    cameraImg.onload = () => {
        cameraImg.classList.add('active');
        console.log('Camera stream started');
    };

    cameraImg.onerror = () => {
        cameraImg.classList.remove('active');
        placeholder.textContent = 'Camera Offline';
        console.warn('Camera stream unavailable');
    };
}

function stopCameraStream() {
    const cameraImg = document.getElementById('camera-stream');
    cameraImg.src = '';
    cameraImg.classList.remove('active');
}

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('RMITBOT Teleop Web App initialized');
    setupEventListeners();
    updateModeUI();

    // Set initial speed display
    document.getElementById('speed-value').textContent = state.currentSpeed.toFixed(1);
    document.getElementById('angular-value').textContent = state.angularSpeed.toFixed(1);
});
