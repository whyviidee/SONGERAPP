from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QFileDialog, QMessageBox, QFormLayout, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QClipboard
from PyQt6.QtWidgets import QApplication

from core.config import Config
from ui.theme import STYLE


class CodeExchangeWorker(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, client_id, client_secret, pasted_url):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.pasted_url = pasted_url

    def run(self):
        try:
            from core.spotify import SpotifyClient
            sp = SpotifyClient(self.client_id, self.client_secret)
            sp.connect_with_code(self.pasted_url)
            self.success.emit()
        except Exception as e:
            self.error.emit(str(e))


class SlskTestWorker(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, api_key, username, password):
        super().__init__()
        self.url = url
        self.api_key = api_key
        self.username = username
        self.password = password

    def run(self):
        try:
            from core.soulseek import SoulseekClient
            c = SoulseekClient(self.url, self.api_key, self.username, self.password)
            c.connect()
            self.success.emit()
        except Exception as e:
            self.error.emit(str(e))


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Definições — SONGER")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.addTab(self._spotify_tab(), "Spotify")
        tabs.addTab(self._download_tab(), "Download")
        tabs.addTab(self._soulseek_tab(), "Soulseek")
        layout.addWidget(tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Guardar")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Spotify tab — flow manual, sem servidor local
    # ------------------------------------------------------------------

    def _spotify_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # --- Passo 1 ---
        step1_lbl = QLabel("<b>Passo 1</b> — Criar app no Spotify Developer Dashboard")
        step1_lbl.setStyleSheet("color: #fff; font-size: 13px; margin-bottom: 2px;")
        layout.addWidget(step1_lbl)

        step1_row = QHBoxLayout()
        step1_row.setSpacing(8)
        dash_btn = QPushButton("Abrir Spotify Developer Dashboard")
        dash_btn.setObjectName("secondary")
        dash_btn.setToolTip("Abre developer.spotify.com/dashboard no browser")
        dash_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://developer.spotify.com/dashboard")))
        step1_row.addWidget(dash_btn)
        step1_row.addStretch()
        layout.addLayout(step1_row)

        step1_info = QLabel(
            "Na app criada, vai a <b>Settings</b> e em <b>Redirect URIs</b> adiciona este URI:"
        )
        step1_info.setWordWrap(True)
        step1_info.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(step1_info)

        uri_row = QHBoxLayout()
        uri_row.setSpacing(6)
        uri_lbl = QLabel("<code>https://open.spotify.com</code>")
        uri_lbl.setStyleSheet("color: #1db954; font-size: 11px; background: #1e1e1e; padding: 4px 8px; border-radius: 4px;")
        _small_btn_style = "QPushButton { border-radius: 6px; padding: 4px 14px; } QPushButton:hover { background: #555; border-color: #888; }"
        copy_uri_btn = QPushButton("Copiar")
        copy_uri_btn.setObjectName("secondary")
        copy_uri_btn.setFixedHeight(30)
        copy_uri_btn.setMinimumWidth(80)
        copy_uri_btn.setStyleSheet(_small_btn_style)
        copy_uri_btn.setToolTip("Copiar redirect URI para o clipboard")
        copy_uri_btn.clicked.connect(lambda: (
            QApplication.clipboard().setText("https://open.spotify.com"),
            copy_uri_btn.setText("✓ Copiado"),
            copy_uri_btn.setStyleSheet(_small_btn_style + " QPushButton { color: #1db954; }"),
        ))
        uri_row.addWidget(uri_lbl)
        uri_row.addWidget(copy_uri_btn)
        uri_row.addStretch()
        layout.addLayout(uri_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #333;")
        layout.addWidget(sep1)

        # --- Passo 2 ---
        step2_lbl = QLabel("<b>Passo 2</b> — Colar Client ID e Client Secret")
        step2_lbl.setStyleSheet("color: #fff; font-size: 13px; margin-bottom: 2px;")
        layout.addWidget(step2_lbl)

        form = QFormLayout()
        form.setSpacing(8)

        self._sp_id = QLineEdit()
        self._sp_id.setPlaceholderText("Client ID")
        form.addRow("Client ID:", self._sp_id)

        self._sp_secret = QLineEdit()
        self._sp_secret.setPlaceholderText("Client Secret")
        self._sp_secret.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Client Secret:", self._sp_secret)

        layout.addLayout(form)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #333;")
        layout.addWidget(sep2)

        # --- Passo 3 ---
        step3_lbl = QLabel("<b>Passo 3</b> — Autenticar conta Spotify")
        step3_lbl.setStyleSheet("color: #fff; font-size: 13px; margin-bottom: 2px;")
        layout.addWidget(step3_lbl)

        open_btn = QPushButton("Abrir login Spotify no browser")
        open_btn.setFixedHeight(40)
        open_btn.clicked.connect(self._open_spotify_browser)
        open_btn.setToolTip("Abre o browser para fazeres login no Spotify")
        layout.addWidget(open_btn)

        paste_lbl = QLabel("Depois de fazer login, copia o URL completo da barra do browser e cola aqui:")
        paste_lbl.setWordWrap(True)
        paste_lbl.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 4px;")
        layout.addWidget(paste_lbl)

        url_row = QHBoxLayout()
        self._sp_code_input = QLineEdit()
        self._sp_code_input.setPlaceholderText("https://open.spotify.com?code=AQC...")
        confirm_btn = QPushButton("Confirmar")
        confirm_btn.setFixedHeight(34)
        confirm_btn.setMinimumWidth(100)
        confirm_btn.setStyleSheet("QPushButton { border-radius: 6px; padding: 4px 16px; }")
        confirm_btn.clicked.connect(self._confirm_spotify_code)
        confirm_btn.setToolTip("Verifica o código e liga ao Spotify")
        url_row.addWidget(self._sp_code_input)
        url_row.addWidget(confirm_btn)
        layout.addLayout(url_row)

        self._sp_status = QLabel("")
        self._sp_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._sp_status)

        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Download tab
    # ------------------------------------------------------------------

    def _download_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        path_row = QHBoxLayout()
        self._dl_path = QLineEdit()
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(36)
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(self._dl_path)
        path_row.addWidget(browse_btn)
        form.addRow("Pasta destino:", path_row)

        self._dl_concurrent = QSpinBox()
        self._dl_concurrent.setRange(1, 12)
        self._dl_concurrent.setValue(6)
        form.addRow("Downloads simultâneos:", self._dl_concurrent)

        self._dl_organize = QCheckBox("Organizar em Artista / Álbum")
        form.addRow("", self._dl_organize)

        layout.addLayout(form)
        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Soulseek tab
    # ------------------------------------------------------------------

    def _soulseek_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info = QLabel(
            "Soulseek permite downloads de alta qualidade (FLAC, MP3 320).\n"
            "Precisas do <b>slskd</b> a correr localmente. Cria conta em <b>slsknet.org</b> (gratuito)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        self._slsk_enabled = QCheckBox("Activar Soulseek")
        layout.addWidget(self._slsk_enabled)

        form = QFormLayout()
        form.setSpacing(8)

        self._slsk_url = QLineEdit()
        self._slsk_url.setPlaceholderText("http://localhost:5030")
        form.addRow("slskd URL:", self._slsk_url)

        self._slsk_apikey = QLineEdit()
        self._slsk_apikey.setPlaceholderText("API Key (opcional)")
        self._slsk_apikey.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key:", self._slsk_apikey)

        self._slsk_user = QLineEdit()
        self._slsk_user.setPlaceholderText("Username Soulseek")
        form.addRow("Username:", self._slsk_user)

        self._slsk_pass = QLineEdit()
        self._slsk_pass.setPlaceholderText("Password Soulseek")
        self._slsk_pass.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self._slsk_pass)

        layout.addLayout(form)

        test_btn = QPushButton("Testar ligação ao slskd")
        test_btn.setFixedHeight(40)
        test_btn.setObjectName("secondary")
        test_btn.clicked.connect(self._test_soulseek)
        layout.addWidget(test_btn)

        self._slsk_status = QLabel("")
        self._slsk_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._slsk_status)

        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _load_values(self):
        self._sp_id.setText(self._config.get("spotify", "client_id", default=""))
        self._sp_secret.setText(self._config.get("spotify", "client_secret", default=""))

        from core.spotify import SpotifyClient, CACHE_PATH
        if CACHE_PATH.exists():
            self._sp_status.setText("✓ Spotify ligado")
            self._sp_status.setStyleSheet("color: #1db954; font-weight: bold;")

        self._dl_path.setText(self._config.get("download", "path", default=str(Path.home() / "Music" / "SONGER")))
        self._dl_concurrent.setValue(self._config.get("download", "max_concurrent", default=2))
        self._dl_organize.setChecked(self._config.get("download", "organize", default=True))

        self._slsk_enabled.setChecked(self._config.get("soulseek", "enabled", default=False))
        self._slsk_url.setText(self._config.get("soulseek", "slskd_url", default="http://localhost:5030"))
        self._slsk_apikey.setText(self._config.get("soulseek", "slskd_api_key", default=""))
        self._slsk_user.setText(self._config.get("soulseek", "username", default=""))
        self._slsk_pass.setText(self._config.get("soulseek", "password", default=""))

    def _save(self):
        self._config.set("spotify", "client_id", self._sp_id.text().strip())
        self._config.set("spotify", "client_secret", self._sp_secret.text().strip())

        self._config.set("download", "path", self._dl_path.text().strip())
        self._config.set("download", "max_concurrent", self._dl_concurrent.value())
        self._config.set("download", "organize", self._dl_organize.isChecked())

        self._config.set("soulseek", "enabled", self._slsk_enabled.isChecked())
        self._config.set("soulseek", "slskd_url", self._slsk_url.text().strip())
        self._config.set("soulseek", "slskd_api_key", self._slsk_apikey.text().strip())
        self._config.set("soulseek", "username", self._slsk_user.text().strip())
        self._config.set("soulseek", "password", self._slsk_pass.text().strip())

        self.accept()

    def _open_spotify_browser(self):
        client_id = self._sp_id.text().strip()
        client_secret = self._sp_secret.text().strip()
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Falta info", "Mete o Client ID e Client Secret primeiro.")
            return
        # Save credentials before opening browser
        self._config.set("spotify", "client_id", client_id)
        self._config.set("spotify", "client_secret", client_secret)

        from core.spotify import SpotifyClient
        sp = SpotifyClient(client_id, client_secret)
        sp.open_browser_for_auth()
        self._sp_status.setText("Browser aberto. Faz login e cola o URL abaixo.")
        self._sp_status.setStyleSheet("color: #aaa;")

    def _confirm_spotify_code(self):
        pasted = self._sp_code_input.text().strip()
        if not pasted:
            QMessageBox.warning(self, "URL em falta", "Cola o URL do browser primeiro.")
            return

        client_id = self._sp_id.text().strip()
        client_secret = self._sp_secret.text().strip()
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Falta info", "Mete o Client ID e Client Secret primeiro.")
            return

        self._sp_status.setText("A verificar...")
        self._sp_status.setStyleSheet("color: #aaa;")

        self._code_worker = CodeExchangeWorker(client_id, client_secret, pasted)
        self._code_worker.success.connect(self._on_auth_ok)
        self._code_worker.error.connect(self._on_auth_err)
        self._code_worker.start()

    def _on_auth_ok(self):
        self._sp_status.setText("✓ Ligado ao Spotify!")
        self._sp_status.setStyleSheet("color: #1db954; font-weight: bold;")
        self._sp_code_input.clear()

    def _on_auth_err(self, msg):
        self._sp_status.setText(f"✗ Erro: {msg}")
        self._sp_status.setStyleSheet("color: #e74c3c;")

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Escolhe pasta de destino", self._dl_path.text())
        if folder:
            self._dl_path.setText(folder)

    def _test_soulseek(self):
        self._slsk_status.setText("A testar...")
        self._slsk_status.setStyleSheet("color: #aaa;")
        self._slsk_worker = SlskTestWorker(
            self._slsk_url.text().strip() or "http://localhost:5030",
            self._slsk_apikey.text().strip(),
            self._slsk_user.text().strip(),
            self._slsk_pass.text().strip(),
        )
        self._slsk_worker.success.connect(lambda: (
            self._slsk_status.setText("✓ slskd ligado!"),
            self._slsk_status.setStyleSheet("color: #1db954; font-weight: bold;")
        ))
        self._slsk_worker.error.connect(lambda e: (
            self._slsk_status.setText(f"✗ {e}"),
            self._slsk_status.setStyleSheet("color: #e74c3c;")
        ))
        self._slsk_worker.start()
