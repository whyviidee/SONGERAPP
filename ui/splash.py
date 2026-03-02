"""Splash screen animado — waveform equalizer."""

import math
import sys
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap, QPen, QRadialGradient


def _asset(name: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).parents[1]))
    return base / 'assets' / name


W, H = 380, 370


class AnimatedSplash(QWidget):
    def __init__(self):
        super().__init__()
        self._frame = 0
        self._opacity = 0.0
        self._closing = False
        self._fade_timer = None

        # Carregar logo
        logo_path = _asset("logo.png")
        self._logo = None
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            if not pm.isNull():
                self._logo = pm.scaled(
                    120, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

        self.setFixedSize(W, H)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Centrar no ecrã
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - W) // 2,
            (screen.height() - H) // 2,
        )

        # Timer de animação ~30fps
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(33)

    # ------------------------------------------------------------------

    def _tick(self):
        self._frame += 1
        if not self._closing and self._opacity < 1.0:
            self._opacity = min(1.0, self._opacity + 0.06)
        self.update()

    def fade_out(self):
        self._closing = True
        self._anim_timer.stop()
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._do_fade)
        self._fade_timer.start(25)

    def _do_fade(self):
        self._opacity = max(0.0, self._opacity - 0.1)
        self.update()
        if self._opacity <= 0.0:
            self._fade_timer.stop()
            self.close()

    # ------------------------------------------------------------------

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)

        t = self._frame / 30.0

        # ── Fundo escuro arredondado ───────────────────────────────
        painter.setBrush(QColor("#0d1117"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(6, 6, W - 12, H - 12, 22, 22)

        # Borda subtil verde
        pen = QPen(QColor(29, 185, 84, 40))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(6, 6, W - 12, H - 12, 22, 22)
        painter.setPen(Qt.PenStyle.NoPen)

        # ── Glow radial por baixo do logo ──────────────────────────
        glow_y = 150
        pulse = 0.6 + 0.4 * math.sin(t * 1.8)
        grad = QRadialGradient(W / 2, glow_y, int(90 * pulse))
        grad.setColorAt(0, QColor(29, 185, 84, int(55 * pulse)))
        grad.setColorAt(0.5, QColor(29, 185, 84, int(20 * pulse)))
        grad.setColorAt(1, QColor(29, 185, 84, 0))
        painter.setBrush(grad)
        painter.drawEllipse(int(W / 2 - 100), glow_y - 100, 200, 200)

        # ── Logo ───────────────────────────────────────────────────
        logo_y = 38
        if self._logo and not self._logo.isNull():
            lw = self._logo.width()
            lh = self._logo.height()
            painter.drawPixmap((W - lw) // 2, logo_y, self._logo)

        # ── Barras equalizador animadas ────────────────────────────
        bar_count = 20
        bar_w = 5
        bar_gap = 3
        total_w = bar_count * (bar_w + bar_gap) - bar_gap
        bx = (W - total_w) // 2
        base_y = 220
        max_h = 32
        min_h = 5

        for i in range(bar_count):
            # Cada barra tem fase e amplitude únicas — efeito orgânico
            phase = i * 0.42
            amp = 0.5 + 0.5 * math.sin(i * 0.8)
            h_bar = int(min_h + (max_h - min_h) * amp * (0.5 + 0.5 * math.sin(t * 4.0 + phase)))
            h_bar = max(min_h, h_bar)

            x = bx + i * (bar_w + bar_gap)

            # Cor: verde com brilho a pulsar por barra
            alpha = int(160 + 80 * math.sin(t * 2.5 + i * 0.35))
            bright = int(185 + 40 * math.sin(t * 3.0 + i * 0.5))
            bright = min(255, max(100, bright))
            painter.setBrush(QColor(29, bright, 84, alpha))
            painter.drawRoundedRect(x, base_y - h_bar, bar_w, h_bar, 2, 2)

        # ── SONGER texto ───────────────────────────────────────────
        font = QFont("Segoe UI", 17, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 7)
        painter.setFont(font)
        painter.setPen(QColor("#1db954"))
        painter.drawText(0, 235, W, 34, Qt.AlignmentFlag.AlignHCenter, "SONGER")

        # ── "A carregar..." com dots animados ─────────────────────
        dot_count = (self._frame // 18 % 3) + 1
        dots = "•" * dot_count
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor("#4a5568"))
        painter.drawText(0, 272, W, 22, Qt.AlignmentFlag.AlignHCenter, f"A carregar  {dots}")

        painter.end()
