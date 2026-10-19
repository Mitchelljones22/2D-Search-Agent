import tkinter

import pygame


def _tk_get():
    root = tkinter.Tk()
    root.withdraw()
    try:
        return root.clipboard_get()
    except tkinter.TclError:
        return ""
    finally:
        root.destroy()


def _tk_put(text):
    root = tkinter.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()


def get_text():
    try:
        pygame.scrap.init()
        text = pygame.scrap.get_text()
        if text:
            return text
    except Exception:
        pass
    return _tk_get()


def put_text(text):
    try:
        pygame.scrap.init()
        pygame.scrap.put_text(text)
        if pygame.scrap.get_text() == text:
            return
    except Exception:
        pass
    _tk_put(text)