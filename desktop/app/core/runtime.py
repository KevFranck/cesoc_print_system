from __future__ import annotations

import logging
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar

from PySide6.QtWidgets import QApplication, QMessageBox


LOGGER = logging.getLogger("cesoc.desktop")
F = TypeVar("F", bound=Callable[..., object])


def setup_runtime_logging(app_name: str) -> Path:
    """Configure un log fichier persistant pour les applis desktop.

    En production Windows, un `.exe` peut sinon sembler "disparaitre" sans que
    l'on sache pourquoi. Ce log garde une trace des exceptions et des erreurs
    remontées par les actions UI.
    """

    log_dir = Path.cwd() / "runtime_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{app_name.lower()}-{datetime.now().strftime('%Y%m%d')}.log"

    if not LOGGER.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        LOGGER.setLevel(logging.INFO)
        LOGGER.addHandler(file_handler)
        LOGGER.addHandler(stream_handler)
        LOGGER.propagate = False

    return log_path


def install_exception_hooks(app_name: str) -> None:
    """Installe des hooks globaux pour éviter les crashs silencieux."""

    def _handle_exception(exc_type, exc_value, exc_traceback) -> None:  # type: ignore[no-untyped-def]
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        LOGGER.exception("Unhandled exception in %s:\n%s", app_name, message)
        _show_error_dialog(
            "Une erreur inattendue est survenue.",
            "L'application a intercepte l'erreur pour eviter une fermeture brutale.\n"
            "Consulte le dossier runtime_logs pour le detail technique.",
        )

    def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        _handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = _handle_exception
    threading.excepthook = _handle_thread_exception


def guarded_ui_action(function: F) -> F:
    """Décorateur pour journaliser et afficher proprement les erreurs de slots Qt."""

    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return function(*args, **kwargs)
        except Exception:
            LOGGER.exception("UI action failed: %s", function.__qualname__)
            _show_error_dialog(
                "Action interrompue",
                "Une erreur est survenue pendant cette action. "
                "L'application reste ouverte et le detail a ete enregistre dans runtime_logs.",
            )
            return None

    return wrapper  # type: ignore[return-value]


def _show_error_dialog(title: str, message: str) -> None:
    app = QApplication.instance()
    if app is None:
        return
    active_window = app.activeWindow()
    QMessageBox.critical(active_window, title, message)
