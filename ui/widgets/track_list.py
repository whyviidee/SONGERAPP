"""Widget reutilizável de lista de tracks com botões de download e preview."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QScrollArea, QFrame, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

import os
from pathlib import Path

from ui.theme import GREEN, RED, TEXT, TEXT_SEC, TEXT_DIM, BG_MAIN


class TrackRow(QFrame):
    download_clicked = pyqtSignal(dict)
    play_clicked = pyqtSignal(dict, str)  # track, path

    def __init__(self, track: dict, index: int, parent=None):
        super().__init__(parent)
        self.track = track
        self.setFixedHeight(52)
        self.setObjectName("track_row")
        self.setStyleSheet(f"""
            QFrame#track_row {{
                background: transparent;
                border-radius: 6px;
            }}
            QFrame#track_row:hover {{
                background: #2e2e2e;
            }}
        """)
        self._build(index)

    def _build(self, index: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 12, 4)
        layout.setSpacing(8)

        # Número
        num = QLabel(str(index))
        num.setFixedWidth(30)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")

        # Info
        info = QVBoxLayout()
        info.setSpacing(1)
        title_lbl = QLabel(self.track.get("title", ""))
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        title_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        artist_lbl = QLabel(self.track.get("artist", ""))
        artist_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; background: transparent;")
        info.addWidget(title_lbl)
        info.addWidget(artist_lbl)

        # Duração
        ms = self.track.get("duration_ms", 0)
        mins, secs = divmod(ms // 1000, 60)
        dur = QLabel(f"{mins}:{secs:02d}")
        dur.setFixedWidth(40)
        dur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dur.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")

        # Progress
        self._progress = QProgressBar()
        self._progress.setFixedSize(80, 14)
        self._progress.setTextVisible(True)
        self._progress.setFormat("%p%")
        self._progress.hide()

        # Download btn
        self._dl_btn = QPushButton("↓  Download")
        self._dl_btn.setFixedHeight(30)
        self._dl_btn.setFixedWidth(100)
        self._dl_btn.setObjectName("dl_btn")
        self._dl_btn.setToolTip("Descarregar")
        self._dl_btn.clicked.connect(lambda: self.download_clicked.emit(self.track))

        # Status icon
        self._status = QLabel("")
        self._status.setFixedWidth(20)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFont(QFont("Segoe UI", 13))
        self._status.setStyleSheet("background: transparent;")

        # Play btn (visível após download)
        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(28, 28)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {GREEN};
                border: 1px solid {GREEN};
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
                padding: 0;
                padding-left: 2px;
            }}
            QPushButton:hover {{ background: {GREEN}; color: #000; }}
        """)
        self._play_btn.setToolTip("Reproduzir")
        self._play_btn.clicked.connect(self._on_play)
        self._play_btn.hide()

        # Delete btn (só visível após download)
        self._del_btn = QPushButton("🗑")
        self._del_btn.setFixedSize(26, 26)
        self._del_btn.setObjectName("ghost")
        self._del_btn.setToolTip("Apagar ficheiro do disco")
        self._del_btn.setStyleSheet("""
            QPushButton#ghost {
                background: transparent;
                color: #666;
                border: none;
                font-size: 13px;
                border-radius: 4px;
                padding: 0;
            }
            QPushButton#ghost:hover { color: #E53935; background: #2a2a2a; }
        """)
        self._del_btn.clicked.connect(self._on_delete)
        self._del_btn.hide()
        self._file_path: str = ""

        layout.addWidget(num)
        layout.addLayout(info, stretch=1)
        layout.addWidget(dur)
        layout.addWidget(self._progress)
        layout.addWidget(self._dl_btn)
        layout.addWidget(self._play_btn)
        layout.addWidget(self._del_btn)
        layout.addWidget(self._status)

    def set_progress(self, pct: float):
        self._dl_btn.hide()
        self._progress.show()
        self._progress.setValue(int(pct))

    def set_done(self, path: str = ""):
        self._file_path = path
        self._dl_btn.hide()
        self._progress.hide()
        self._status.setText("✓")
        self._status.setStyleSheet(f"color: {GREEN}; background: transparent;")
        if path and Path(path).exists():
            self._play_btn.show()
            self._del_btn.show()

    def set_failed(self, error: str = ""):
        self._dl_btn.show()
        self._dl_btn.setText("↓  Tentar again")
        self._progress.hide()
        self._status.setText("✗")
        self._status.setStyleSheet(f"color: {RED}; background: transparent;")
        self.setToolTip(f"Erro: {error[:300]}" if error else "Download falhou")

    def _on_play(self):
        if self._file_path and Path(self._file_path).exists():
            self.play_clicked.emit(self.track, self._file_path)

    def mouseDoubleClickEvent(self, event):
        if self._file_path and Path(self._file_path).exists():
            self.play_clicked.emit(self.track, self._file_path)
        super().mouseDoubleClickEvent(event)

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Apagar ficheiro",
            f"Apagar «{self.track.get('title', 'esta faixa')}» do disco?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        p = Path(self._file_path)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                self._status.setText("🔒")
                self._status.setToolTip("Ficheiro em uso — para a música antes de apagar")
                return
        self._file_path = ""
        self._play_btn.hide()
        self._del_btn.hide()
        self.reset()

    def reset(self):
        self._dl_btn.show()
        self._dl_btn.setText("↓  Download")
        self._play_btn.hide()
        self._del_btn.hide()
        self._file_path = ""
        self._progress.hide()
        self._progress.setValue(0)
        self._status.setText("")
        self.setToolTip("")


class TrackList(QWidget):
    """Lista scrollável de tracks."""
    download_clicked = pyqtSignal(dict)
    play_clicked = pyqtSignal(dict, str)  # track, path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, TrackRow] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("background: transparent; border: none;")

        self._container = QWidget()
        self._container.setObjectName("trackListContainer")
        self._container.setStyleSheet(f"QWidget#trackListContainer {{ background: {BG_MAIN}; }}")
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll)

    def set_tracks(self, tracks: list[dict]):
        self.clear()
        for i, track in enumerate(tracks, 1):
            row = TrackRow(track, i)
            row.download_clicked.connect(self.download_clicked.emit)
            row.play_clicked.connect(self.play_clicked.emit)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

            tid = track.get("id") or f"__idx_{i}"
            self._rows[tid] = row

    def get_row(self, tid: str) -> TrackRow | None:
        return self._rows.get(tid)

    def get_all_rows(self) -> dict[str, TrackRow]:
        return self._rows

    def clear(self):
        self._rows.clear()
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
