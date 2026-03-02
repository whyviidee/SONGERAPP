"""Barra inferior — player embutido + badges Spotify/Soulseek + stats."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont

from core.app_state import AppState
from ui.theme import BG_BOTTOMBAR, GREEN, TEXT, TEXT_DIM


def _fmt_ms(ms: int) -> str:
    s = max(0, ms) // 1000
    return f"{s // 60}:{s % 60:02d}"


class BottomBar(QWidget):
    open_folder_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setObjectName("bottomBar")
        self.setStyleSheet(
            f"QWidget#bottomBar {{ background-color: {BG_BOTTOMBAR}; border-top: 1.5px solid #2a2a2a; }}"
        )

        # Media player
        self._player = QMediaPlayer()
        self._audio_out = QAudioOutput()
        self._audio_out.setVolume(0.8)
        self._player.setAudioOutput(self._audio_out)
        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(self._on_duration)
        self._player.playbackStateChanged.connect(self._on_state)
        self._duration_ms = 0
        self._seeking = False

        self._build()

        AppState.instance().spotify_status_changed.connect(self._on_spotify)
        AppState.instance().soulseek_status_changed.connect(self._on_soulseek)

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        # === ESQUERDA: badges + stats ===
        left = QWidget()
        left.setFixedWidth(200)
        left.setStyleSheet("background: transparent;")
        llayout = QVBoxLayout(left)
        llayout.setContentsMargins(0, 6, 0, 6)
        llayout.setSpacing(3)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(6)

        self._sp_badge = QLabel("● Spotify")
        self._sp_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._sp_badge.setStyleSheet("color: #555; background: transparent;")
        self._sp_badge.setToolTip("Spotify: a verificar...")

        self._sl_badge = QLabel("● Soulseek")
        self._sl_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._sl_badge.setStyleSheet("color: #444; background: transparent;")
        self._sl_badge.setToolTip("Soulseek: desconectado")

        badges_row.addWidget(self._sp_badge)
        badges_row.addWidget(self._sl_badge)
        badges_row.addStretch()

        self._stats_lbl = QLabel("")
        self._stats_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")

        llayout.addLayout(badges_row)
        llayout.addWidget(self._stats_lbl)
        layout.addWidget(left)

        # Separador vertical
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #2a2a2a;")
        layout.addWidget(sep)

        # === CENTRO: player ===
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        clayout = QVBoxLayout(center)
        clayout.setContentsMargins(0, 4, 0, 4)
        clayout.setSpacing(3)

        # Controls + label
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(34, 34)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN};
                color: #000;
                border: none;
                border-radius: 17px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #5aff6e; }}
            QPushButton:disabled {{
                background: #2a2a2a;
                color: #888;
                border: 1.5px solid #444;
            }}
        """)
        self._play_btn.clicked.connect(self._toggle_play)
        self._play_btn.setEnabled(False)
        self._play_btn.setToolTip("Play / Pausa")

        self._track_lbl = QLabel("Nenhuma faixa carregada")
        self._track_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        self._track_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._stop_btn = QPushButton("■")
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: 1px solid #555;
                border-radius: 14px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: #fff; border-color: #888; }}
            QPushButton:disabled {{ color: #555; border-color: #444; }}
        """)
        self._stop_btn.clicked.connect(self._do_stop)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setToolTip("Parar")

        ctrl_row.addWidget(self._play_btn)
        ctrl_row.addWidget(self._stop_btn)
        ctrl_row.addWidget(self._track_lbl, stretch=1)

        # Progress bar
        prog_row = QHBoxLayout()
        prog_row.setSpacing(6)

        self._time_lbl = QLabel("0:00")
        self._time_lbl.setFixedWidth(34)
        self._time_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(1000)
        self._slider.setValue(0)
        self._slider.setFixedHeight(4)
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: #333;
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {GREEN};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {GREEN};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
        """)
        self._slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self._slider.sliderReleased.connect(self._on_seek)

        self._dur_lbl = QLabel("0:00")
        self._dur_lbl.setFixedWidth(34)
        self._dur_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        self._dur_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._vol_btn = QPushButton("🔊")
        self._vol_btn.setFixedSize(22, 22)
        self._vol_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 12px; } QPushButton:hover { color: #fff; }")
        self._vol_btn.clicked.connect(self._toggle_mute)
        self._vol_btn.setToolTip("Silenciar / Activar volume")

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setMinimum(0)
        self._vol_slider.setMaximum(100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(64)
        self._vol_slider.setFixedHeight(4)
        self._vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background: #333; height: 4px; border-radius: 2px; }}
            QSlider::sub-page:horizontal {{ background: #888; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: #aaa; width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; }}
        """)
        self._vol_slider.valueChanged.connect(lambda v: self._audio_out.setVolume(v / 100.0))
        self._muted = False
        self._vol_before_mute = 80

        prog_row.addWidget(self._time_lbl)
        prog_row.addWidget(self._slider, stretch=1)
        prog_row.addWidget(self._dur_lbl)
        prog_row.addWidget(self._vol_btn)
        prog_row.addWidget(self._vol_slider)

        clayout.addLayout(ctrl_row)
        clayout.addLayout(prog_row)
        layout.addWidget(center, stretch=1)

        # Separador vertical
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #2a2a2a;")
        layout.addWidget(sep2)

        # === DIREITA: folder btn ===
        folder_btn = QPushButton("📁")
        folder_btn.setFixedSize(36, 36)
        folder_btn.setObjectName("play_btn")
        folder_btn.setFont(QFont("Segoe UI", 16))
        folder_btn.setToolTip("Abrir pasta de downloads")
        folder_btn.clicked.connect(self.open_folder_clicked.emit)
        layout.addWidget(folder_btn)

    # ------------------------------------------------------------------
    # Player API
    # ------------------------------------------------------------------

    def play_track(self, path: str, title: str, artist: str):
        """Carrega e reproduz uma faixa local."""
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        label = f"{artist} — {title}" if artist else title
        self._track_lbl.setText(label)
        self._track_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px; background: transparent;")
        self._play_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)

    def stop(self):
        self._player.stop()
        self._play_btn.setText("▶")
        self._play_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._slider.setValue(0)
        self._time_lbl.setText("0:00")
        self._track_lbl.setText("Nenhuma faixa carregada")
        self._track_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")

    # ------------------------------------------------------------------
    # Player internals
    # ------------------------------------------------------------------

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _do_stop(self):
        self._player.stop()
        self._slider.setValue(0)
        self._time_lbl.setText("0:00")

    def _toggle_mute(self):
        if self._muted:
            self._audio_out.setVolume(self._vol_before_mute / 100.0)
            self._vol_slider.setValue(self._vol_before_mute)
            self._vol_btn.setText("🔊")
            self._muted = False
        else:
            self._vol_before_mute = self._vol_slider.value()
            self._audio_out.setVolume(0)
            self._vol_slider.setValue(0)
            self._vol_btn.setText("🔇")
            self._muted = True

    def _on_state(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("II")
        else:
            self._play_btn.setText("▶")

    def _on_position(self, pos: int):
        self._time_lbl.setText(_fmt_ms(pos))
        if self._duration_ms > 0 and not self._seeking:
            self._slider.setValue(int(pos * 1000 / self._duration_ms))

    def _on_duration(self, dur: int):
        self._duration_ms = dur
        self._dur_lbl.setText(_fmt_ms(dur))

    def _on_seek(self):
        self._seeking = False
        if self._duration_ms > 0:
            self._player.setPosition(int(self._slider.value() * self._duration_ms / 1000))

    # ------------------------------------------------------------------
    # Stats + badges
    # ------------------------------------------------------------------

    def update_stats(self, done: int, fail: int, pending: int, total: int):
        parts = []
        if done:
            parts.append(f"✓ {done}")
        if fail:
            parts.append(f"✗ {fail}")
        if pending:
            parts.append(f"↓ {pending}")
        if total:
            parts.append(f"/ {total}")
        self._stats_lbl.setText("  ".join(parts) if parts else "")

    def _on_spotify(self, connected: bool, username: str):
        if connected:
            tip = f"Spotify: {username}" if username else "Spotify: conectado"
            self._sp_badge.setStyleSheet(f"color: {GREEN}; background: transparent;")
        else:
            tip = "Spotify: desconectado"
            self._sp_badge.setStyleSheet("color: #E53935; background: transparent;")
        self._sp_badge.setToolTip(tip)

    def _on_soulseek(self, connected: bool):
        if connected:
            self._sl_badge.setStyleSheet(f"color: {GREEN}; background: transparent;")
            self._sl_badge.setToolTip("Soulseek: conectado")
        else:
            self._sl_badge.setStyleSheet("color: #444; background: transparent;")
            self._sl_badge.setToolTip("Soulseek: desconectado")
