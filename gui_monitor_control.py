import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import subprocess
import os

CONFIG_PATH = "config.json"
PROCESS = None


def save_config(naming, compression):
    config = {
        "naming": naming,
        "compression": compression
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print("設定を保存しました：", config)


def main():
    root = tk.Tk()
    root.title("Watch Man")
    root.geometry("400x420")

    # 設定変数
    naming_var = tk.StringVar(value=True)
    compress_var = tk.StringVar(value="JPEG")
    monitor_running = tk.BooleanVar(value=False)

    # 命名規則
    naming_frame = ttk.LabelFrame(root, text="命名規則", padding=10)
    naming_frame.pack(padx=10, pady=10, fill="x")

    ttk.Radiobutton(naming_frame, text="随時命名", variable=naming_var, value="1").pack(anchor="w")
    # ttk.Radiobutton(naming_frame, text="命名統合", variable=naming_var, value="2").pack(anchor="w")
    ttk.Radiobutton(naming_frame, text="そのまま", variable=naming_var, value="0").pack(anchor="w")

    # 圧縮方式
    # def on_compression_selected():
    #     print("※ 圧縮機能は未実装です")
    
    # def off_compression_selected():
    #     print("※ 圧縮機能は未実装です")

    compress_frame = ttk.LabelFrame(root, text="圧縮方式", padding=10)
    compress_frame.pack(padx=10, pady=10, fill="x")

    ttk.Radiobutton(compress_frame, text="JPEG", variable=compress_var, value="JPEG").pack(anchor="w")
    ttk.Radiobutton(compress_frame, text="Nomal", variable=compress_var, value="Nomal").pack(anchor="w")

    # バックアップパス
    backup_frame = ttk.Frame(root, padding=10)
    backup_frame.pack(padx=10, pady=10, fill="x")
    ttk.Label(backup_frame, text="バックアップディレクトリ:").pack(anchor="w")
    ttk.Label(backup_frame, text=r"C:\BackUp_Pictures", foreground="blue").pack(anchor="w")

    # ボタン群
    button_frame = ttk.Frame(root, padding=10)
    button_frame.pack(padx=10, pady=10, fill="x")

    def toggle_monitor():
        if monitor_running.get():
            stop_monitor()
        else:
            start_monitor()

    def start_monitor():
        global PROCESS
        if PROCESS is None:
            try:
                PROCESS = subprocess.Popen(["python", "img_check.py"])
                monitor_running.set(True)
                toggle_btn.config(text="監視停止")
                print("監視開始")
            except Exception as e:
                messagebox.showerror("エラー", f"監視プログラムの起動に失敗しました\n{e}")

    def stop_monitor():
        global PROCESS
        if PROCESS:
            PROCESS.terminate()
            PROCESS.wait()
            PROCESS = None
            monitor_running.set(False)
            toggle_btn.config(text="監視開始")
            print("監視停止")

    def on_save():
        save_config(naming_var.get(), compress_var.get())
        messagebox.showinfo("保存", "設定を保存しました")

    save_btn = ttk.Button(button_frame, text="設定を保存", command=on_save)
    save_btn.pack(side="left", padx=5, pady=5)

    toggle_btn = ttk.Button(button_frame, text="監視開始", command=toggle_monitor)
    toggle_btn.pack(side="left", padx=5, pady=5)

    root.protocol("WM_DELETE_WINDOW", lambda: (stop_monitor(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
