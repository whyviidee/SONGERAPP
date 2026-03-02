"""Header rico com album art, info e controles de download."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl

from ui.theme import GREEN, TEXT, TEXT_SEC, TEXT_DIM, BG_CARD


class AlbumHeader(QFrame):
    download_all_clicked = pyqtSignal(str, str)  # fmt, source

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(150)
        self.setObjectName("album_header")
        self.setStyleSheet(f"""
            QFrame#album_header {{
                background-color: {BG_CARD};
                border-radius: 10px;
            }}
        """)
        self._net = QNetworkAccessManager(self)
        self._build()
        self.hide()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(18)

        # Cover art
        self._cover = QLabel()
        self._cover.setFixedSize(118, 118)
        self._cover.setStyleSheet("background: #333; border-radius: 6px;")
        self._cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover.setText("🎵")
        self._cover.setFont(QFont("Segoe UI", 28))
        layout.addWidget(self._cover)

        # Info
        info = QVBoxLayout()
        info.setSpacing(4)

        self._type_lbl = QLabel("PLAYLIST")
        self._type_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent;")

        self._name_lbl = QLabel("")
        self._name_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._name_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        self._name_lbl.setWordWrap(True)

        self._meta_lbl = QLabel("")
        self._meta_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")

        # Controles
        controls = QHBoxLayout()
        controls.setSpacing(10)

        self._dl_all_btn = QPushButton("Download All")
        self._dl_all_btn.setFixedHeight(36)
        self._dl_all_btn.setFixedWidth(150)
        self._dl_all_btn.clicked.connect(self._on_download_all)
        self._dl_all_btn.setToolTip("Descarregar todas as faixas")

        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["MP3 320", "MP3 256", "MP3 128", "FLAC"])
        self._fmt_combo.setFixedHeight(32)
        self._fmt_combo.setToolTip("Formato de áudio")

        self._src_combo = QComboBox()
        self._src_combo.addItems(["Híbrido", "YouTube", "Soulseek"])
        self._src_combo.setFixedHeight(32)
        self._src_combo.setToolTip("Fonte de download")

        controls.addWidget(self._dl_all_btn)
        controls.addWidget(self._fmt_combo)
        controls.addWidget(self._src_combo)
        controls.addStretch()

        info.addWidget(self._type_lbl)
        info.addWidget(self._name_lbl)
        info.addWidget(self._meta_lbl)
        info.addStretch()
        info.addLayout(controls)

        layout.addLayout(info, stretch=1)

    def set_info(self, name: str, subtitle: str, cover_url: str, kind: str = "PLAYLIST", track_count: int = 0):
        self._type_lbl.setText(kind.upper())
        self._name_lbl.setText(name)

        meta_parts = [subtitle] if subtitle else []
        if track_count:
            meta_parts.append(f"{track_count} tracks")
        self._meta_lbl.setText("  •  ".join(meta_parts))

        if cover_url:
            self._load_cover(cover_url)

        self.show()

    def get_format(self) -> str:
        mapping = {"MP3 320": "mp3_320", "MP3 256": "mp3_256", "MP3 128": "mp3_128", "FLAC": "flac"}
        return mapping.get(self._fmt_combo.currentText(), "mp3_320")

    def get_source(self) -> str:
        mapping = {"Híbrido": "hybrid", "YouTube": "youtube", "Soulseek": "soulseek"}
        return mapping.get(self._src_combo.currentText(), "hybrid")

    def _on_download_all(self):
        self.download_all_clicked.emit(self.get_format(), self.get_source())

    def _load_cover(self, url: str):
        reply = self._net.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_cover_loaded(reply))

    def _on_cover_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self._cover.setPixmap(
                    pixmap.scaled(118, 118, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
                self._cover.setStyleSheet("border-radius: 6px;")
        reply.deleteLater()
