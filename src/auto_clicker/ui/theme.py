from __future__ import annotations

from PySide6.QtWidgets import QApplication

ACCENT = "#5EC8D6"


def apply_theme(app: QApplication) -> None:
    try:
        import qdarktheme  # type: ignore[import-not-found]

        qdarktheme.setup_theme("dark", custom_colors={"primary": ACCENT})
    except ImportError:
        app.setStyleSheet(_FALLBACK_DARK)


_FALLBACK_DARK = """
    QWidget { background-color: #1e1e1e; color: #e0e0e0; }
    QPushButton { background-color: #2d2d2d; border: 1px solid #3a3a3a; padding: 6px 12px; }
    QPushButton:hover { background-color: #383838; }
    QPushButton#primary { background-color: #5EC8D6; color: #1e1e1e; font-weight: 600; }
    QLineEdit, QSpinBox { background-color: #2d2d2d; border: 1px solid #3a3a3a; padding: 4px; }
    QRadioButton, QCheckBox { spacing: 8px; }
"""
