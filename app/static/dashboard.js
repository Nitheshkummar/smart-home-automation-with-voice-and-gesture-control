        const state = {
            isListening: false,
            gestureMode: false,
            appliances: {
                fan: false,
                light: false,
                ac: false
            },
            environmental: {
                temperature: 32.3,
                humidity: 72
            }
        };

        const buttons = {
            fan: document.getElementById('fanBtn'),
            light: document.getElementById('lightBtn'),
            ac: document.getElementById('acBtn'),
        };

        // DOM elements
        const voiceControlBtn = document.getElementById('voiceControlBtn');
        const gestureControlBtn = document.getElementById('gestureControlBtn');
        const temperatureValue = document.getElementById('temperatureValue');
        const humidityValue = document.getElementById('humidityValue');
        const fanIcon = document.getElementById('fanIcon');
        const lightIcon = document.getElementById('lightIcon');
        const acIcon = document.getElementById('acIcon');
        const fanBtn = document.getElementById('fanBtn');
        const lightBtn = document.getElementById('lightBtn');
        const acBtn = document.getElementById('acBtn');
        const statusMessage = document.getElementById('statusMessage');
        const logoutBtn = document.getElementById('logoutBtn');

        function fetchSensorDataAndUpdateUI() {
            fetch("http://127.0.0.1:5001/sensor")
                .then(response => response.json())
                .then(data => {
                    if (data.temperature !== undefined && data.humidity !== undefined) {
                        document.getElementById('temperatureValue').innerText = data.temperature || "N/A";
                        document.getElementById('humidityValue').innerText = data.humidity || "N/A";
                    } else {
                        document.getElementById('temperatureValue').innerText = "Error";
                        document.getElementById('humidityValue').innerText = "Error";
                    }
                })
                .catch(err => {
                    console.error("Sensor fetch error:", err);
                    document.getElementById('temperatureValue').innerText = "Error";
                    document.getElementById('humidityValue').innerText = "Error";
                });
        }
        
        function fetchLastCommandAndUpdateUI() {
            fetch("http://127.0.0.1:5001/last_command")
                .then(response => response.json())
                .then(data => {
                    const commandText = data.last_command || "No command found.";
                    document.getElementById("last-command").innerText = commandText;
                })
                .catch(err => {
                    console.error("Last command fetch error:", err);
                    document.getElementById("last-command").innerText = "Error fetching command.";
                });
        }

        // Function to fetch appliance status from the backend
        function fetchApplianceStatus() {
            fetch('http://127.0.0.1:5001/get_status')
                .then(response => response.json())
                .then(data => {
                    Object.keys(buttons).forEach(appliance => {
                        state.appliances[appliance] = data[appliance];
                    });
                    updateUI();
                })
                .catch(err => {
                    console.error("Failed to fetch appliance status:", err);
                });
        }
        
        // Function to fetch status from backend and update the UI
        function syncApplianceStatus() {
                fetch('http://127.0.0.1:5001/get_status')
                .then(response => response.json())
                .then(data => {
                    // Update local state and UI if changed
                    let updated = false;
                    Object.keys(buttons).forEach(appliance => {
                        if (state.appliances[appliance] !== data[appliance]) {
                            state.appliances[appliance] = data[appliance];
                            updated = true;
                        }
                    });

                    if (updated) updateUI(); // only update UI if something changed
                })
                .catch(error => {
                    console.error("[ERROR] Failed to fetch status:", error);
                });
        }
        // Update the UI based on state
        function updateUI() {
            // Voice control
            if (state.isListening) {
                voiceControlBtn.classList.add('voice-control');
                voiceControlBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon mic-icon"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><path d="M12 19v3"></path></svg>
                    Voice Control
                `;
            }
                 
            /*// Gesture control
            if (state.gestureMode) {
                gestureControlBtn.classList.add('voice-control');
            } else {
                gestureControlBtn.classList.remove('voice-control');
            }*/

            // Environmental data
            temperatureValue.textContent = `${state.environmental.temperature}°C`;
            humidityValue.textContent = `${state.environmental.humidity}%`;


            // Fan
            if (state.appliances.fan) {
                fanIcon.classList.add('icon-active', 'spin');
                fanBtn.classList.add('on');
                fanBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon power-icon"><path d="M12 12h0"></path><path d="M18.36 6.64A9 9 0 0 1 20.77 15"></path><path d="M6.16 6.16a9 9 0 1 0 12.68 12.68"></path><path d="M12 2v4"></path></svg>
                    On
                `;
            } else {
                fanIcon.classList.remove('icon-active', 'spin');
                fanBtn.classList.remove('on');
                fanBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon power-icon"><path d="M12 12h0"></path><path d="M18.36 6.64A9 9 0 0 1 20.77 15"></path><path d="M6.16 6.16a9 9 0 1 0 12.68 12.68"></path><path d="M12 2v4"></path></svg>
                    Off
                `;
            }

            // Light
            if (state.appliances.light) {
                lightIcon.classList.add('icon-active');
                lightBtn.classList.add('on');
                lightBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon power-icon"><path d="M12 12h0"></path><path d="M18.36 6.64A9 9 0 0 1 20.77 15"></path><path d="M6.16 6.16a9 9 0 1 0 12.68 12.68"></path><path d="M12 2v4"></path></svg>
                    On
                `;
            } else {
                lightIcon.classList.remove('icon-active');
                lightBtn.classList.remove('on');
                lightBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon power-icon"><path d="M12 12h0"></path><path d="M18.36 6.64A9 9 0 0 1 20.77 15"></path><path d="M6.16 6.16a9 9 0 1 0 12.68 12.68"></path><path d="M12 2v4"></path></svg>
                    Off
                `;
            }

            // ac
            if (state.appliances.ac) {
                acIcon.classList.add('icon-active');
                acBtn.classList.add('on');
                acBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon power-icon"><path d="M12 12h0"></path><path d="M18.36 6.64A9 9 0 0 1 20.77 15"></path><path d="M6.16 6.16a9 9 0 1 0 12.68 12.68"></path><path d="M12 2v4"></path></svg>
                    On
                `;
            } else {
                acIcon.classList.remove('icon-active');
                acBtn.classList.remove('on');
                acBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon power-icon"><path d="M12 12h0"></path><path d="M18.36 6.64A9 9 0 0 1 20.77 15"></path><path d="M6.16 6.16a9 9 0 1 0 12.68 12.68"></path><path d="M12 2v4"></path></svg>
                    Off
                `;
            }

            // Status message
            if (state.isListening) {
                statusMessage.textContent = 'Listening for voice commands...';
            } else if (state.gestureMode) {
                statusMessage.textContent = 'Gesture detection active...';
            } else {
                statusMessage.textContent = 'Use voice or gesture controls to manage your smart home';
            }
        }

        function sendUpdatedStatus() {
            fetch('/update_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(state.appliances),
            })
            .then(response => response.json())
            .then(data => {
                console.log("Updated appliance status on server:", data);
            })
            .catch(error => {
                console.error("Error updating appliance status:", error);
            });
        }

        function startListening() {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = "en-US";
            recognition.start();
    
            recognition.onresult = function(event) {
                let transcript = event.results[0][0].transcript;
                document.getElementById("speechResult").innerText = transcript;
    
                // Send the transcription back to the dashboard
                window.opener.postMessage(transcript, "http://127.0.0.1:5001");
    
                // Auto-close after speech is processed
                setTimeout(() => {
                    window.close();
                }, 2000);
            };
    
            recognition.onerror = function(event) {
                alert("Error occurred in recognition: " + event.error);
            };
        }
        
        // Event listeners
        voiceControlBtn.addEventListener('click', () => {
            state.isListening = state.isListening;
            updateUI();
        });

        gestureControlBtn.addEventListener('click', () => {
            state.gestureMode = state.gestureMode;
            updateUI();
        });
        
        
        Object.keys(buttons).forEach(appliance => {
            buttons[appliance].addEventListener('click', () => {
                state.appliances[appliance] = !state.appliances[appliance];
                updateUI();
                sendUpdatedStatus();  
            });
        });
        

        logoutBtn.addEventListener('click', () => {
            // In a real app, this would redirect to login page or call logout API
            alert('Logging out...');
        });

        // Initialize
        updateUI();

        // Create floating particles
        function createParticles() {
            const body = document.body;
            const colors = ['#8a2be2', '#646cff', '#42b883', '#af4bce'];
            
            for (let i = 0; i < 15; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                
                // Random positioning
                const left = Math.random() * 100;
                const top = Math.random() * 100;
                
                // Random size (5-15px)
                const size = Math.random() * 10 + 5;
                
                // Random color
                const colorIndex = Math.floor(Math.random() * colors.length);
                
                // Random animation delay
                const delay = Math.random() * 5;
                
                // Apply styles
                particle.style.cssText = `
                    position: absolute;
                    border-radius: 50%;
                    opacity: 0.2;
                    animation: float 8s infinite ease-in-out;
                    left: ${left}%;
                    top: ${top}%;
                    width: ${size}px;
                    height: ${size}px;
                    background-color: ${colors[colorIndex]};
                    animation-delay: ${delay}s;
                    pointer-events: none;
                    z-index: -1;
                `;
                
                document.body.appendChild(particle);
            }
        }

        // Execute when DOM is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            createParticles();
            fetchSensorDataAndUpdateUI();
            fetchLastCommandAndUpdateUI();
            fetchApplianceStatus();
            syncApplianceStatus();


            setInterval(fetchSensorDataAndUpdateUI, 10000);
            setInterval(fetchLastCommandAndUpdateUI, 2000);
            setInterval(fetchApplianceStatus, 2000);
            setInterval(syncApplianceStatus, 2000);
        
            // Add random position updates for the radial gradients
            setInterval(() => {
                document.body.style.setProperty('--x', Math.random() * 100 + '%');
                document.body.style.setProperty('--y', Math.random() * 100 + '%');
                document.body.style.setProperty('--x2', Math.random() * 100 + '%');
                document.body.style.setProperty('--y2', Math.random() * 100 + '%');
            }, 3000);
        });
        