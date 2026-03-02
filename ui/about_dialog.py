"""Diálogo Sobre SONGER."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QPixmap, QDesktopServices

from ui.theme import BG_MAIN, TEXT, TEXT_DIM

GREEN = "#1db954"
BG_CARD = "#1e1e1e"


def _asset(name: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).parents[1]))
    return base / 'assets' / name


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre SONGER")
        self.setFixedSize(340, 470)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG_MAIN};
            }}
        """)
        self._build()

    def _open_disclaimer(self):
        from ui.disclaimer_dialog import DisclaimerDialog
        dlg = DisclaimerDialog(self, read_only=True)
        dlg.exec()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 28)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Logo
        logo_path = _asset("logo.png")
        if logo_path.exists():
            pm = QPixmap(str(logo_path)).scaled(
                100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_lbl = QLabel()
            logo_lbl.setPixmap(pm)
            logo_lbl.setFixedSize(100, 100)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
            layout.addSpacing(16)

        # Nome
        name_lbl = QLabel("SONGER")
        name_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        name_font = name_lbl.font()
        name_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet(f"color: {GREEN}; background: transparent;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_lbl)
        layout.addSpacing(6)

        # Versão
        ver_lbl = QLabel("v1.2.0")
        ver_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver_lbl)
        layout.addSpacing(20)

        # Separador
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: #2a2a2a;")
        layout.addWidget(sep)
        layout.addSpacing(20)

        # Descrição
        desc = QLabel("Music downloader para Spotify.\nDescarrega em MP3, FLAC e OGG\ncom metadata automático.")
        desc.setStyleSheet(f"color: {TEXT}; font-size: 12px; line-height: 1.6; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(20)

        # Créditos
        credits = QLabel("Feito em Moçambique")
        credits.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)

        layout.addStretch()

        # Aviso legal breve
        legal = QLabel("Uso pessoal. O utilizador é responsável pelo cumprimento das leis de direitos de autor.")
        legal.setWordWrap(True)
        legal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legal.setStyleSheet(f"color: #3a3a3a; font-size: 9px; background: transparent; padding: 0 10px;")
        layout.addWidget(legal)
        layout.addSpacing(6)

        # Botão aviso legal
        disclaimer_btn = QPushButton("Ver Aviso Legal")
        disclaimer_btn.setFixedHeight(36)
        disclaimer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        disclaimer_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: 1px solid #3a3a3a;
                border-radius: 18px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #2a2a2a; color: #fff; border-color: #666; }}
        """)
        disclaimer_btn.clicked.connect(self._open_disclaimer)
        layout.addWidget(disclaimer_btn)
        layout.addSpacing(6)

        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.setFixedHeight(40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN};
                color: #000;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #22c95e; }}
            QPushButton:pressed {{ background: #179945; }}
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
