import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve

from config import COLORS
from audio_engine import AudioEngine
from components import BitbitWidget, FadeOverlay, TitleBar
from screens import MainMenu, SerenadePiano, MidiSequencer, InstructionsScreen

class TuneboyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 700)
        
        # Main Container
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainContainer")
        
        # Targeting #MainContainer ensures border doesn't cascade to children labels automatically
        # We will add borders manually to components that need them (Buttons, etc.)
        self.central_widget.setStyleSheet(f"""
            #MainContainer {{
                background-color: {COLORS['bg']}; 
                border: 1px solid {COLORS['fg_dim']};
            }}
        """)
        self.setCentralWidget(self.central_widget)
        
        # Layout for TitleBar + Content
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Custom Title Bar
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        
        # 2. Stacked Content
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # Audio Engine
        self.audio = AudioEngine()
        
        # Mascot (Bitbit)
        self.mascot = BitbitWidget(self.central_widget)
        self.default_mascot_pos = QPoint(800, 300)
        self.mascot.move(self.default_mascot_pos)
        self.mascot.raise_()
        
        # Mascot Movement Animation
        self.mascot_anim = QPropertyAnimation(self.mascot, b"pos")
        self.mascot_anim.setDuration(800)
        self.mascot_anim.setEasingCurve(QEasingCurve.OutBack)
        
        # Initialize Screens
        self.menu_screen = MainMenu(self.audio, self.navigate_to, self.mascot)
        self.piano_screen = SerenadePiano(self.audio, self.go_home, self.mascot)
        self.seq_screen = MidiSequencer(self.audio, self.go_home, self.mascot)
        self.help_screen = InstructionsScreen(self.go_home)
        
        self.stack.addWidget(self.menu_screen) # Index 0
        self.stack.addWidget(self.piano_screen) # Index 1
        self.stack.addWidget(self.seq_screen) # Index 2
        self.stack.addWidget(self.help_screen) # Index 3
        
        # Fade Overlay
        self.fade = FadeOverlay(self.central_widget)
        self.fade.setGeometry(0, 40, self.width(), self.height()-40)
        self.fade.finished.connect(self._on_fade_finished)
        self.next_index = 0

    def resizeEvent(self, event):
        self.fade.setGeometry(0, 40, self.width(), self.height()-40)
        if self.stack.currentIndex() == 0:
            self.default_mascot_pos = QPoint(self.width() - 200, self.height() // 2 - 64)
            self.mascot.move(self.default_mascot_pos)
        super().resizeEvent(event)

    def navigate_to(self, target):
        idx = 0
        if target == "piano": idx = 1
        elif target == "sequencer": idx = 2
        elif target == "help": idx = 3
        
        self.next_index = idx
        self.fade.raise_()
        self.fade.fade_out()

        if target == "piano":
            target_pos = QPoint(self.width() - 200, 150)
            self.mascot_anim.setStartValue(self.mascot.pos())
            self.mascot_anim.setEndValue(target_pos)
            self.mascot_anim.start()
        elif target == "home" or target == "help":
            self.mascot_anim.setStartValue(self.mascot.pos())
            self.default_mascot_pos = QPoint(self.width() - 200, self.height() // 2 - 64)
            self.mascot_anim.setEndValue(self.default_mascot_pos)
            self.mascot_anim.start()

    def go_home(self):
        self.mascot.set_expression("neutral")
        self.navigate_to("home")

    def _on_fade_finished(self):
        if self.fade.effect.opacity() > 0.9:
            self.stack.setCurrentIndex(self.next_index)
            if self.next_index == 1:
                self.piano_screen.setFocus()
            elif self.next_index == 2:
                self.seq_screen.setFocus()
            self.fade.fade_in()
        else:
            self.fade.hide()

    def keyPressEvent(self, event):
        current = self.stack.currentWidget()
        if current:
            current.keyPressEvent(event)
            
    def keyReleaseEvent(self, event):
        current = self.stack.currentWidget()
        if current:
            current.keyReleaseEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Global stylesheet to remove focus outlines entirely
    app.setStyleSheet("* { outline: none; }")
    window = TuneboyApp()
    window.show()
    sys.exit(app.exec_())