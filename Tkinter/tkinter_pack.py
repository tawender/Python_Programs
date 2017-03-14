import Tkinter as tki

def print_var(*args):
    print root.getvar(name=args[0])
    # or
    print var.get()

root = tki.Tk()

frm = tki.Frame(root, bd=16, relief='sunken')
frm.pack()

var = tki.StringVar()
var.trace('w', print_var)

b_dict = {'Mild':0, 'Medium':0, 'Hot':0}

for key in b_dict:
    b_dict[key] = tki.Radiobutton(frm, text=key, bd=4, width=12)
    b_dict[key].config(indicatoron=0, variable=var, value=key)
    b_dict[key].pack(side='left')

root.mainloop()