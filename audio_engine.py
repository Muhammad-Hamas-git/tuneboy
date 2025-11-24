import numpy as np
import pygame
from config import SAMPLE_RATE, BIT_DEPTH, FREQUENCIES

class AudioEngine:
    def __init__(self):
        # Initialize pygame mixer with low latency
        pygame.mixer.pre_init(SAMPLE_RATE, -BIT_DEPTH, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32) # Allow polyphony

        self.presets = ['sine', 'square', 'sawtooth', 'triangle']
        self.current_preset_index = 0
        self.sustain = False
        
        # Cache for generated sound objects
        self.sound_cache = {}
        self.active_channels = {} 
        self.typing_notes = [
            261.63, 329.63, 392.00, 493.88, 587.33,
            523.25, 659.25, 783.99, 987.77, 1174.66
        ]
        self._generate_all_presets()

    @property
    def current_preset(self):
        return self.presets[self.current_preset_index]

    def cycle_preset(self):
        self.current_preset_index = (self.current_preset_index + 1) % len(self.presets)
        return self.current_preset
        
    def toggle_sustain(self):
        self.sustain = not self.sustain
        return self.sustain

    def _generate_wave(self, freq, shape, duration=4.0, volume=0.1): 
        # Increased duration to 4.0s to support long sequencer notes
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        
        if shape == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif shape == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif shape == 'sawtooth':
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))
        elif shape == 'triangle':
            wave = np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) * 2 - 1
        else:
            wave = np.sin(2 * np.pi * freq * t)

        envelope = np.ones_like(wave)
        attack = int(SAMPLE_RATE * 0.01)
        release = int(SAMPLE_RATE * 0.05) 
        
        if len(t) > attack + release:
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
        
        wave = wave * envelope * volume
        audio_data = (wave * 32767).astype(np.int16)
        return np.column_stack((audio_data, audio_data))

    def _generate_all_presets(self):
        print("Synthesizing waveforms...")
        for preset in self.presets:
            self.sound_cache[preset] = {}
            for note, freq in FREQUENCIES.items():
                arr = self._generate_wave(freq, preset)
                self.sound_cache[preset][note] = pygame.sndarray.make_sound(arr)

    def play_note(self, note_name, instrument=None, duration_ms=None):
        inst = instrument if instrument else self.current_preset
        
        if inst in self.sound_cache and note_name in self.sound_cache[inst]:
            sound = self.sound_cache[inst][note_name]
            
            # If duration is provided (Sequencer), limit playback time
            if duration_ms:
                sound.play(maxtime=int(duration_ms))
            else:
                channel = sound.play()
                if channel:
                    self.active_channels[note_name] = channel

    def stop_note(self, note_name):
        if self.sustain:
            return

        if note_name in self.active_channels:
            channel = self.active_channels[note_name]
            try:
                channel.fadeout(100)
            except:
                pass
            del self.active_channels[note_name]

    def stop_all(self):
        """Immediately stops all audio playback."""
        pygame.mixer.stop()
        self.active_channels.clear()
            
    def play_sound_effect(self, type="beep", index=0):
        if type == "type":
            freq = self.typing_notes[index % len(self.typing_notes)]
            vol = 0.05 + (0.02 * np.sin(index))
            arr = self._generate_wave(freq, 'sine', 0.1, vol)
            s = pygame.sndarray.make_sound(arr)
            s.play()
        elif type == "hover":
            freq = 200
            arr = self._generate_wave(freq, 'sawtooth', 0.05, 0.03)
            s = pygame.sndarray.make_sound(arr)
            s.play()