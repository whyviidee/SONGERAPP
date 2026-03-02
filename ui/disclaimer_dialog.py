"""Disclaimer legal — aparece na primeira execução."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

BG = "#0d1117"
BG_CARD = "#161b22"
GREEN = "#1db954"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
BORDER = "#30363d"


class DisclaimerDialog(QDialog):
    def __init__(self, parent=None, read_only: bool = False):
        super().__init__(parent)
        self._read_only = read_only
        self.setWindowTitle("Aviso Legal — SONGER")
        self.setFixedSize(520, 560)
        self.setModal(True)
        if read_only:
            # Modo leitura — pode fechar com X
            self.setWindowFlags(
                Qt.WindowType.Dialog |
                Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint |
                Qt.WindowType.WindowCloseButtonHint
            )
        else:
            # Primeira execução — forçar decisão, sem X
            self.setWindowFlags(
                Qt.WindowType.Dialog |
                Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        # Título
        title = QLabel("Aviso Legal de Utilização")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        # Subtítulo
        sub = QLabel("Lê com atenção antes de continuar.")
        sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
        layout.addWidget(sub)

        # Caixa de texto com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background: {BG_CARD};
            }}
            QScrollBar:vertical {{ background: {BG_CARD}; width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: #444; border-radius: 3px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {GREEN}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background: {BG_CARD};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 16, 18, 16)
        content_layout.setSpacing(14)

        sections = [
            ("Ferramenta de uso pessoal",
             "O SONGER é uma ferramenta de software fornecida exclusivamente para uso pessoal, "
             "educacional e não comercial. Não hospedamos, distribuímos nem reproduzimos "
             "conteúdo protegido por direitos de autor."),

            ("Responsabilidade do utilizador",
             "O utilizador é o único e exclusivo responsável pela forma como utiliza esta "
             "aplicação. Ao usar o SONGER, confirmas que:\n\n"
             "• Tens direito legal de aceder e descarregar o conteúdo em questão;\n"
             "• Não usarás a app para violar direitos de autor ou propriedade intelectual;\n"
             "• Cumpres as leis de direitos autorais aplicáveis na tua jurisdição."),

            ("Direitos de autor e lei internacional",
             "A música e outros conteúdos podem ser protegidos por direitos autorais nos termos "
             "da Convenção de Berna, do DMCA (EUA), da Directiva 2001/29/CE (UE) e da "
             "Lei 9/2022 (Moçambique). O descarregamento não autorizado de conteúdo "
             "protegido pode ser ilegal na tua jurisdição."),

            ("Isenção de responsabilidade",
             "Os criadores do SONGER não se responsabilizam por qualquer uso ilegal feito "
             "desta aplicação, incluindo violações de direitos de autor, perdas de dados, "
             "ou danos directos/indirectos resultantes do seu uso. O software é fornecido "
             "'tal como está', sem garantias de qualquer tipo."),

            ("Ao continuar, confirmas que:",
             "• Tens 18 anos ou mais, ou tens autorização de um tutor;\n"
             "• Leste e compreendeste este aviso;\n"
             "• Aceitas total responsabilidade pelo uso que fazes da aplicação."),
        ]

        for heading, body in sections:
            h = QLabel(heading)
            h.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            h.setStyleSheet(f"color: {GREEN}; background: transparent;")
            content_layout.addWidget(h)

            b = QLabel(body)
            b.setWordWrap(True)
            b.setStyleSheet(f"color: {TEXT}; font-size: 12px; line-height: 1.5; background: transparent;")
            content_layout.addWidget(b)

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        if self._read_only:
            # Modo leitura — só botão fechar
            close_btn = QPushButton("Fechar")
            close_btn.setFixedHeight(40)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {GREEN};
                    color: #000;
                    border: none;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: #22c95e; }}
            """)
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)
        else:
            # Primeira execução — checkbox + aceitar/recusar
            self._checkbox = QCheckBox("Li e compreendi o aviso legal acima.")
            self._checkbox.setStyleSheet(f"""
                QCheckBox {{ color: {TEXT}; font-size: 12px; background: transparent; spacing: 8px; }}
                QCheckBox::indicator {{
                    width: 18px; height: 18px;
                    border: 2px solid {BORDER};
                    border-radius: 4px;
                    background: {BG_CARD};
                }}
                QCheckBox::indicator:checked {{
                    background: {GREEN};
                    border: 2px solid {GREEN};
                }}
            """)
            self._checkbox.stateChanged.connect(self._on_check)
            layout.addWidget(self._checkbox)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            self._decline_btn = QPushButton("Recusar e Fechar")
            self._decline_btn.setFixedHeight(40)
            self._decline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._decline_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_DIM};
                    border: 1px solid {BORDER};
                    border-radius: 20px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: #1a1a1a; color: {TEXT}; }}
            """)
            self._decline_btn.clicked.connect(self.reject)

            self._accept_btn = QPushButton("Aceitar e Continuar")
            self._accept_btn.setFixedHeight(40)
            self._accept_btn.setEnabled(False)
            self._accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._accept_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {GREEN};
                    color: #000;
                    border: none;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: #22c95e; }}
                QPushButton:disabled {{ background: #333; color: #666; }}
            """)
            self._accept_btn.clicked.connect(self.accept)

            btn_row.addWidget(self._decline_btn)
            btn_row.addWidget(self._accept_btn)
            layout.addLayout(btn_row)

    def _on_check(self, state):
        self._accept_btn.setEnabled(state == Qt.CheckState.Checked.value)
