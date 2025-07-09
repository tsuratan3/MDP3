import tkinter as tk
from tkinter import ttk

def ask_name(master=None):
    if master is None:
        master = tk.Tk()
        master.withdraw()  # メインウィンドウ非表示

    popup = tk.Toplevel(master)
    popup.title("新規命名")
    popup.geometry("300x150")
    popup.transient(master)
    popup.grab_set()

    entry = ttk.Entry(popup, width=20)
    entry.pack(pady=20)
    result = {"value": None}

    def on_ok():
        v = entry.get().strip()
        if v:
            result["value"] = v
            popup.destroy()

    ttk.Button(popup, text="決定", command=on_ok).pack()
    master.wait_window(popup)
    return result["value"]

# 単体実行テスト用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    name = ask_name(root)
    print("入力された名前:", name)