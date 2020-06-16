# Test layout for the rowIO page.

import tkinter as tk                # python 3

class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, PageOne, PageTwo):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # First create a frame to hold the exit buttons at the bottom of the page
        self.bottomFrame = tk.Frame (self, width = 4000, relief = 'ridge', padx = 10, pady = 10)
        self.bottomFrame.pack (side = tk.BOTTOM, expand = True)
        # Now create two frames, one on the left and the other on the right
        self.leftFrame = tk.Frame (self, padx = 10, pady = 10)
        self.leftFrame.pack (side = tk.LEFT, expand = True)
        self.rightFrame = tk.Frame (self, padx = 10, pady = 10)
        self.rightFrame.pack (side = tk.RIGHT, expand = True)

        # Now set up a toggle that determines which of the above frames is used
        self.toggleFrame = self.leftFrame
        self.leftRows = 0
        self.rightRows = 0

        # Set up a list to hold the button widgets
        self.oRBtn = []
        self.iRBtn = []

        # Read the specification file and populate the input and output
        # button lists as we go
        self.fHandle = open ('rowIO.txt', 'r')
        for self.fLine in self.fHandle:
            if self.fLine[0] == 'O':
                self.board, self.pin = self.getBoardnPin (self.fLine)
                self.oRBtn.append (0)
                pointer = len (self.oRBtn) - 1
                self.oRBtn [pointer] = tk.Button (self.toggleFrame, text = 'off\n' + 'O' + str (self.board) + ',' + str (self.pin) + '\nforce on', width = 20,
                                anchor = 'w', justify = tk.LEFT)
                self.oRBtn [pointer].pack (padx = 5, pady = 5)
                if self.toggleFrame == self.leftFrame:
                    self.leftRows += 1
                else:
                    self.rightRows += 1
            elif self.fLine [0] == 'I':
                self.board, self.pin = self.getBoardnPin (self.fLine)
                self.iRBtn.append (0)
                pointer = len (self.iRBtn) - 1
                self.iRBtn [pointer] = tk.Button (self.toggleFrame, text = 'on\n' + 'I' + str (self.board) + ',' + str (self.pin) + '\nlive', width = 20,
                                anchor = 'w', justify = tk.LEFT)
                self.iRBtn [pointer].pack (padx = 5, pady = 5)
                if self.toggleFrame == self.leftFrame:
                    self.leftRows += 1
                else:
                    self.rightRows += 1
            elif self.fLine [0] == "+":
                # Figure out which frame we're going to use for all following specification
                # file entries
                if self.leftRows < self.rightRows:
                    self.toggleFrame = self.leftFrame
                else:
                    self.toggleFrame = self.rightFrame

                label = tk.Label (self.toggleFrame, text = self.fLine[1:-1])
                label.pack (side = 'top', anchor = 'w')
                if self.toggleFrame == self.leftFrame:
                    self.leftRows += 1
                else:
                    self.rightRows += 1
#                label.pack (side = 'top', fill = 'x',  anchor = 'w', justify = tk.LEFT, pady = 5)
            else:
                print ('Error')

        self.fHandle.close ()

        button1 = tk.Button(self.bottomFrame, text="Go to Page One",
                            command=lambda: controller.show_frame("PageOne"))
        button2 = tk.Button(self.bottomFrame, text="Go to Page Two",
                            command=lambda: controller.show_frame("PageTwo"))
        button1.pack()
        button2.pack()

    def getBoardnPin (self, lt):
        # Seperate out the board and pin from the supplied text
        address = lt[1:]
        b = int (address.split (',')[0])
        p = int (address.split (',')[1])
        return b, p

class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 1")
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 2")
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
