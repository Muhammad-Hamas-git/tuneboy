import random
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGraphicsScene, QGraphicsView, QGraphicsRectItem, QFrame, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QPainter
from config import COLORS, KEY_MAPPINGS, SPLASH_MESSAGES, FREQUENCIES, FONT_FAMILY
from components import TerminalButton

# --- HELPER WIDGETS ---
class HLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet(f"color: {COLORS['fg_dim']}; border: none; border-bottom: 1px solid {COLORS['fg_dim']};")

class VLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setStyleSheet(f"color: {COLORS['fg_dim']}; border: none; border-right: 1px solid {COLORS['fg_dim']};")

# --- CUSTOM PIANO WIDGET ---
class PixelPiano(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 200)
        self.active_notes = set()
        
        all_notes = list(FREQUENCIES.keys())
        mapped_notes = set(KEY_MAPPINGS.values())
        self.notes_sorted = [n for n in all_notes if n in mapped_notes]
        
        self.white_keys = [n for n in self.notes_sorted if '#' not in n]
        self.black_keys = [n for n in self.notes_sorted if '#' in n]

    def set_active_notes(self, notes):
        self.active_notes = notes
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        w = self.width()
        h = self.height()
        
        key_width = w / len(self.white_keys)
        white_key_h = h
        black_key_h = h * 0.6
        black_key_w = key_width * 0.6
        
        pen = QPen(QColor(COLORS['fg']))
        pen.setWidth(2)
        painter.setPen(pen)
        
        dither_brush = QBrush(QColor(COLORS['fg_dim']), Qt.Dense4Pattern)
        active_brush = QBrush(QColor(COLORS['note_active']), Qt.SolidPattern)
        
        white_positions = {}
        for i, note in enumerate(self.white_keys):
            x = i * key_width
            white_positions[note] = x
            if note in self.active_notes:
                painter.setBrush(active_brush)
            else:
                painter.setBrush(dither_brush)
            painter.drawRect(QRectF(x, 0, key_width, white_key_h))
            painter.setPen(QColor(COLORS['fg']))
            painter.drawText(QRectF(x, h - 30, key_width, 20), Qt.AlignCenter, note)
            painter.setPen(pen)

        for note in self.black_keys:
            base_note = note.replace('#', '')
            if base_note in white_positions:
                wx = white_positions[base_note]
                bx = wx + (key_width * 0.7)
                if note in self.active_notes:
                    painter.setBrush(active_brush)
                else:
                    painter.setBrush(QBrush(QColor(COLORS['bg']), Qt.SolidPattern)) 
                    painter.drawRect(QRectF(bx, 0, black_key_w, black_key_h))
                    painter.setBrush(dither_brush) 
                painter.drawRect(QRectF(bx, 0, black_key_w, black_key_h))
                painter.setPen(QColor(COLORS['fg']))
                painter.drawText(QRectF(bx, black_key_h - 25, black_key_w, 20), Qt.AlignCenter, note)
                painter.setPen(pen)

# --- SEQUENCER VIEW ---
class SequencerView(QGraphicsView):
    def __init__(self, scene, sequencer_parent):
        super().__init__(scene)
        self.seq = sequencer_parent
        self.setRenderHint(QPainter.Antialiasing, False)
        self.setMouseTracking(True)
        self.viewport().setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        
        if event.modifiers() & Qt.ShiftModifier and event.button() == Qt.LeftButton:
            col = int(scene_pos.x() / self.seq.cell_w)
            self.seq.set_playhead(col)
        elif event.button() == Qt.LeftButton:
            self.seq.start_drawing_note(scene_pos.x(), scene_pos.y())
        elif event.button() == Qt.RightButton:
            item = self.itemAt(event.pos())
            if isinstance(item, NoteRect):
                self.scene().removeItem(item)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.seq.is_drawing:
            scene_pos = self.mapToScene(event.pos())
            self.seq.update_drawing_note(scene_pos.x())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.seq.finish_drawing_note()
        super().mouseReleaseEvent(event)

# --- SCREENS ---

class MainMenu(QWidget):
    def __init__(self, audio, navigate_callback, mascot):
        super().__init__()
        self.audio = audio
        self.navigate = navigate_callback
        self.mascot = mascot 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Explicit border: none for title and splash
        self.lbl_title = QLabel("// tuneboy", self)
        self.lbl_title.setFont(QFont(FONT_FAMILY, 40, QFont.Bold))
        self.lbl_title.setStyleSheet(f"color: {COLORS['fg']}; border: none;") 
        layout.addWidget(self.lbl_title)
        
        self.lbl_splash = QLabel("", self)
        splash_font = QFont(FONT_FAMILY, 14)
        splash_font.setItalic(True)
        self.lbl_splash.setFont(splash_font)
        self.lbl_splash.setStyleSheet(f"color: {COLORS['fg_dim']}; border: none;") 
        layout.addWidget(self.lbl_splash)
        
        self.full_splash_text = f"# {random.choice(SPLASH_MESSAGES)}"
        self.type_idx = 0
        self.type_timer = QTimer(self)
        self.type_timer.timeout.connect(self._type_splash)
        self.type_timer.start(50)

        layout.addSpacing(40)

        self.btn_piano = self._create_nav_btn("> serenade!", "piano", "smiling")
        self.btn_seq = self._create_nav_btn("> orchestrate", "sequencer", "singing")
        self.btn_help = self._create_nav_btn("> instructions", "help", "hm")
        
        layout.addWidget(self.btn_piano)
        layout.addWidget(self.btn_seq)
        layout.addWidget(self.btn_help)
        layout.addStretch()
        
        # FIXED: Call the connection method
        self._connect_mascot_hover()

    def _create_nav_btn(self, text, target, expression):
        btn = TerminalButton(text)
        btn.clicked.connect(lambda: self.navigate(target))
        btn.hovered.connect(lambda: self._on_hover(expression))
        btn.left.connect(lambda: self.mascot.set_expression("neutral"))
        return btn

    def _connect_mascot_hover(self):
        self.mascot.hovered.connect(lambda: self.mascot.set_expression("freaky"))
        self.mascot.left.connect(lambda: self.mascot.set_expression("neutral"))

    def _on_hover(self, expr):
        self.audio.play_sound_effect("hover")
        self.mascot.set_expression(expr)

    def _type_splash(self):
        if self.type_idx < len(self.full_splash_text):
            self.lbl_splash.setText(self.full_splash_text[:self.type_idx+1])
            if self.type_idx % 2 == 0: 
                self.audio.play_sound_effect("type", self.type_idx)
            self.type_idx += 1
        else:
            self.type_timer.stop()

class SerenadePiano(QWidget):
    def __init__(self, audio, back_callback, mascot):
        super().__init__()
        self.audio = audio
        self.back_callback = back_callback
        self.mascot = mascot
        self.active_keys = set()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        header = QHBoxLayout()
        lbl_mode = QLabel("MODE: SERENADE")
        lbl_mode.setFont(QFont(FONT_FAMILY, 20, QFont.Bold))
        lbl_mode.setStyleSheet(f"color: {COLORS['fg']}; border: none;")
        header.addWidget(lbl_mode)
        header.addWidget(VLine())
        self.lbl_info = QLabel("INST: SINE")
        self.lbl_info.setFont(QFont(FONT_FAMILY, 14))
        self.lbl_info.setStyleSheet(f"color: {COLORS['fg_bright']}; border: none;")
        header.addWidget(self.lbl_info)
        header.addStretch()
        btn_back = TerminalButton("< BACK")
        btn_back.clicked.connect(lambda: [back_callback(), self.mascot.set_expression("neutral")])
        header.addWidget(btn_back)
        
        self.layout.addLayout(header)
        self.layout.addWidget(HLine())
        self.layout.addStretch()
        
        self.piano_widget = PixelPiano()
        self.layout.addWidget(self.piano_widget)
        
        self.layout.addStretch()
        self.layout.addWidget(HLine())
        
        footer = QHBoxLayout()
        controls = QLabel("CONTROLS: [1] CYCLE INST | [2] SUSTAIN TOGGLE")
        controls.setStyleSheet(f"color: {COLORS['fg_dim']}; font-family: {FONT_FAMILY}; border: none;")
        footer.addWidget(controls)
        self.layout.addLayout(footer)

    def keyPressEvent(self, event):
        if event.isAutoRepeat(): return
        key = event.text().lower()
        if key == '1':
            new_preset = self.audio.cycle_preset()
            self._update_status()
        elif key == '2':
            self.audio.toggle_sustain()
            self._update_status()
        elif key in KEY_MAPPINGS:
            note = KEY_MAPPINGS[key]
            if not self.active_keys:
                self.mascot.set_expression("singing")
            self.audio.play_note(note)
            self.active_keys.add(key)
            active_notes = {KEY_MAPPINGS[k] for k in self.active_keys}
            self.piano_widget.set_active_notes(active_notes)
    
    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): return
        key = event.text().lower()
        if key in KEY_MAPPINGS:
            note = KEY_MAPPINGS[key]
            self.audio.stop_note(note)
            if key in self.active_keys:
                self.active_keys.remove(key)
            active_notes = {KEY_MAPPINGS[k] for k in self.active_keys}
            self.piano_widget.set_active_notes(active_notes)
            if not self.active_keys:
                self.mascot.set_expression("smiling")

    def _update_status(self):
        inst = self.audio.current_preset.upper()
        sus = "ON" if self.audio.sustain else "OFF"
        self.lbl_info.setText(f"INST: {inst} | SUS: {sus}")

class InstructionsScreen(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        
        title = QLabel("> INSTRUCTIONS.TXT")
        title.setFont(QFont(FONT_FAMILY, 24, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['fg']}; border: none;")
        layout.addWidget(title)
        layout.addWidget(HLine())
        
        grid_layout = QHBoxLayout()
        col1 = QLabel("""
        [ WHITE KEYS ]
        A -> C4
        S -> D4
        D -> E4
        F -> F4
        G -> G4
        H -> A4
        J -> B4
        K -> C5
        L -> D5
        ; -> E5
        ' -> F5
        """)
        col1.setFont(QFont(FONT_FAMILY, 12))
        col1.setStyleSheet(f"color: {COLORS['fg_dim']}; border: none;")
        
        col2 = QLabel("""
        [ BLACK KEYS ]
        W -> C#4
        E -> D#4
        T -> F#4
        Y -> G#4
        U -> A#4
        O -> C#5
        P -> D#5
        ] -> F#5
        """)
        col2.setFont(QFont(FONT_FAMILY, 12))
        col2.setStyleSheet(f"color: {COLORS['fg_dim']}; border: none;")
        
        grid_layout.addWidget(col1)
        grid_layout.addWidget(VLine())
        grid_layout.addWidget(col2)
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
        btn_back = TerminalButton("< BACK_TO_ROOT")
        btn_back.clicked.connect(back_callback)
        layout.addWidget(btn_back)

class MidiSequencer(QWidget):
    def __init__(self, audio, back_callback, mascot):
        super().__init__()
        self.audio = audio
        self.back_callback = back_callback
        self.mascot = mascot 
        self.is_playing = False
        self.is_drawing = False
        self.playhead_x = 0
        self.bpm = 120
        self.selected_inst = "sine"
        self.cell_w = 40
        self.cell_h = 25
        self.grid_rows = list(FREQUENCIES.keys())[::-1] 
        self.width_steps = 100
        
        self.current_drawing_note = None
        self.drawing_start_col = 0
        
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Save/Load Buttons
        btn_save = TerminalButton("[ SAVE ]")
        btn_save.clicked.connect(self.save_sequence)
        toolbar.addWidget(btn_save)
        
        btn_load = TerminalButton("[ LOAD ]")
        btn_load.clicked.connect(self.load_sequence)
        toolbar.addWidget(btn_load)
        
        toolbar.addWidget(VLine())
        
        self.lbl_tool = QLabel(f"TOOL: {self.selected_inst.upper()}")
        self.lbl_tool.setStyleSheet(f"color: {COLORS['fg']}; font-family: {FONT_FAMILY}; font-weight: bold; border: none;")
        toolbar.addWidget(self.lbl_tool)
        
        self.lbl_bpm = QLabel(f"BPM: {self.bpm} [ / ]")
        self.lbl_bpm.setStyleSheet(f"color: {COLORS['fg_dim']}; font-family: {FONT_FAMILY}; border: none;")
        toolbar.addWidget(self.lbl_bpm)
        
        self.btn_play = TerminalButton("[ PLAY ]")
        self.btn_play.clicked.connect(self.toggle_play)
        toolbar.addWidget(self.btn_play)
        
        self.btn_clear = TerminalButton("[ CLEAR ]")
        self.btn_clear.clicked.connect(self.clear_grid)
        toolbar.addWidget(self.btn_clear)
        
        btn_back = TerminalButton("[ EXIT ]")
        btn_back.clicked.connect(self.exit_sequencer)
        toolbar.addWidget(btn_back)
        
        main_layout.addLayout(toolbar)
        
        # Graphics Scene
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor(COLORS['bg'])))
        
        self.view = SequencerView(self.scene, self)
        self.view.setStyleSheet(f"border: 1px solid {COLORS['fg_dim']}; outline: none;")
        
        scene_width = self.width_steps * self.cell_w
        scene_height = len(self.grid_rows) * self.cell_h
        self.scene.setSceneRect(0, 0, scene_width, scene_height)
        
        pen_grid = QPen(QColor(COLORS['grid']))
        pen_grid.setStyle(Qt.DotLine)
        
        for i, note in enumerate(self.grid_rows):
            y = i * self.cell_h
            self.scene.addLine(0, y, scene_width, y, pen_grid)
            txt = self.scene.addText(note)
            txt.setDefaultTextColor(QColor(COLORS['fg_dim']))
            txt.setPos(0, y)
            txt.setFont(QFont(FONT_FAMILY, 8))

        for i in range(self.width_steps):
            x = i * self.cell_w
            self.scene.addLine(x, 0, x, scene_height, pen_grid)

        self.playhead_line = self.scene.addLine(0, 0, 0, scene_height, QPen(QColor(COLORS['playhead']), 2))
        self.playhead_line.setZValue(10)

        main_layout.addWidget(self.view)
        
        info = QLabel("Shift+Click: Move Playhead | L-Click+Drag: Create Note | R-Click: Delete | [1]: Instrument")
        info.setStyleSheet(f"color: {COLORS['fg_dim']}; font-family: {FONT_FAMILY}; border: none;")
        main_layout.addWidget(info)

    def start_drawing_note(self, x, y):
        col = int(x / self.cell_w)
        row = int(y / self.cell_h)
        if row < 0 or row >= len(self.grid_rows): return
        
        note_name = self.grid_rows[row]
        rect_x = col * self.cell_w
        rect_y = row * self.cell_h
        
        self.current_drawing_note = NoteRect(0, 0, self.cell_w, self.cell_h, 
                                             note_name, self.selected_inst)
        self.current_drawing_note.setPos(rect_x, rect_y)
        self.scene.addItem(self.current_drawing_note)
        
        self.is_drawing = True
        self.drawing_start_col = col
        
        self.audio.play_note(note_name, self.selected_inst, duration_ms=200)

    def update_drawing_note(self, x):
        if not self.is_drawing or not self.current_drawing_note: return
        col = int(x / self.cell_w)
        width_cells = max(1, col - self.drawing_start_col + 1)
        new_w = width_cells * self.cell_w
        rect = self.current_drawing_note.rect()
        rect.setWidth(new_w)
        self.current_drawing_note.setRect(rect)

    def finish_drawing_note(self):
        self.is_drawing = False
        self.current_drawing_note = None

    def keyPressEvent(self, event):
        # UPDATED: Use key '1' instead of Tab to avoid focus cycling issues
        if event.key() == Qt.Key_1:
            self.selected_inst = self.audio.cycle_preset()
            self.lbl_tool.setText(f"TOOL: {self.selected_inst.upper()}")
        elif event.text() == '[':
            self.bpm = max(60, self.bpm - 5)
            self.update_bpm_label()
        elif event.text() == ']':
            self.bpm = min(240, self.bpm + 5)
            self.update_bpm_label()

    def update_bpm_label(self):
        self.lbl_bpm.setText(f"BPM: {self.bpm} [ / ]")
        if self.is_playing:
            self.timer.start(int(60000 / (self.bpm * 4)))

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("[ STOP ]")
            interval = 60000 / (self.bpm * 4) 
            self.timer.start(int(interval))
            self.mascot.set_expression("singing")
            self.tick(increment=False) # Check current pos immediately
        else:
            self.btn_play.setText("[ PLAY ]")
            self.timer.stop()
            self.audio.stop_all() 
            self.mascot.set_expression("neutral")

    def exit_sequencer(self):
        self.is_playing = False
        self.timer.stop()
        self.audio.stop_all() 
        self.mascot.set_expression("neutral")
        self.back_callback()

    def set_playhead(self, col):
        self.playhead_x = col
        self.tick(increment=False)

    def tick(self, increment=True):
        px_x = self.playhead_x * self.cell_w
        self.playhead_line.setLine(px_x, 0, px_x, self.scene.height())
        
        tick_duration = 60000 / (self.bpm * 4)
        
        # Check notes AT CURRENT position
        for item in self.scene.items():
            if isinstance(item, NoteRect):
                note_start_col = int(item.x() // self.cell_w)
                if note_start_col == self.playhead_x:
                    width_cells = item.rect().width() / self.cell_w
                    note_duration = width_cells * tick_duration
                    self.audio.play_note(item.note_name, item.instrument, duration_ms=note_duration)
        
        # THEN Increment
        if increment:
            self.playhead_x += 1
            if self.playhead_x >= self.width_steps:
                self.playhead_x = 0

    def clear_grid(self):
        for item in self.scene.items():
            if isinstance(item, NoteRect):
                self.scene.removeItem(item)

    # --- SAVE / LOAD LOGIC ---
    def save_sequence(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Sequence", "", "JSON Files (*.json)")
        if not filepath: return
        
        data = []
        for item in self.scene.items():
            if isinstance(item, NoteRect):
                note_data = {
                    "x": item.x(),
                    "y": item.y(),
                    "w": item.rect().width(),
                    "h": item.rect().height(),
                    "note": item.note_name,
                    "inst": item.instrument
                }
                data.append(note_data)
        
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load_sequence(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Sequence", "", "JSON Files (*.json)")
        if not filepath: return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        self.clear_grid()
        for d in data:
            rect = NoteRect(0, 0, d['w'], d['h'], d['note'], d['inst'])
            rect.setPos(d['x'], d['y'])
            self.scene.addItem(rect)

class NoteRect(QGraphicsRectItem):
    def __init__(self, x, y, w, h, note_name, instrument):
        super().__init__(x, y, w, h)
        self.note_name = note_name
        self.instrument = instrument
        
        self.setPen(QPen(QColor(COLORS['bg']), 1))
        
        if instrument == 'sine': col = "#00ff00"
        elif instrument == 'square': col = "#00ccaa"
        elif instrument == 'sawtooth': col = "#ccff00"
        elif instrument == 'triangle': col = "#0088ff"
        else: col = COLORS['note_active']

        self.setBrush(QBrush(QColor(col)))