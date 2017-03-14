import Tkinter as tki # tkinter in Python 3

root = tki.Tk()

frm = tki.Frame(root, bd=16, relief='sunken')
frm.grid()

var = tki.StringVar()

mild = tki.Radiobutton(frm, text='Mild', variable=var)
mild.config(indicatoron=0, bd=4, width=12, value='Mild')
mild.grid(row=0, column=0)

medium = tki.Radiobutton(frm, text='Medium', variable=var)
medium.config(indicatoron=0, bd=4, width=12, value='Medium')
medium.grid(row=0, column=1)

hot = tki.Radiobutton(frm, text='Hot', variable=var)
hot.config(indicatoron=0, bd=4, width=12, value='Hot')
hot.grid(row=0, column=2)

root.mainloop()