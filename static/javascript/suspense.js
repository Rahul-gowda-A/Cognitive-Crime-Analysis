/**
 * CRIME ANALYSIS - SUSPENSE & TACTICAL INTELLIGENCE FX SYSTEM
 * Synthesizes Web Audio API sound effects, radar animations, typing dossier effects,
 * and high-tension threat level reveals.
 */

// Web Audio API Sound Synthesizer (No external mp3 files required)
class SuspenseAudioEngine {
    constructor() {
        this.ctx = null;
        this.muted = localStorage.getItem('crime_audio_muted') === 'true';
        this.ambientOsc = null;
        this.ambientGain = null;
        this.isAmbientPlaying = false;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        localStorage.setItem('crime_audio_muted', this.muted);
        if (this.muted && this.isAmbientPlaying) {
            this.stopAmbient();
        } else if (!this.muted && !this.isAmbientPlaying) {
            this.playAmbient();
        }
        return this.muted;
    }

    // Play subtle tactical click/blip
    playBlip(freq = 800, type = 'sine', duration = 0.06) {
        if (this.muted) return;
        try {
            this.init();
            if (!this.ctx) return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(freq * 0.4, this.ctx.currentTime + duration);

            gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start();
            osc.stop(this.ctx.currentTime + duration);
        } catch (e) {
            // Audio context policy safe catch
        }
    }

    // Play suspenseful threat alert reveal
    playThreatAlert(isRed = false) {
        if (this.muted) return;
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            
            // Dramatic low sub-bass impact
            const sub = this.ctx.createOscillator();
            const subGain = this.ctx.createGain();
            sub.type = 'sawtooth';
            sub.frequency.setValueAtTime(isRed ? 110 : 80, now);
            sub.frequency.exponentialRampToValueAtTime(35, now + 0.6);
            subGain.gain.setValueAtTime(0.12, now);
            subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
            sub.connect(subGain);
            subGain.connect(this.ctx.destination);
            sub.start(now);
            sub.stop(now + 0.7);

            // High tension radar sonar ping
            const ping = this.ctx.createOscillator();
            const pingGain = this.ctx.createGain();
            ping.type = 'sine';
            ping.frequency.setValueAtTime(isRed ? 950 : 650, now + 0.05);
            ping.frequency.exponentialRampToValueAtTime(isRed ? 1200 : 850, now + 0.4);
            pingGain.gain.setValueAtTime(0.08, now + 0.05);
            pingGain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
            ping.connect(pingGain);
            pingGain.connect(this.ctx.destination);
            ping.start(now + 0.05);
            ping.stop(now + 0.5);
        } catch (e) {}
    }

    // Play subtle low ambient suspense drone
    playAmbient() {
        if (this.muted || this.isAmbientPlaying) return;
        try {
            this.init();
            if (!this.ctx) return;
            this.ambientOsc = this.ctx.createOscillator();
            this.ambientGain = this.ctx.createGain();

            this.ambientOsc.type = 'sine';
            this.ambientOsc.frequency.setValueAtTime(48, this.ctx.currentTime); // Low 48Hz drone

            this.ambientGain.gain.setValueAtTime(0.001, this.ctx.currentTime);
            this.ambientGain.gain.linearRampToValueAtTime(0.02, this.ctx.currentTime + 3);

            this.ambientOsc.connect(this.ambientGain);
            this.ambientGain.connect(this.ctx.destination);

            this.ambientOsc.start();
            this.isAmbientPlaying = true;
        } catch (e) {}
    }

    stopAmbient() {
        try {
            if (this.ambientGain && this.ctx) {
                this.ambientGain.gain.linearRampToValueAtTime(0.0001, this.ctx.currentTime + 1);
                setTimeout(() => {
                    if (this.ambientOsc) {
                        this.ambientOsc.stop();
                        this.ambientOsc.disconnect();
                        this.ambientOsc = null;
                    }
                    this.isAmbientPlaying = false;
                }, 1000);
            }
        } catch (e) {}
    }
}

const SuspenseFX = new SuspenseAudioEngine();

// Attach UI interaction listeners
document.addEventListener('DOMContentLoaded', () => {
    // Add Suspense Header Bar if not present
    injectSuspenseStatusBar();

    // Attach sound on buttons & cards
    attachInteractiveSounds();

    // Initialize Dropdown menu click & touch handlers
    initDropdownInteractions();

    // Enhance prediction result reveal with suspense animations
    enhancePredictionReveals();

    // First user gesture enables audio context smoothly
    const unlockAudio = () => {
        SuspenseFX.init();
        if (!SuspenseFX.muted && !SuspenseFX.isAmbientPlaying) {
            SuspenseFX.playAmbient();
        }
        document.removeEventListener('click', unlockAudio);
        document.removeEventListener('keydown', unlockAudio);
    };
    document.addEventListener('click', unlockAudio);
    document.addEventListener('keydown', unlockAudio);
});

function initDropdownInteractions() {
    document.querySelectorAll('.drop-down').forEach(dropdown => {
        const btn = dropdown.querySelector('button, .button');
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = dropdown.classList.contains('open');
                // Close other open dropdowns
                document.querySelectorAll('.drop-down.open').forEach(d => {
                    if (d !== dropdown) d.classList.remove('open');
                });
                dropdown.classList.toggle('open', !isOpen);
                if (!isOpen) {
                    SuspenseFX.playBlip(1050, 'sine', 0.05);
                }
            });
        }
    });

    // Close open dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.drop-down')) {
            document.querySelectorAll('.drop-down.open').forEach(d => d.classList.remove('open'));
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.drop-down.open').forEach(d => d.classList.remove('open'));
        }
    });
}

function injectSuspenseStatusBar() {
    if (document.getElementById('tactical-status-strip')) return;

    const nav = document.querySelector('nav.main');
    const strip = document.createElement('div');
    strip.id = 'tactical-status-strip';
    strip.className = 'tactical-status-strip';

    const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
    const isMuted = SuspenseFX.muted;

    strip.innerHTML = `
        <div class="status-left">
            <span class="status-indicator red-pulse"></span>
            <span class="status-tag">RESTRICTED DOSSIER // CRIME ANALYSIS INTELLIGENCE</span>
            <span class="status-coord hidden-mobile">SYS.VER: 4.8.2 // UTC: <span id="tactical-clock">${timestamp}</span></span>
        </div>
        <div class="status-right">
            <span class="threat-badge"><span class="radar-blip"></span> SURVEILLANCE RADAR: ARMED</span>
            <button id="audio-toggle-btn" class="audio-btn" title="Toggle Suspense Sound FX">
                <span class="audio-icon">${isMuted ? '🔇' : '🔊'}</span>
                <span class="audio-text">${isMuted ? 'FX: OFF' : 'FX: LIVE'}</span>
            </button>
        </div>
    `;

    if (nav) {
        nav.parentNode.insertBefore(strip, nav);
    } else {
        document.body.insertBefore(strip, document.body.firstChild);
    }

    // Audio button click listener
    const audioBtn = document.getElementById('audio-toggle-btn');
    if (audioBtn) {
        audioBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const nowMuted = SuspenseFX.toggleMute();
            audioBtn.querySelector('.audio-icon').textContent = nowMuted ? '🔇' : '🔊';
            audioBtn.querySelector('.audio-text').textContent = nowMuted ? 'FX: OFF' : 'FX: LIVE';
            if (!nowMuted) {
                SuspenseFX.playBlip(1000, 'sine', 0.1);
            }
        });
    }

    // Live clock updater
    setInterval(() => {
        const clock = document.getElementById('tactical-clock');
        if (clock) {
            clock.textContent = new Date().toISOString().slice(0, 19).replace('T', ' ');
        }
    }, 1000);
}

function attachInteractiveSounds() {
    // Buttons hover & click sound
    document.querySelectorAll('button, .button, .btn, a, select, input').forEach(el => {
        el.addEventListener('mouseenter', () => {
            SuspenseFX.playBlip(900, 'sine', 0.03);
        });
        el.addEventListener('click', () => {
            SuspenseFX.playBlip(1200, 'triangle', 0.08);
        });
    });

    // Card hover sound
    document.querySelectorAll('.card, .drop-down, .dossier-card, .xl\\:w-1\\/4').forEach(card => {
        card.addEventListener('mouseenter', () => {
            SuspenseFX.playBlip(440, 'sine', 0.05);
        });
    });
}

function enhancePredictionReveals() {
    // Check K-Means prediction result
    const clusterElem = document.getElementById('cluster-text');
    if (clusterElem && clusterElem.textContent.trim().length > 0) {
        const txt = clusterElem.textContent.trim();
        const isRed = txt.includes('RED');
        const isOrange = txt.includes('ORANGE') || txt.includes('Yellow');
        
        clusterElem.classList.add('suspense-reveal');
        if (isRed) {
            clusterElem.classList.add('threat-critical');
        } else if (isOrange) {
            clusterElem.classList.add('threat-elevated');
        } else {
            clusterElem.classList.add('threat-low');
        }
        SuspenseFX.playThreatAlert(isRed);
    }

    // Check Random Forest & Linear Regression prediction result
    const rfPredElem = document.getElementById('prediction-text');
    if (rfPredElem && rfPredElem.textContent.trim().length > 0) {
        const isRed = rfPredElem.textContent.includes('RED');
        SuspenseFX.playThreatAlert(isRed);
    }

    const lrPredElem = document.getElementById('prediction-input');
    if (lrPredElem && lrPredElem.textContent.trim().length > 0) {
        SuspenseFX.playThreatAlert(false);
    }
}
