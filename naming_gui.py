import tkinter as tk
from tkinter import ttk
import time
import json
import threading
import subprocess
import os

class name_input:
    def main():
        root = tk.Tk()
        root.title("新規命名")
        root.geometry("300x150")
    
        text_frame = ttk.Frame(root, padding=10)
        text_frame.pack(padx=10, pady=10, fill="x")
        button_frame = ttk.Frame(root, padding=10)
        button_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(text_frame, text="命名欄：").pack(side="left")

        entry = ttk.Entry(text_frame, width=20)
        entry.pack(side="top")

        def any_command():
            get_value()
            stop_win()

        ttk.Button(button_frame, text="決定", command=any_command).pack(side="right", padx=5, pady=5)
        
        def stop_win():
            root.destroy()

        def get_value():
            value = entry.get().strip()
            print(value)


        root.mainloop()


    if __name__ == "__main__":
        main()