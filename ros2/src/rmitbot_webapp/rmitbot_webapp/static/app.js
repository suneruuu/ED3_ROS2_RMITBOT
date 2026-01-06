// Robot Web Interface JavaScript
class RobotController {
    constructor() {
        this.socket = io();
        this.isJoystickMode = true;
        this.isDragging = false;
        this.joystickCenter = { x: 0, y: 0 };
        this.maxDistance = 85; // Maximum distance from center
        this.currentVelocity = { linear_x: 0, linear_y: 0, angular_z: 0 };
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupSocketEvents();
        this.startVelocityLoop();
    }

    initializeElements() {
        // Control mode elements
        this.joystickModeBtn = document.getElementById('joystick-mode');
        this.arrowModeBtn = document.getElementById('arrow-mode');
        this.joystickContainer = document.getElementById('joystick-container');
        this.arrowControls = document.getElementById('arrow-controls');
        
        // Joystick elements
        this.joystick = document.getElementById('joystick');
        this.joystickKnob = document.getElementById('joystick-knob');
        
        // Arrow control elements
        this.forwardBtn = document.getElementById('forward');
        this.backwardBtn = document.getElementById('backward');
        this.leftBtn = document.getElementById('left');
        this.rightBtn = document.getElementById('right');
        this.stopBtn = document.getElementById('stop');
        
        // Status elements
        this.cameraFeed = document.getElementById('camera-feed');
        this.cameraFps = document.getElementById('camera-fps');
        this.connectionStatus = document.getElementById('connection-status');
        
        // Position elements
        this.posX = document.getElementById('pos-x');
        this.posY = document.getElementById('pos-y');
        this.posTheta = document.getElementById('pos-theta');
        this.velLinear = document.getElementById('vel-linear');
        this.velAngular = document.getElementById('vel-angular');
    }

    setupEventListeners() {
        // Mode switching
        this.joystickModeBtn.addEventListener('click', () => this.switchMode(true));
        this.arrowModeBtn.addEventListener('click', () => this.switchMode(false));
        
        // Joystick events
        this.joystick.addEventListener('mousedown', (e) => this.startJoystickDrag(e));
        this.joystick.addEventListener('touchstart', (e) => this.startJoystickDrag(e));
        
        document.addEventListener('mousemove', (e) => this.updateJoystick(e));
        document.addEventListener('touchmove', (e) => this.updateJoystick(e));
        
        document.addEventListener('mouseup', () => this.stopJoystickDrag());
        document.addEventListener('touchend', () => this.stopJoystickDrag());
        
        // Arrow control events
        this.setupArrowControls();
        
        // Keyboard events for arrow mode
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));
    }

    setupArrowControls() {
        const controls = [
            { btn: this.forwardBtn, vel: { linear_x: 0.5, linear_y: 0, angular_z: 0 } },
            { btn: this.backwardBtn, vel: { linear_x: -0.5, linear_y: 0, angular_z: 0 } },
            { btn: this.leftBtn, vel: { linear_x: 0, linear_y: 0.5, angular_z: 0 } },
            { btn: this.rightBtn, vel: { linear_x: 0, linear_y: -0.5, angular_z: 0 } },
            { btn: this.stopBtn, vel: { linear_x: 0, linear_y: 0, angular_z: 0 } }
        ];

        controls.forEach(({ btn, vel }) => {
            btn.addEventListener('mousedown', () => this.setVelocity(vel));
            btn.addEventListener('touchstart', () => this.setVelocity(vel));
            btn.addEventListener('mouseup', () => this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 }));
            btn.addEventListener('touchend', () => this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 }));
        });
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to robot');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from robot');
            this.updateConnectionStatus(false);
        });

        this.socket.on('camera_frame', (data) => {
            this.cameraFeed.src = data.image;
            this.cameraFps.textContent = data.fps;
        });

        this.socket.on('robot_status', (data) => {
            this.updateRobotStatus(data);
        });
    }

    switchMode(isJoystick) {
        this.isJoystickMode = isJoystick;
        
        if (isJoystick) {
            this.joystickModeBtn.classList.add('active');
            this.arrowModeBtn.classList.remove('active');
            this.joystickContainer.style.display = 'flex';
            this.arrowControls.classList.remove('active');
        } else {
            this.arrowModeBtn.classList.add('active');
            this.joystickModeBtn.classList.remove('active');
            this.joystickContainer.style.display = 'none';
            this.arrowControls.classList.add('active');
        }
        
        // Stop any current movement
        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
    }

    startJoystickDrag(e) {
        if (!this.isJoystickMode) return;
        
        this.isDragging = true;
        const rect = this.joystick.getBoundingClientRect();
        this.joystickCenter = {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
        
        e.preventDefault();
    }

    updateJoystick(e) {
        if (!this.isDragging || !this.isJoystickMode) return;
        
        const clientX = e.clientX || (e.touches && e.touches[0].clientX);
        const clientY = e.clientY || (e.touches && e.touches[0].clientY);
        
        if (!clientX || !clientY) return;
        
        const deltaX = clientX - this.joystickCenter.x;
        const deltaY = clientY - this.joystickCenter.y;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        let knobX = deltaX;
        let knobY = deltaY;
        
        if (distance > this.maxDistance) {
            knobX = (deltaX / distance) * this.maxDistance;
            knobY = (deltaY / distance) * this.maxDistance;
        }
        
        // Update knob position
        this.joystickKnob.style.transform = `translate(${knobX - 30}px, ${knobY - 30}px)`;
        
        // Calculate velocities (normalize to -1 to 1 range)
        const normalizedX = knobX / this.maxDistance;
        const normalizedY = -knobY / this.maxDistance; // Invert Y axis
        
        // Map to robot velocities
        const maxLinearVel = 0.5; // m/s
        const maxAngularVel = 1.0; // rad/s
        
        this.setVelocity({
            linear_x: normalizedY * maxLinearVel,
            linear_y: normalizedX * maxLinearVel,
            angular_z: -normalizedX * maxAngularVel * 0.5 // Reduced angular velocity
        });
    }

    stopJoystickDrag() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        // Return knob to center
        this.joystickKnob.style.transform = 'translate(-30px, -30px)';
        
        // Stop robot
        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
    }

    handleKeyDown(e) {
        if (this.isJoystickMode) return;
        
        const maxVel = 0.5;
        
        switch(e.key) {
            case 'ArrowUp':
            case 'w':
                this.setVelocity({ linear_x: maxVel, linear_y: 0, angular_z: 0 });
                break;
            case 'ArrowDown':
            case 's':
                this.setVelocity({ linear_x: -maxVel, linear_y: 0, angular_z: 0 });
                break;
            case 'ArrowLeft':
            case 'a':
                this.setVelocity({ linear_x: 0, linear_y: maxVel, angular_z: 0 });
                break;
            case 'ArrowRight':
            case 'd':
                this.setVelocity({ linear_x: 0, linear_y: -maxVel, angular_z: 0 });
                break;
            case ' ':
                this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                break;
        }
        e.preventDefault();
    }

    handleKeyUp(e) {
        if (this.isJoystickMode) return;
        
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a', 's', 'd'].includes(e.key)) {
            this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
        }
    }

    setVelocity(velocity) {
        this.currentVelocity = velocity;
    }

    startVelocityLoop() {
        setInterval(() => {
            this.socket.emit('cmd_vel', this.currentVelocity);
        }, 100); // Send commands at 10Hz
    }

    updateConnectionStatus(connected) {
        if (connected) {
            this.connectionStatus.textContent = 'Connected';
            this.connectionStatus.className = 'connection-status connected';
        } else {
            this.connectionStatus.textContent = 'Disconnected';
            this.connectionStatus.className = 'connection-status disconnected';
        }
    }

    updateRobotStatus(data) {
        if (data.pose) {
            this.posX.textContent = data.pose.x.toFixed(2);
            this.posY.textContent = data.pose.y.toFixed(2);
            this.posTheta.textContent = data.pose.theta.toFixed(2);
        }
        
        if (data.velocity) {
            this.velLinear.textContent = data.velocity.linear.toFixed(2);
            this.velAngular.textContent = data.velocity.angular.toFixed(2);
        }
    }
}

// Initialize the robot controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new RobotController();
});
