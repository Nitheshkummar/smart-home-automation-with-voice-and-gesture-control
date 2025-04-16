let socket = io();
let mediaRecorder;
let audioContext;
let audioStream;
let audioChunks = [];
let analyser;
let animationId;
let visualizerBars = [];

// Create particles
function createParticles() {
    const particles = document.getElementById('particles');
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
        
        particle.style.left = `${left}%`;
        particle.style.top = `${top}%`;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.backgroundColor = colors[colorIndex];
        particle.style.animationDelay = `${delay}s`;
        
        particles.appendChild(particle);
    }
}

// Call createParticles on page load
document.addEventListener('DOMContentLoaded', createParticles);

// Create visualizer bars
const visualizer = document.getElementById('visualizer');
for (let i = 0; i < 30; i++) {
    const bar = document.createElement('div');
    bar.className = 'bar';
    visualizer.appendChild(bar);
    visualizerBars.push(bar);
}

function updateVisualizer() {
    if (!analyser) return;
    
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    
    // Use only part of the frequency data
    const step = Math.floor(dataArray.length / visualizerBars.length);
    
    for (let i = 0; i < visualizerBars.length; i++) {
        const value = dataArray[i * step];
        const height = Math.max(3, value / 2);  // Scale down the height
        visualizerBars[i].style.height = height + 'px';
    }
    
    animationId = requestAnimationFrame(updateVisualizer);
}

// WAV encoder functions
function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

function writeInt16(view, offset, value) {
    view.setInt16(offset, value, true);
}

function writeInt32(view, offset, value) {
    view.setInt32(offset, value, true);
}

function encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // RIFF identifier
    writeString(view, 0, 'RIFF');
    // file length
    writeInt32(view, 4, 36 + samples.length * 2);
    // RIFF type
    writeString(view, 8, 'WAVE');
    // format chunk identifier
    writeString(view, 12, 'fmt ');
    // format chunk length
    writeInt32(view, 16, 16);
    // sample format (1 is PCM)
    writeInt16(view, 20, 1);
    // channel count
    writeInt16(view, 22, 1);
    // sample rate
    writeInt32(view, 24, sampleRate);
    // byte rate (sample rate * block align)
    writeInt32(view, 28, sampleRate * 2);
    // block align (channel count * bytes per sample)
    writeInt16(view, 32, 2);
    // bits per sample
    writeInt16(view, 34, 16);
    // data chunk identifier
    writeString(view, 36, 'data');
    // data chunk length
    writeInt32(view, 40, samples.length * 2);

    // write the PCM samples
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
        const s = Math.max(-1, Math.min(1, samples[i]));
        writeInt16(view, offset, s < 0 ? s * 0x8000 : s * 0x7FFF);
    }

    return new Blob([view], { type: 'audio/wav' });
}

document.getElementById("startRecord").onclick = function () {
    const status = document.getElementById("status");
    const output = document.getElementById("output");
    
    status.innerText = "Connecting to microphone...";
    status.className = "";
    output.innerText = "Transcribed text will appear here...";
    output.className = "animate__animated animate__fadeIn";
    
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        status.innerText = "Recording... Speak now";
        status.className = "status-recording";
        
        audioStream = stream;
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        audioChunks = [];
        
        processor.onaudioprocess = function(e) {
            const channelData = e.inputBuffer.getChannelData(0);
            // Push a copy of the audio data
            const channelDataCopy = new Float32Array(channelData.length);
            channelDataCopy.set(channelData);
            audioChunks.push(channelDataCopy);
        };
        
        // Start visualizer animation
        updateVisualizer();

        document.getElementById("startRecord").disabled = true;
        document.getElementById("stopRecord").disabled = false;
    }).catch(error => {
        console.error("Error accessing microphone:", error);
        status.innerText = "Error: " + error.message;
        status.className = "status-error";
    });
};

document.getElementById("stopRecord").onclick = function () {
    const status = document.getElementById("status");
    status.innerText = "Processing audio...";
    status.className = "status-processing";
    
    // Stop animation
    if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
    }
    
    // Reset visualizer bars
    visualizerBars.forEach(bar => {
        bar.style.height = '3px';
    });
    
    if (audioStream) {
        // Stop all audio tracks
        audioStream.getTracks().forEach(track => track.stop());
    }
    
    if (audioContext) {
        // Create one large Float32Array from all the chunks
        const sampleRate = audioContext.sampleRate;
        let totalLength = 0;
        audioChunks.forEach(chunk => {
            totalLength += chunk.length;
        });
        
        const mergedAudio = new Float32Array(totalLength);
        let offset = 0;
        audioChunks.forEach(chunk => {
            mergedAudio.set(chunk, offset);
            offset += chunk.length;
        });
        
        // Convert to WAV
        const wavBlob = encodeWAV(mergedAudio, sampleRate);
        
        // Convert to base64 and send
        const reader = new FileReader();
        reader.readAsDataURL(wavBlob);
        reader.onloadend = function() {
            const base64Audio = reader.result.split(",")[1];
            socket.emit("audio_data", { 
                audio_data: base64Audio,
                mime_type: 'audio/wav'
            });
        };
        
        analyser = null;
        audioContext.close();
        audioContext = null;
        audioStream = null;
    }
    
    document.getElementById("startRecord").disabled = false;
    document.getElementById("stopRecord").disabled = true;
};

socket.on("transcription", function (data) {
    const output = document.getElementById("output");
    const status = document.getElementById("status");
    
    output.className = "animate__animated animate__fadeIn";
    
    // Force reflow to restart animation
    void output.offsetWidth;
    
    output.innerText = data.text || "No speech detected";
    status.innerText = "Transcription complete";
    status.className = "status-complete";

    socket.emit("execute_command", { command: text });
});

socket.on("error", function (data) {
    const status = document.getElementById("status");
    status.innerText = "Error: " + data.message;
    status.className = "status-error";
});

// Add some animation on load
document.addEventListener('DOMContentLoaded', function() {
    // Stagger animation of bars on load for visual effect
    visualizerBars.forEach((bar, index) => {
        setTimeout(() => {
            bar.style.height = Math.floor(Math.random() * 10) + 'px';
            setTimeout(() => {
                bar.style.height = '3px';
            }, 300);
        }, index * 30);
    });
});