import sys
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QGraphicsOpacityEffect, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QFont
from config import COLORS, BITBIT_MAPS, FONT_FAMILY

# --- CUSTOM WINDOW TITLE BAR ---
class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_win = parent
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {COLORS['title_bar_bg']}; border: 1px solid {COLORS['fg_dim']};")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Title
        self.title = QLabel("// tuneboy_v1.0")
        self.title.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        self.title.setStyleSheet(f"color: {COLORS['fg']}; border:1px solid {COLORS['title_bar_border']};")
        layout.addWidget(self.title)
        
        layout.addStretch()
        
        # Buttons
        btn_style = f"""
            QPushButton {{
                color: {COLORS['fg_dim']};
                background: transparent;
                border: none;
                font-family: {FONT_FAMILY};
                font-size: 14px;
                font-weight: bold;
                outline: none;
            }}
            QPushButton:hover {{ color: {COLORS['fg']}; }}
        """
        
        btn_min = QPushButton("[-]")
        btn_max = QPushButton("[□]")
        btn_close = QPushButton("[x]")
        
        for b in (btn_min, btn_max, btn_close):
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(btn_style)
            layout.addWidget(b)
            
        btn_min.clicked.connect(self.parent_win.showMinimized)
        btn_max.clicked.connect(self.toggle_maximize)
        btn_close.clicked.connect(self.parent_win.close)
        
        self.start_pos = None

    def toggle_maximize(self):
        if self.parent_win.isMaximized():
            self.parent_win.showNormal()
        else:
            self.parent_win.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            if not self.parent_win.isMaximized():
                delta = event.globalPos() - self.start_pos
                self.parent_win.move(self.parent_win.pos() + delta)
                self.start_pos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        self.start_pos = None

# --- BITBIT MASCOT ---
class BitbitWidget(QWidget):
    # Added signals so screens.py can listen to them
    hovered = pyqtSignal()
    left = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(128, 128)
        self.pixel_size = 8
        self.current_map = "neutral"
        self.show_music_note = False
        
        self.offset_y = 0
        self.bob_direction = 1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_bob)
        self.timer.start(100) 

    # Added mouse events
    def enterEvent(self, event):
        self.hovered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)

    def set_expression(self, name):
        if name == "singing":
            self.show_music_note = True
        else:
            self.show_music_note = False
        self.offset_y = -5
        self.current_map = name if name in BITBIT_MAPS else "neutral"
        self.update()

    def _animate_bob(self):
        self.offset_y += self.bob_direction
        if abs(self.offset_y) > 2:
            self.bob_direction *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        data = BITBIT_MAPS[self.current_map]
        c = QColor(COLORS["fg"])
        
        for i, char in enumerate(data):
            if char == '1':
                x = (i % 16) * self.pixel_size
                y = (i // 16) * self.pixel_size + self.offset_y + 16
                painter.fillRect(x, int(y), self.pixel_size, self.pixel_size, c)

        if self.show_music_note:
            note_data = BITBIT_MAPS["music"]
            nc = QColor(COLORS["fg_bright"])
            for i, char in enumerate(note_data):
                if char == '1':
                    x = (i % 16) * self.pixel_size + 80
                    y = (i // 16) * self.pixel_size + self.offset_y
                    painter.fillRect(int(x), int(y), self.pixel_size, self.pixel_size, nc)

# --- STANDARD BUTTON ---
class TerminalButton(QPushButton):
    hovered = pyqtSignal()
    left = pyqtSignal()
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont(FONT_FAMILY, 14))
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus) 
        
        # FIXED: Tell the button to only take up the space it needs
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['fg_dim']};
                background-color: transparent; 
                text-align: left;
                padding: 10px;
                outline: none;
            }}
            QPushButton:hover {{ 
                color: {COLORS['fg']}; 
                border: 1px solid {COLORS['fg']};
            }}
        """)

    def enterEvent(self, event):
        self.hovered.emit()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.left.emit()
        super().leaveEvent(event)

class FadeOverlay(QWidget):
    finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()
        
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(500)
        self.anim.finished.connect(self.finished.emit)

    def fade_out(self):
        self.show()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def fade_in(self):
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()