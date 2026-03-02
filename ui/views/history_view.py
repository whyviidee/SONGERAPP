"""Vista Histórico — mostra downloads passados."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.history import DownloadHistory
from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, GREEN, BG_CARD, BG_MAIN


class HistoryCard(QFrame):
    reload_clicked = pyqtSignal(str)  # URL

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self._entry = entry
        self.setFixedHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("history_card")
        self.setStyleSheet(f"""
            QFrame#history_card {{
                background: {BG_CARD};
                border-radius: 8px;
                border: 1px solid transparent;
            }}
            QFrame#history_card:hover {{
                background: #363636;
                border: 1px solid #444;
            }}
        """)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(self._entry.get("name", "Sem nome"))
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        name.setStyleSheet(f"color: {TEXT}; background: transparent;")
        name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        done = self._entry.get("done_count", 0)
        total = self._entry.get("tracks_count", 0)
        fail = self._entry.get("fail_count", 0)
        fmt = self._entry.get("format", "")
        date = self._entry.get("date", "")[:16].replace("T", " ")

        meta_parts = [f"✓ {done}/{total}"]
        if fail:
            meta_parts.append(f"✗ {fail}")
        meta_parts.append(fmt.upper().replace("_", " "))
        meta_parts.append(date)

        meta = QLabel("  •  ".join(meta_parts))
        meta.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; background: transparent;")
        meta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        info.addWidget(name)
        info.addWidget(meta)
        layout.addLayout(info, stretch=1)

        # Re-download
        btn = QPushButton("▶")
        btn.setFixedSize(32, 32)
        btn.setObjectName("dl_btn")
        btn.setToolTip("Re-carregar esta playlist")
        btn.clicked.connect(lambda: self.reload_clicked.emit(self._entry.get("url", "")))
        layout.addWidget(btn)

    def mousePressEvent(self, _event):
        url = self._entry.get("url", "")
        if url:
            self.reload_clicked.emit(url)


class HistoryView(QWidget):
    reload_url = pyqtSignal(str)  # URL para recarregar na search view

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = DownloadHistory()
        self.setObjectName("historyView")
        self.setStyleSheet(f"QWidget#historyView {{ background: {BG_MAIN}; }}")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 8)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Histórico")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")

        clear_btn = QPushButton("Limpar tudo")
        clear_btn.setObjectName("secondary")
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self._clear_all)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        self._list_widget = QWidget()
        self._list_widget.setObjectName("historyList")
        self._list_widget.setStyleSheet(f"QWidget#historyList {{ background: {BG_MAIN}; }}")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, stretch=1)

        # Empty state
        self._empty = QLabel("Nenhum download no histórico.\n\nOs teus downloads aparecerão aqui.")
        self._empty.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty)

    def refresh(self):
        # Limpar
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        entries = self._history.get_all()
        if not entries:
            self._empty.show()
            return

        self._empty.hide()
        for entry in entries:
            card = HistoryCard(entry)
            card.reload_clicked.connect(self.reload_url.emit)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)

    def add_entry(self, url: str, name: str, tracks_count: int, done: int, fail: int, fmt: str):
        self._history.add(url, name, tracks_count, done, fail, fmt)

    def _clear_all(self):
        self._history.clear()
        self.refresh()
