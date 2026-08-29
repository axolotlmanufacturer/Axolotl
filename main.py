#!/usr/bin/env python3
"""Einstiegspunkt: Lokal-SEO Manager fuer Handwerksbetriebe."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seo_optimizer.database import Database
from seo_optimizer.gui.main_window import MainWindow

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "seo_optimizer.db")


def main():
    db = Database(DB_PATH)
    app = MainWindow(db)
    try:
        app.mainloop()
    finally:
        db.close()


if __name__ == "__main__":
    main()
