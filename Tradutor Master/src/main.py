import tkinter as tk

from ui import TranslatorUI


def main() -> None:
    root = tk.Tk()
    TranslatorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
