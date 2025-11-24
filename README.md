# Tuneboy: Retro-Synth Workstation

## Project Overview

Tuneboy is a multi-mode desktop music application built entirely in Python, designed to fuse the nostalgic aesthetic of a high-contrast CRT terminal with modern digital audio synthesis and sequencing. It offers a unique, minimalist workspace for musicians and developers interested in digital audio synthesis (DAS) and retro UI design.

The core of Tuneboy is a highly optimized, polyphonic sound engine using Pygame and NumPy to generate precise, low-latency pure Sine, Square, Sawtooth, and Triangle waveforms, eliminating reliance on external audio samples.

## Core Features

### 1. Serenade Mode (Virtual Piano)
A real-time playable virtual instrument optimized for immediate performance.

- **Custom Keymap**: Utilizes a custom QWERTY keyboard map specifically optimized for two-handed piano playing across two octaves.
  - White Keys: `ASDFGHJKL;'` (mapped to C4-F5)
  - Black Keys: `WETYUOP]` (mapped to C#4-F#5)
- **Real-time Controls**: Dedicated hotkeys (1 and 2) to cycle instrument presets and toggle sustain mode.
- **Visual Feedback**: The custom pixel-art piano graphically highlights pressed keys and reflects the current sound preset.

### 2. Orchestrate Mode (Step Sequencer)
A grid-based editor for composing looping patterns.

- **MIDI Grid**: Allows users to graphically draw note blocks onto a grid where the length of the drawn block precisely dictates the synthesized note's duration.
- **Playback Control**: Includes Play/Stop, BPM adjustment (`[` and `]`), and non-linear playhead navigation (Shift + Click).
- **Persistence**: Sequences can be saved and loaded as JSON files.

### 3. Terminal Aesthetic & Interaction
- **PyQt5 Custom Shell**: The entire application uses custom-styled PyQt5 widgets with a green-on-black color scheme (JetBrains Mono Medium font) and a custom, draggable Title Bar, maintaining an immersive console experience.
- **Bitbit Mascot**: An interactive 16x16 pixel mascot that provides state-based visual feedback (e.g., singing during playback, smiling in piano mode) through fluid bobbing and reactive micro-animations.

## Project Structure

The codebase is cleanly separated into modular files for easy maintenance and expansion:

| File | Description |
|------|-------------|
| `main.py` | Main application entry point. Initializes the PyQt5 window, the AudioEngine, the BitbitWidget, and manages screen transitions (QStackedWidget). |
| `config.py` | Stores all global constants: color palette, font family, splash screen messages, key mappings, note frequencies, and Bitbit's pixel maps. |
| `audio_engine.py` | Handles all sound generation. Uses NumPy to synthesize Sine, Square, Sawtooth, and Triangle waves. Manages polyphony, note caching, and clipping prevention. |
| `components.py` | Contains reusable UI elements like the TerminalButton, TitleBar, and BitbitWidget class, handling drag functionality and mascot animations. |
| `screens.py` | Defines the three main views: MainMenu, SerenadePiano, MidiSequencer, and InstructionsScreen. Contains the core UI layout and logic for each mode. |
| `tuneboy.spec` | PyInstaller configuration file used for creating the optimized Windows executable. |

## Installation & Usage

### Prerequisites

You need a Python environment (3.7+) with the following dependencies:

```bash
pip install PyQt5 pygame numpy
