import ttk
from Tkinter import *

class myTestFrame(Frame):

    def __init__(self):

        Frame.__init__(self)

        self.master.title("My Test Frame")

        self.master.minsize(350, 150)
        self.grid(sticky=W+N+S+E)

        firstLayer      = Frame(self)
        firstLayer.pack(side="top", fill="x")
        secondLayer      = Frame(self)
        secondLayer.pack(side="top", fill="x")
        thirdLayer      = Frame(self)
        thirdLayer.pack(side="top", fill="x")

        labelText=StringVar()
        labelText.set("Enter your area zip code: ")
        labelDir=Label(firstLayer, textvariable=labelText, fg="black", font = "Calibri 10 bold")
        labelDir.grid(row=2, column=0, sticky="W")
        zipCode=IntVar(None)
        entryFieldFrame=Entry(firstLayer,textvariable=zipCode,width=5)
        entryFieldFrame.grid(row=2, column=1, sticky="W", padx=31)

        ttk.Separator(secondLayer, orient='horizontal').grid(column=0,
            row=0, columnspan=2, sticky='ew')

        labelText=StringVar()
        labelText.set("Enter your age: ")
        labelDir=Label(secondLayer, textvariable=labelText, fg="black", font = "Calibri 10 bold")
        labelDir.grid(row=2, column=0, sticky="W")
        age=IntVar(None)
        age.set(1.0)
        entryFieldFrame=Entry(secondLayer,textvariable=age,width=5)
        entryFieldFrame.grid(row=2, column=1, sticky="W", padx=83)

        ttk.Separator(thirdLayer, orient='horizontal').grid(column=0,
            row=0, columnspan=2, sticky='ew')

        labelText=StringVar()
        labelText.set("Enter your brother's age: ")
        labelDir=Label(thirdLayer, textvariable=labelText, fg="black", font = "Calibri 10 bold")
        labelDir.grid(row=2, column=0, sticky="W")
        brothersAge=IntVar(None)
        entryFieldFrame=Entry(thirdLayer,textvariable=brothersAge,width=5)
        entryFieldFrame.grid(row=2, column=1, sticky="W", padx=29)

if __name__ == "__main__":

    testFrame = myTestFrame()
    testFrame.mainloop()