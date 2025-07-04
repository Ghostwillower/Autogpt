"""Simple Tkinter based GUI for Ghosthand."""


import tkinter as tk
from tkinter import scrolledtext, messagebox

from memory import get_recent_goals, list_users
from main import run_goal
from user_profile import detect_user
from enrollment import run_enrollment


def start_gui() -> None:
    """Launch the Ghosthand graphical interface."""

    root = tk.Tk()
    root.title("Ghosthand")
    root.configure(bg="#eef2ff")

    title_lbl = tk.Label(root, text="Ghosthand", font=("Helvetica", 16, "bold"), bg="#eef2ff")
    title_lbl.pack(pady=(10, 5))

    entry_frame = tk.Frame(root, bg="#eef2ff")
    entry_frame.pack(padx=10, pady=10, fill=tk.X)

    goal_var = tk.StringVar()
    goal_entry = tk.Entry(entry_frame, textvariable=goal_var, width=60)
    goal_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    users = list_users()
    if detect_user() not in users:
        users.append(detect_user())
    user_var = tk.StringVar(value=users[0])
    user_menu = tk.OptionMenu(entry_frame, user_var, *users)
    user_menu.pack(side=tk.RIGHT)

    dry_var = tk.BooleanVar()
    dry_check = tk.Checkbutton(root, text="Dry run", variable=dry_var, bg="#eef2ff")
    dry_check.pack(anchor="w", padx=10)

    enroll_button = tk.Button(root, text="Enroll New User", command=run_enrollment)
    enroll_button.pack(anchor="w", padx=10, pady=(0, 5))

    output = scrolledtext.ScrolledText(root, width=80, height=20)
    output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def run_clicked() -> None:
        goal = goal_var.get().strip()
        if not goal:
            messagebox.showinfo("Ghosthand", "Please enter a goal.")
            return
        output.insert(tk.END, f"> {goal}\n")
        results = run_goal(goal, dry_run=dry_var.get(), user=user_var.get())
        output.insert(tk.END, f"Result: {results}\n")
        output.see(tk.END)

    run_button = tk.Button(entry_frame, text="Run Goal", command=run_clicked)
    run_button.pack(side=tk.RIGHT, padx=(5, 0))

    def show_recent() -> None:
        recent = get_recent_goals(5)
        lines = [f"{ts}: {g} -> {r}" for ts, g, r in recent]
        messagebox.showinfo("Recent Goals", "\n".join(lines) if lines else "No history")

    menubar = tk.Menu(root)
    history_menu = tk.Menu(menubar, tearoff=0)
    history_menu.add_command(label="Show Recent Goals", command=show_recent)
    menubar.add_cascade(label="History", menu=history_menu)
    root.config(menu=menubar)

    root.mainloop()
