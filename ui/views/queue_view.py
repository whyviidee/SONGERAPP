"""Vista de downloads (queue) — mostra downloads activos + pendentes + concluídos."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QProgressBar, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont

from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, GREEN, RED, BG_MAIN


class QueueItem(QFrame):
    cancel_requested = pyqtSignal(str)  # track_id

    def __init__(self, track: dict, parent=None):
        super().__init__(parent)
        self.track = track
        self._done = False
        self._failed = False
        self._file_path = ""
        self.setFixedHeight(44)
        self.setObjectName("queue_item")
        self.setStyleSheet(f"""
            QFrame#queue_item {{
                background: transparent;
                border-radius: 6px;
            }}
            QFrame#queue_item:hover {{
                background: #2e2e2e;
            }}
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        self._icon = QLabel("|")
        self._icon.setFixedWidth(18)
        self._icon.setStyleSheet(f"color: {GREEN}; font-size: 15px; background: transparent;")

        name = f"{self.track.get('artist', '')} — {self.track.get('title', '')}"
        lbl = QLabel(name)
        lbl.setStyleSheet(f"font-size: 12px; color: #ddd; background: transparent;")
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._bar = QProgressBar()
        self._bar.setFixedWidth(100)
        self._bar.setFixedHeight(5)
        self._bar.setTextVisible(False)

        self._pct = QLabel("0%")
        self._pct.setFixedWidth(40)
        self._pct.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM}; background: transparent;")
        self._pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._cancel_btn = QPushButton("✕")
        self._cancel_btn.setFixedSize(22, 22)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover { color: #E53935; background: #2a2a2a; }
        """)
        self._cancel_btn.clicked.connect(
            lambda: self.cancel_requested.emit(self.track.get("id", ""))
        )
        self._cancel_btn.setToolTip("Cancelar download")

        layout.addWidget(self._icon)
        layout.addWidget(lbl, stretch=1)
        layout.addWidget(self._bar)
        layout.addWidget(self._pct)
        layout.addWidget(self._cancel_btn)

        self._spin_chars = ["|", "/", "-", "\\"]
        self._spin_i = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._spin)
        self._timer.start(350)

    def _spin(self):
        if not self._done and not self._failed:
            self._spin_i = (self._spin_i + 1) % len(self._spin_chars)
            self._icon.setText(self._spin_chars[self._spin_i])

    def set_progress(self, pct: float):
        self._bar.setValue(int(pct))
        self._pct.setText(f"{int(pct)}%")

    def set_done(self, path: str = ""):
        self._done = True
        self._file_path = path
        self._timer.stop()
        self._icon.setText("✓")
        self._icon.setStyleSheet(f"color: {GREEN}; font-size: 15px; background: transparent;")
        self._bar.setValue(100)
        self._pct.setText("✓")
        self._pct.setStyleSheet(f"color: {GREEN}; font-size: 13px; background: transparent;")
        self._cancel_btn.hide()

    def set_failed(self, error: str = ""):
        self._failed = True
        self._timer.stop()
        self._icon.setText("✗")
        self._icon.setStyleSheet(f"color: {RED}; font-size: 15px; background: transparent;")
        self._pct.setText("✗")
        self._pct.setStyleSheet(f"color: {RED}; font-size: 13px; background: transparent;")
        self._cancel_btn.hide()
        if error:
            self.setToolTip(f"Erro: {error[:300]}")

    def set_cancelled(self):
        self._done = True
        self._timer.stop()
        self._icon.setText("–")
        self._icon.setStyleSheet("color: #888; font-size: 15px; background: transparent;")
        self._bar.setValue(0)
        self._pct.setText("–")
        self._pct.setStyleSheet("font-size: 11px; color: #888; background: transparent;")
        self._cancel_btn.hide()

    def reset(self):
        self._done = False
        self._failed = False
        self._icon.setText("|")
        self._icon.setStyleSheet(f"color: {GREEN}; font-size: 15px; background: transparent;")
        self._bar.setValue(0)
        self._pct.setText("0%")
        self._pct.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM}; background: transparent;")
        self.setToolTip("")
        self._timer.start(350)


class QueueView(QWidget):
    cancel_track = pyqtSignal(str)   # track_id
    cancel_all = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: dict[str, QueueItem] = {}
        self.setObjectName("queueView")
        self.setStyleSheet(f"QWidget#queueView {{ background: {BG_MAIN}; }}")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 8)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Downloads")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")

        self._clear_btn = QPushButton("Limpar concluídos")
        self._clear_btn.setObjectName("secondary")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.clicked.connect(self.clear_done)

        self._cancel_all_btn = QPushButton("✕  Cancelar tudo")
        self._cancel_all_btn.setObjectName("secondary")
        self._cancel_all_btn.setFixedHeight(32)
        self._cancel_all_btn.clicked.connect(self.cancel_all.emit)

        header.addWidget(title)
        header.addWidget(self._count_lbl)
        header.addStretch()
        header.addWidget(self._cancel_all_btn)
        header.addWidget(self._clear_btn)
        layout.addLayout(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        self._list_widget = QWidget()
        self._list_widget.setObjectName("queueList")
        self._list_widget.setStyleSheet(f"QWidget#queueList {{ background: {BG_MAIN}; }}")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, stretch=1)
        self._scroll = scroll

        # Empty state
        self._empty = QLabel("Nenhum download em curso.\n\nVai a 🔍 Pesquisar para encontrar música.")
        self._empty.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty)

    def add_item(self, tid: str, track: dict):
        if tid in self._items:
            self._items[tid].reset()
            return
        item = QueueItem(track)
        item.cancel_requested.connect(self.cancel_track.emit)
        self._items[tid] = item
        self._list_layout.insertWidget(self._list_layout.count() - 1, item)
        self._empty.hide()
        self._update_count()
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def get_item(self, tid: str) -> QueueItem | None:
        return self._items.get(tid)

    def clear_done(self):
        for tid, item in list(self._items.items()):
            if item._done or item._failed:
                item.setParent(None)
                item.deleteLater()
                del self._items[tid]
        if not self._items:
            self._empty.show()
        self._update_count()

    def _update_count(self):
        done = sum(1 for i in self._items.values() if i._done)
        fail = sum(1 for i in self._items.values() if i._failed)
        active = len(self._items) - done - fail
        parts = []
        if active:
            parts.append(f"{active} activos")
        if done:
            parts.append(f"{done} concluídos")
        if fail:
            parts.append(f"{fail} falhados")
        self._count_lbl.setText("  •  ".join(parts))
