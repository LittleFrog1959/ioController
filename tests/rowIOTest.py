# Test layout for the rowIO page.

import tkinter as tk                # python 3

class constants ():
    # The number of frames to have across the page
    fCount = 4

c = constants()

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
        # Now create the frames that will hold the pins
        self.fList = []
        for f in range (0, c.fCount):
            # Add an entry to the end of the list (f points at it)
            self.fList.append (0)
            # Now within the current list item, create a list which contains the button at [0]
            # and a simple INT at [1]
            self.fList[f] = [tk.Frame (self, padx = 10, pady = 10)]
            # This zero will be the "rows used" counter for each frame
            self.fList[f].append (0)
            # Now pack the frame
            self.fList[f][0].pack (side = tk.LEFT, expand = True)

            # Quick add of a button in each frame
#            self.btn = tk.Button (self.fList[f][0], text = str (f))
#            self.btn.pack ()

        # Now set up a pointer that determines which of the above frames is used
        fPointer = 0

        # Set up a list to hold the button widgets
        self.oRBtn = []
        self.iRBtn = []

        # Read the specification file and populate the input and output
        # button lists as we go
        self.fHandle = open ('rowIO.txt', 'r')
        # Go through each entry in the specification file
        for self.fLine in self.fHandle:
            if self.fLine[0] == 'O':
                # Extract the board and pin
                self.board, self.pin = self.getBoardnPin (self.fLine)
                # Append an entry to the button list
                self.oRBtn.append (0)
                pointer = len (self.oRBtn) - 1
                # Create the button in the button list AND have it's parent
                # be the current frame
                self.oRBtn [pointer] = tk.Button (self.fList[fPointer][0], text = 'off\n' + 'O' + str (self.board) + ',' + str (self.pin) + '\nforce on', width = 20,
                                anchor = 'w', justify = tk.LEFT)
                self.oRBtn [pointer].pack (padx = 15, pady = 5)
                # Bump the correct rows used counter
                self.fList[fPointer][1] += 1

            elif self.fLine [0] == 'I':
                # As above for inputs
                self.board, self.pin = self.getBoardnPin (self.fLine)
                # Append an entry to the button list
                self.iRBtn.append (0)
                pointer = len (self.iRBtn) - 1
                # Create the button in the button list AND have it's parent
                # be the current frame
                self.iRBtn [pointer] = tk.Button (self.fList[fPointer][0], text = 'off\n' + 'O' + str (self.board) + ',' + str (self.pin) + '\nforce on', width = 20,
                                anchor = 'w', justify = tk.LEFT)
                self.iRBtn [pointer].pack (padx = 15, pady = 5)
                # Bump the correct rows used counter
                self.fList[fPointer][1] += 1

            elif self.fLine [0] == "+":
                # Figure out which frame we're going to use for all following specification
                # file entries. Remember that fPointer contains the current frame
                fPointer = 0
                for pointer in range (0, len (self.fList) - 1):
                    if self.fList[pointer][1] > self.fList[pointer + 1][1]:
                        fPointer = pointer + 1

                # Add the title to the correct frame
                label = tk.Label (self.fList[fPointer][0], text = self.fLine[1:-1])
                label.pack (side = 'top', anchor = 'w')
                # Bump the correct rows used counter
                self.fList[fPointer][1] += 1
            else:
                print ('Error')

        self.fHandle.close ()

        button1 = tk.Button(self.bottomFrame, text="Go to Page One",
                            command=lambda: controller.show_frame("PageOne"))
        button2 = tk.Button(self.bottomFrame, text="Go to Page Two",
                            command=lambda: controller.show_frame("PageTwo"))
        button1.pack()
        button2.pack()

        # Debug:  Output each of the button lists to see what we built
        for entry in self.oRBtn:
            print ("output " + str (entry))
        for entry in self.iRBtn:
            print ("Input  " + str (entry))

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
