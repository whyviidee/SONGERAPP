from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QHBoxLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class FfmpegDownloadWorker(QThread):
    progress = pyqtSignal(float)
    success = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        from core.ffmpeg_manager import download_ffmpeg
        ok = download_ffmpeg(progress_cb=lambda p: self.progress.emit(p))
        if ok:
            self.success.emit()
        else:
            self.error.emit("Falhou o download do ffmpeg. Verifica a ligação à internet.")


class FfmpegSetupDialog(QDialog):
    """Diálogo de primeiro arranque — descarrega ffmpeg automaticamente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SONGER — Configuração inicial")
        self.setFixedSize(420, 220)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Configuração inicial")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #1db954;")
        layout.addWidget(title)

        info = QLabel(
            "O SONGER precisa do <b>ffmpeg</b> para converter áudio.\n"
            "Vamos descarregá-lo agora (~15MB). Acontece só uma vez."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #ccc; font-size: 12px;")
        layout.addWidget(info)

        self._bar = QProgressBar()
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)
        self._bar.hide()
        layout.addWidget(self._bar)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        btn_row = QHBoxLayout()
        self._dl_btn = QPushButton("Descarregar ffmpeg")
        self._dl_btn.clicked.connect(self._start_download)
        self._skip_btn = QPushButton("Ignorar (só YouTube sem conversão)")
        self._skip_btn.setObjectName("secondary")
        self._skip_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._skip_btn)
        btn_row.addWidget(self._dl_btn)
        layout.addLayout(btn_row)

    def _start_download(self):
        self._dl_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._bar.show()
        self._status.setText("A descarregar ffmpeg...")

        self._worker = FfmpegDownloadWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.success.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, pct: float):
        self._bar.setValue(int(pct))
        self._status.setText(f"A descarregar... {int(pct)}%")

    def _on_success(self):
        self._status.setText("✓ ffmpeg instalado com sucesso!")
        self._status.setStyleSheet("color: #1db954; font-size: 11px;")
        self.accept()

    def _on_error(self, msg: str):
        self._status.setText(f"✗ {msg}")
        self._status.setStyleSheet("color: #e74c3c; font-size: 11px;")
        self._dl_btn.setEnabled(True)
        self._skip_btn.setEnabled(True)
