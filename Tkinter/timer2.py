#!/usr/bin/env python3

# Display UTC.
# started with https://docs.python.org/3.4/library/tkinter.html#module-tkinter

import Tkinter as tk
import time

def current_iso8601():
    """Get current date and time in ISO8601"""
    # https://en.wikipedia.org/wiki/ISO_8601
    # https://xkcd.com/1179/
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.now = tk.StringVar()
        self.time = tk.Label(self, font=('Helvetica', 24))
        self.time.pack(side="top")
        self.time["textvariable"] = self.now

        self.QUIT = tk.Button(self, text="QUIT", fg="red",
                                            command=root.destroy)
        self.QUIT.pack(side="bottom")

        # initial time display
        self.onUpdate()

    def onUpdate(self):
        # update displayed time
        self.now.set(current_iso8601())
        # schedule timer to call myself after 1 second
        self.after(1000, self.onUpdate)

root = tk.Tk()
app = Application(master=root)
root.mainloop()