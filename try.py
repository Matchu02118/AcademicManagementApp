from PyQt6.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve
import sys

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("QPushButton { border: 2px solid #444; padding: 10px; }")
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.original_geometry = self.geometry()
        
        # Enable mouse tracking
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.animate(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate(False)
        super().leaveEvent(event)

    def animate(self, hovering):
        self.original_geometry = self.geometry()
        target_geometry = self.original_geometry.adjusted(-5, -5, 5, 5) if hovering else self.original_geometry

        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(target_geometry)
        self.animation.start()


app = QApplication(sys.argv)

window = QWidget()
layout = QVBoxLayout(window)

button = AnimatedButton("Hover me!")
layout.addWidget(button)

window.show()
sys.exit(app.exec())
