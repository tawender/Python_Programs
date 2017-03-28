from Tkinter import *

root = Tk()

labelframe = LabelFrame(root, text="This is a LabelFrame", padx=5, pady=5)
labelframe.pack(fill="both", expand="yes", padx=10, pady=10)

left = Label(labelframe, text="Inside the LabelFrame\t\t\t\n\n\n\n\n\n")
left.pack()

root.mainloop()