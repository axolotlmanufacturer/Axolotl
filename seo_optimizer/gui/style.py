"""Zentrale Farb-/Schrift-Definitionen und ttk-Styling."""

from tkinter import ttk

COLORS = {
    "bg": "#f4f6f8",
    "sidebar": "#ffffff",
    "primary": "#0f4c81",
    "primary_dark": "#0b3a63",
    "accent": "#1f9d55",
    "text": "#1f2937",
    "muted": "#6b7280",
    "border": "#e5e9ef",
    "danger": "#b3261e",
}

FONT_HEADER = ("Segoe UI", 14, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)


def apply_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=COLORS["bg"])

    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONT_NORMAL)
    style.configure("Sidebar.TLabel", background=COLORS["sidebar"], foreground=COLORS["text"], font=FONT_NORMAL)
    style.configure("Header.TLabel", background=COLORS["primary"], foreground="white", font=FONT_HEADER)
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=FONT_SMALL)
    style.configure("Bold.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONT_BOLD)

    style.configure("TButton", font=FONT_NORMAL, padding=6)
    style.configure(
        "Primary.TButton",
        font=FONT_BOLD,
        padding=8,
        background=COLORS["primary"],
        foreground="white",
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_dark"]), ("disabled", COLORS["border"])],
    )
    style.configure("Danger.TButton", font=FONT_NORMAL, padding=6, foreground=COLORS["danger"])

    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", font=FONT_NORMAL, padding=(14, 8))

    style.configure(
        "Treeview",
        background="white",
        fieldbackground="white",
        foreground=COLORS["text"],
        rowheight=26,
        font=FONT_NORMAL,
        borderwidth=0,
    )
    style.configure("Treeview.Heading", font=FONT_BOLD, background=COLORS["border"])
    style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "white")])

    style.configure(
        "Green.Horizontal.TProgressbar",
        troughcolor=COLORS["border"],
        background=COLORS["accent"],
        thickness=14,
    )

    style.configure("TCheckbutton", background=COLORS["bg"], font=FONT_NORMAL)
    style.configure("TLabelframe", background=COLORS["bg"], borderwidth=1)
    style.configure("TLabelframe.Label", background=COLORS["bg"], font=FONT_BOLD, foreground=COLORS["primary"])
    style.configure("TEntry", padding=4)

    return style
