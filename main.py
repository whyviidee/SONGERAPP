import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from core.config import Config
from ui.main_window import MainWindow
from ui.splash import AnimatedSplash


def _check_disclaimer(config: Config) -> bool:
    """Retorna True se o utilizador já aceitou o disclaimer."""
    return bool(config.get("app", "disclaimer_accepted", default=False))


def _show_disclaimer(config: Config) -> bool:
    """Mostra o disclaimer. Retorna True se aceite, False se recusado."""
    from ui.disclaimer_dialog import DisclaimerDialog
    dlg = DisclaimerDialog()
    if dlg.exec() == DisclaimerDialog.DialogCode.Accepted:
        config.set("app", "disclaimer_accepted", True)
        return True
    return False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SONGER")
    app.setOrganizationName("SONGER")

    config = Config()

    # ── Disclaimer (first run) ─────────────────────────────────────
    if not _check_disclaimer(config):
        if not _show_disclaimer(config):
            sys.exit(0)  # Utilizador recusou — fechar

    # ── Splash animado ─────────────────────────────────────────────
    splash = AnimatedSplash()
    splash.show()
    app.processEvents()

    # ── Janela principal ───────────────────────────────────────────
    window = MainWindow()
    window.show()

    # Fechar splash com fade após 2.5s
    QTimer.singleShot(2500, splash.fade_out)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
