# IO control program
# Latest version here   https://github.com/LittleFrog1959/ioController
# Credits here          https://github.com/LittleFrog1959/ioController/wiki/Credits

import tkinter as tk

import socket
import os
import errno
import datetime as dt
import sys
import time

# From a boot, we need a delay before the program starts running.  This is because I
# found that without this, sometimes the eth0 port is not running when we start from
# boot time
time.sleep (5)

# The AB Electronics driver for the PIO board
from IOPi import IOPi

# File containing constants used by this program
import constants
c = constants.constants ()

# File containing globals used by this program
import globals
g = globals.ioGlobals ()

# Set up the logging system
import logging

class logClass (logging.log):
    # This class inherits the disk logger and allows all
    # of it's methods to be used here.
    def __init__ (self):
        super().__init__ ()

    def logMsg (self, message, level = 'debug'):
        # NOTE:  The max message length is about 130 chars.  Form the message then send
        #  to the disk log
        m = self.logDiskMsg (message, level)
        # Send the message to the message text box. At the moment this will error if a
        # message is produced before the messagePage is defined so I just print to the
        # terminal session that started theprogram

        # Init something to hold the message we're going to print
        wm = None
        while (len (m) >  0):

            # Detect first time around the loop
            if wm == None:
                # Load up the first part of the message and trim the remainder
                wm = m[0:c.messageColMax]
                m = m[c.messageColMax:]

            else:
                # We're printing a multi line message to the on-screen text box
                # so do as above but pad the start of the message with some spaces
                wm = ' ' * 10 + m[0:c.messageColMax - 10]
                m = m[c.messageColMax - 10:]
            # The print could fail if the message page is not initialised yet
            try:
                app.frames['messagePage'].addMsg (wm)
            except NameError:
                print ('Could not print to messagePage')
                print (m)

    def logClose (self):
        # Close the disk log because we're shutting down
        self.logDiskClose ()

    def logFlush (self):
        # Flush the disk log to the actual disk.  This makes "tail -F log.log"
        # work better
        self.logDiskFlush ()

# Now actually define the logging object
l = logClass ()

class sampleApp (tk.Tk):
    # This is the start of the main program that interfaces to the tk system.
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Read if we're connected to the touch screen (':0.0' or ':0') or some other
        # screen.  The touch screen uses all the screen space for our application
        # and does not need the mouse.  Other screens don't do touch and so need
        # the mouse to be working.
        try:
            displayReference = os.environ['DISPLAY']

        except KeyError:
            # Could not read DISPLAY value so just proceed with it set to something
            displayReference = None

        # I don't know why but when the program us auto started, the DISPLAY is ':0'
        # and when it's run from the command line, it's set to ':0.0' so this
        # works around that problem
        if (displayReference == ':0.0') or (displayReference == ':0'):
            # If we're running on the touch screen, then set the screen size, turn the
            # mouse off, set it's location  to top left then make sure our window uses
            # the full screen
            self.geometry (c.touchScreenResolution)
            self.config (cursor = 'none')
            self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
            self.attributes('-fullscreen', True)

        else:
            self.geometry (c.touchScreenResolution)

        # Build the frame into which all the page definitions will fit
        container = tk.Frame (self)
        container.pack (side = 'top', fill = 'both', expand = True)
        container.grid_rowconfigure (0, weight = 1)
        container. grid_columnconfigure (0, weight = 1)

        # Amazing bit of code (see credits) which builds a dictionary of the pages
        # initialising them as we go
        self.frames = {}

        for F in (deviceIOPage, gridIOPage, messagePage):
            page_name = F.__name__
            frame = F (parent = container, controller = self)
            self.frames [page_name] = frame
            frame.grid (row = 0, column = 0, sticky = 'nsew')

        # Select the start up page to display
        self.show_frame ('gridIOPage')

    def show_frame (self, page_name):
        # Switches to the named page
        frame = self.frames [page_name]
        frame.tkraise ()

class messagePage (tk.Frame):
    # This class creates the message page.  This is the simplest of the pages and
    # simply echos log messages to the screen.
    def __init__(self, parent, controller):
        # DON'T UNDERSTAND THIS BIT.  It registers the page in the dictionary that
        # controls the presentation of pages.
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Create the text box that will hold the messages
        self.msgText = tk.Text (self)
        self.msgText.pack (anchor = 'nw', expand = True, fill = 'both')

        # Create the buttons that allow you to navigate to other pages and clear
        # the message list
        self.button = tk.Button(self, text='Grid I/O', width = 8,  height = 2,
                   command=lambda: controller.show_frame('gridIOPage'))
        self.button.pack(side = 'left', padx = 100, pady = 5)
        self.button = tk.Button(self, text='Device I/O', width = 8, height = 2,
                   command=lambda: controller.show_frame('deviceIOPage'))
        self.button.pack(side = 'left')
        self.button = tk.Button(self, text='Clear', width = 8, height = 2,
                   command=lambda: self.clearMsgs())
        self.button.pack(side = 'left', padx = 100)

        # Initalise a counter for the number of messages on the screen
        # I only need this because I can't see a way of knowing how many
        # rows of text there are on the screen...  There must be a way??
        self.messageRows = 0

    def clearMsgs (self):
        # Clear the messages from the screen.  Go around a loop deleting the
        # top message in the text box
        rowCount = int(self.msgText.index('end-1c').split('.')[0])

        for self.pointer in range (0, rowCount):
            self.msgText.delete ('1.0', '2.0')

    def addMsg (self, m):
        # Delete the oldest message if we're about to run out of space
        # in the text box and then print the supplied message to the text
        # box
         # Bump the number of messages that we've sent to the text box
        self.messageRows += 1

        # If we're going to print off the bottom of the page, delete the
        # olest message.  Keep the message counter and a sensible value
        if self.messageRows > c.messageRowMax:
            self.messageRows = c.messageRowMax
            # 1.0...  Don't ask... The first row (1) and the first col (0)
            self.msgText.delete ('1.0', '2.0')

        # Print the message to the text box
        self.msgText.insert (tk.END, m + '\n')

class deviceIOPage(tk.Frame):
    # This class creates a funny old page; it reads a text config file and presents
    # I/O grouped in a way that's useful to the user.  Not sure if this was really
    # worth the effort, but it's here now...  This class is something of a 'slave' to
    # the grid I/O page because it assumes that the global lists containing the state
    # of the I/O are populated elsewhere...  That place is the grid I/O page class
    def __init__(self, parent, controller):

        # I still don't understand this!
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # First create a frame to hold the exit buttons at the bottom of the page
        self.bottomFrame = tk.Frame (self)
        self.bottomFrame.pack (side = tk.BOTTOM, fill = tk.X)

        # Create a canvas within which all one big frame and the context menus will be presented
        self.canvas = tk.Canvas (self)

        # And then within that canvas, create a frame which will hold the columns of buttons
        self.bigFrame = tk.Frame (self.canvas)
        self.bigFrame.pack (side = tk.LEFT)

        # Now create one scroll bar that will make the whole frame go up and down the screen
        self.sb = tk.Scrollbar (self, orient = 'vertical', command = self.canvas.yview, width = 30)
        self.canvas.configure (yscrollcommand = self.sb.set)
        self.sb.pack (side = 'right', fill = 'y')
        self.canvas.pack (side = 'left')
        self.canvas.create_window ((0, 0), window = self.bigFrame, anchor = 'nw')
        self.bigFrame.bind ('<Configure>', self.scrollFunction)

        # Create a pop up menu to control the forced state of a selected pin.  This was copied
        # from the grid I/O page
        self.outputPopUpMenu = tk.Menu (self.bigFrame, tearoff = 0)
        self.outputPopUpMenu.config (font = (None, 20))
        self.outputPopUpMenu.add_command (label = 'output')
        self.outputPopUpMenu.entryconfigure (0, state = tk.DISABLED)
        self.outputPopUpMenu.add_command (label = 'live', command = self.setOutputPinLive)
        self.outputPopUpMenu.add_command (label = 'force on', command = self.setOutputPinForceOn)
        self.outputPopUpMenu.add_command (label = 'force off', command = self.setOutputPinForceOff)

        self.inputPopUpMenu = tk.Menu (self.bigFrame, tearoff = 0)
        self.inputPopUpMenu.config (font = (None, 20))
        self.inputPopUpMenu.add_command (label = 'input')
        self.inputPopUpMenu.entryconfigure (0, state = tk.DISABLED)
        self.inputPopUpMenu.add_command (label = 'live', command = self.setInputPinLive)
        self.inputPopUpMenu.add_command (label = 'force on', command = self.setInputPinForceOn)
        self.inputPopUpMenu.add_command (label = 'force off', command = self.setInputPinForceOff)

        # Now create the frames that will hold the pins
        self.fList = []

        for f in range (0, c.fCount):
            # Add an entry to the end of the list (f points at it)
            self.fList.append (0)
            # Now within the current list item, create a list which contains the button at [0]
            # and a simple INT at [1]
            self.fList[f] = [tk.Frame (self.bigFrame, padx = 10, pady = 10)]
            # This zero will be the "rows used" counter for each frame
            self.fList[f].append (0)
            # Now pack the frame
            self.fList[f][0].pack (side = tk.LEFT, expand = True)

        # Now set up a pointer that determines which of the above frames is used
        fPointer = 0

        # Set up a list to hold the button widgets
        self.oRBtn = []
        self.iRBtn = []

        # Read the specification file and populate the input and output
        # button lists as we go
        self.loadDeviceIOPage ()

        # Now create the navigatio buttons that get you to other pages

        button = tk.Button(self.bottomFrame, text= 'Grid I/O', width = 8, height = 2,
                        command=lambda: controller.show_frame('gridIOPage'))
        button.pack(side = 'left', padx = 100, pady = 5)

        button = tk.Button(self.bottomFrame, text= 'Messages', width = 8, height = 2,
                        command=lambda: controller.show_frame('messagePage'))
        button.pack(side = 'left')

    def loadDeviceIOPage (self):
        # This is a bit tricky.  It populates the frames with buttons based on "who's
        # got the fewest right now".

        # First of all try to open the text file containing the config of the buttons
        # we want to see and error/exit if it does not exist
        try:
            self.fHandle = open (c.deviceIOFilename, 'r')

        except Exception as ex:
            template = 'An exception of type {0} occurred. Arguments:{1!r}'
            message = template.format(type(ex).__name__, ex.args)
            l.logMsg (message)
            return

        # Go through each entry in the specification file seeing if the first char on
        # the line is an O, I or some other legal value
        for self.fLine in self.fHandle:
            if self.fLine[0] == 'O':
                # Extract the board and pin from the line of text we're working on
                self.board, self.pin = self.getBoardnPin (self.fLine)

                # Append an entry to the button list
                self.oRBtn.append (0)
                pointer = len (self.oRBtn) - 1

                # Create the button in the button list AND have it's parent
                # be the current frame.  Note how we add this as a list becuase
                # in a moment we're going to add the board and pin to this one
                # pointer entry
                self.oRBtn [pointer] = [tk.Button (self.fList[fPointer][0], text = 'null', width = 18,
                                anchor = 'w', justify = tk.LEFT,
                                command = lambda x = pointer: self.outputPopUpCallBack (x))]
                self.oRBtn [pointer][0].pack (padx = 15, pady = 5)

                # Append two more list items to this entry to save the board and pin
                self.oRBtn [pointer].append (self.board)
                self.oRBtn [pointer].append (self.pin)

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
                self.iRBtn [pointer] = [tk.Button (self.fList[fPointer][0], text = 'null', width = 18,
                                anchor = 'w', justify = tk.LEFT,
                                command = lambda x = pointer: self.inputPopUpCallBack (x))]
                self.iRBtn [pointer][0].pack (padx = 15, pady = 5)

                # Append two more list items to this entry to save the board and pin
                self.iRBtn [pointer].append (self.board)
                self.iRBtn [pointer].append (self.pin)

                # Bump the correct rows used counter
                self.fList[fPointer][1] += 1

            elif self.fLine [0] == "+":
                # Figure out which frame we're going to use for all following specification
                # file entries. Remember that fPointer contains the current frame

                # Find the lowest row count and remember the column that's in
                lowest = 999999
                for pointer in range (0, len (self.fList)):
                    if self.fList[pointer][1] < lowest:
                        lowest = self.fList[pointer][1]
                        fPointer = pointer

                # Add the title to the correct frame
                label = tk.Label (self.fList[fPointer][0], text = self.fLine[1:-1])
                label.pack (side = 'top', anchor = 'w')

                # Bump the correct rows used counter
                self.fList[fPointer][1] += 1

            elif self.fLine[0] == "#":
                # Throw away comment lines
                pass

            elif self.fLine.lstrip () == '':
                # Throw away blank lines
                pass

            elif self.fLine.find ("abort") == 0:
                # If the line starts with abort then stop reading the input specification
                # file
                break
            else:
                print ('Error in grid I/O specification file')

        # Close the specification file and exit
        self.fHandle.close ()

    def scrollFunction (self, event):
        # Called when someone moves the scroll bar up / down
        self.canvas.configure (scrollregion = self.canvas.bbox ('all'), width = 1270, height = 710)

# GOT TO HERE DAVID!

    def outputPopUpCallBack (self, p):
        # Given the current mouse location, fix the location that the menu will be placed
        x, y = self.fixPopUpLocation ()

        # We get the board and pin as parameters.  Make these visable to the selected menu
        # items through these variables
        g.popUpBoard = self.oRBtn[p][1]
        g.popUpPin = self.oRBtn[p][2]

        # There might already be another pop up menu being displayed so remove it.  This does
        # not seem to error if it's not being displayed which is good I guess
        self.inputPopUpMenu.unpost ()

        try:
            # Fix the name of the menu to be the name of the pin we're trying to change state
            # on then display the menu
            self.outputPopUpMenu.entryconfigure (0, label = g.oName[g.popUpBoard][g.popUpPin])
            self.outputPopUpMenu.post (x, y)

        except:
            l.logMsg ('Unknown error while trying to present output pop up menu', level = 'alarm')

    def inputPopUpCallBack (self, p):
        # Given the current mouse location, fix the location that the menu will be placed
        x, y = self.fixPopUpLocation ()

        g.popUpBoard = self.iRBtn[p][1]
        g.popUpPin = self.iRBtn[p][2]
        self.outputPopUpMenu.unpost ()

        try:
            self.inputPopUpMenu.entryconfigure (0, label = g.iName[g.popUpBoard][g.popUpPin])
            self.inputPopUpMenu.post (x, y)
        except:
            l.logMsg ('Unknown error while trying to present input pop up menu', level = 'alarm')

    def setOutputPinLive (self):
        g.oForce[g.popUpBoard][g.popUpPin] = 'live'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        app.frames['gridIOPage'].updateOutputs ()

    def setOutputPinForceOn (self):
        g.oForce[g.popUpBoard][g.popUpPin] = 'force on'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        app.frames['gridIOPage'].updateOutputs ()

    def setOutputPinForceOff (self):
        g.oForce[g.popUpBoard][g.popUpPin] = 'force off'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        app.frames['gridIOPage'].updateOutputs ()

    def setInputPinLive (self):
        g.iForce[g.popUpBoard][g.popUpPin] = 'live'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        app.frames['gridIOPage'].updateInputs ()

    def setInputPinForceOn (self):
        g.iForce[g.popUpBoard][g.popUpPin] = 'force on'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        app.frames['gridIOPage'].updateInputs ()

    def setInputPinForceOff (self):
        g.iForce[g.popUpBoard][g.popUpPin] = 'force off'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        app.frames['gridIOPage'].updateInputs ()

    def fixPopUpLocation (self):
        # Given the current location of the mouse, fix it so that that
        # pop up menu appears at a useful place
        x = self.winfo_pointerx ()
        y = self.winfo_pointery ()
        x = x + 70                      # Shift it to the right and down a bit
        y = y + 70
        if (x > 1100):                  # If we're getting near the right of
            x = x - 240                 # the screen, move the menu way left
        if (y > 600):                   # Similarly if we're near the bottom
            y = y - 160                 # joggle us up a bit
        return x, y

    def getBoardnPin (self, lt):
        # Seperate out the board and pin from the supplied text
        address = lt[1:]
        b = int (address.split (',')[0])
        p = int (address.split (',')[1])
        return b, p

    def updateInput (self, b, p):
        # Given the board and pin which has changed state, see if it's used on the
        # deviceIO page and if it is, update it
        for pin in range (0, len (self.iRBtn)):
            if (self.iRBtn[pin][1] == b) & (self.iRBtn[pin][2] == p):
                self.iRBtn[pin][0].config (activebackground = app.frames['gridIOPage'].iBtn[b][p].cget ('activebackground'))
                self.iRBtn[pin][0].config (highlightbackground = app.frames['gridIOPage'].iBtn[b][p].cget ('highlightbackground'))
                self.iRBtn[pin][0].config (background = app.frames['gridIOPage'].iBtn[b][p].cget ('background'))
                self.iRBtn[pin][0].config (text = app.frames['gridIOPage'].iBtn[b][p].cget ('text'))

    def updateOutput (self, b, p):
        for pin in range (0, len (self.oRBtn)):
            if (self.oRBtn[pin][1] == b) & (self.oRBtn[pin][2] == p):
                self.oRBtn[pin][0].config (activebackground = app.frames['gridIOPage'].oBtn[b][p].cget ('activebackground'))
                self.oRBtn[pin][0].config (highlightbackground = app.frames['gridIOPage'].oBtn[b][p].cget ('highlightbackground'))
                self.oRBtn[pin][0].config (background = app.frames['gridIOPage'].oBtn[b][p].cget ('background'))
                self.oRBtn[pin][0].config (text = app.frames['gridIOPage'].oBtn[b][p].cget ('text'))

class gridIOPage(tk.Frame):
    def __init__(self, parent, controller):
        # Initalise the basic form we're going to be writing to
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # Create the on-screen widgets
        self.createWidgets()

        # Then the two timers; one to get the state of the I/O
        # and the second to create a walking pattern of outputs
        # if it's enabled.
        self.createTimers ()

        # Set up the ABE PIO boards
        self.iObj, self.oObj = self.configPorts ()

        # Start the TCP/IP server
        self.createTCPServers ()

        # Create two more timers...  These is a poor way of including the
        # TCP/IP code so that it runs along side the TK interface
        self.createTCPTimers ()

        # I used to populate the bit maps for both inputs and outputs and then
        # send these to the UI but I've deferred this to the main program
        # because it allows for all the other pages to have initalised before
        # we do inter-class calls (which fail if you do them here)
#        self.readInputs ()
#        self.readOutputs ()
#        self.updateInputs ()
#        self.updateOutputs ()

    def createTCPServers (self):
        # Before we start on the actual TCP stuff, work out the IP address
        # of eth0 which we're going to use to connect to the other devices
        # in the system
        g.ioIPAddress = os.popen ('ip addr show eth0').read().split ('inet ')[1].split ('/')[0]

        # Create two servers that can handle just one client connection
        # at a time
        #       tcpControl A bit like a CLI based interface for
        #                  setting up the IO controller
        #       tcpData    Sends/Receives I/O state information 
        self.tcpControl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Allow for the port to be re-used immediately
        self.tcpControl.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.tcpData.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

        # Bind the connection to a port
        self.tcpControl.bind ((g.ioIPAddress, c.tcpControlPort))
        self.tcpData.bind ((g.ioIPAddress, c.tcpDataPort))

        # Make all operations with the socket non-blocking. Note that this only sets
        # the way that "socket.accept" works.  There's a seperate statement for
        # actual data received
        self.tcpControl.setblocking (0)
        self.tcpData.setblocking (0)

        # Start listening for an incoming connection.  This will only allow one
        # pending connection attempt at a time.  This is NOT the thing that actually stops
        # more than one connection.
        self.tcpControl.listen (1)
        self.tcpData.listen (1)

    def tcpDataClose (self):
        if self.dataClient != None:
            print ('Got to close the TCP Data client')
            self.dataClient.close ()
            self.dataClient = None
            self.tcpData = None
            time.sleep (1)

    def tcpControlClose (self):
        if self.controlClient != None:
            print ('Got to close the TCP Control client')
            self.controlClient.close ()
            self.controlClient = None
            self.tcpControl = None
            time.sleep (1)

    def createTCPTimers (self):
        # Set up the Control port periodic timer
        self.tcpControlTimerLabel = tk.Label (self, text = 'Control Client')
        self.tcpControlTimerLabel.grid (row = 11, column = 0)
        # Set up the client socket.  This is used as a crude state machine
        # when we service the TCP port every 10mS
        self.controlClient = None
        self.tcpControlTimerLabel.after (15, self.tcpControlTimer)

        # Repeat for the Data client
        self.tcpDataTimerLabel = tk.Label (self, text = 'Data Client')
        self.tcpDataTimerLabel.grid (row = 12, column = 0)
        self.dataClient = None
        self.tcpDataTimerLabel.after (10, self.tcpDataTimer)

    def tcpControlTimer (self):
        # Service the TCP Control port server.  Tee up the next refresh of this code
        self.tcpControlTimerLabel.after (10, self.tcpControlTimer)

        # Are we connected?
        if (self.controlClient == None):
            try:
                (self.controlClient, self.address) = self.tcpControl.accept ()
            except:
                # There was an error so nothing is trying to connect
                # just return to the main program
                return
            else:
                # We got a new client connecting!!!
                if (self.controlClient != None):
                    self.tcpControlTimerLabel.config (bg = 'green')
                    self.controlClient.setblocking (0)
                    self.RxDControlBuffer = ''
                else:
                    l.logMsg ('TCP control port connect error', level = 'alarm')
                    return
        # If we get this far, we have a client connected either for the first
        # time or just on a 10mS timer.  Try to grab some bytes
        try:
            self.RxD = self.controlClient.recv (1024)
        except socket.error as e:
            err = e.args [0]
            if (err == errno.EAGAIN) or (err == errno.EWOULDBLOCK):
                # Expected error if there's nothing received
                return
            else:
                # This is a real error while waiting for incoming
                # data
                l.logMsg ('TCP control port receive error ' + e, level = 'alarm')
                return
        else:
            # There was no error so either we got some bytes or
            # the client closed the connection
            if (len (self.RxD) == 0):
                # We need to close our connection which does not require any
                # code as such, we just need to zap the clientSocket
                # so the correct code gets executed next time around
                self.controlClient = None
                self.tcpControlTimerLabel.config (bg = c.normalGrey)
            else:
                # Append the incoming bytes to the string (decode
                # converts the bytes to a string)
                self.RxDControlBuffer = self.RxDControlBuffer + self.RxD.decode ()
                # Loop round processing lines of text as long as there's a \n in the buffer
                while self.RxDControlBuffer.find ('\n') != -1:
                    # Slice off the string to process without the \r\n
                    self.lineOfText = self.RxDControlBuffer[0:self.RxDControlBuffer.find ("\n") - 1]
                    # Process the command
                    self.tcpProcessControl (self.lineOfText)
                    # Trim the command line off the begining of the buffer
                    self.RxDControlBuffer = self.RxDControlBuffer[self.RxDControlBuffer.find ('\n') + 1:]

    def tcpProcessControl (self, RxD):
        # Process the supplied command
        args = RxD.split (' ')
        if args[0] == 'test':
            if args [1] == 'on':
                self.toggleTest = True
                self.toggleLabel.config (bg = 'green')
#                self.controlClient.send (('test enabled\r\n').encode ())
            elif args [1] == 'off':
                self.toggleTest = False
                self.toggleLabel.config (bg = c.normalGrey)
#                self.controlClient.send (('test disabled\r\n').encode ())
        elif args[0] == 'exec':
            # Use the full supplied string but remove the word "exec "
            args = RxD[RxD.find (' '):].lstrip (' ')
            try:
                exec (args)
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                l.logMsg (message)
            # Refresh the state of the button text in case something got updated
            self.updateInputs ()
            self.updateOutputs ()

    def tcpDataTimer (self):
        # Service the TCP Data server.  Tee up the next refresh of this code
        self.tcpControlTimerLabel.after (10, self.tcpDataTimer)

        # Are we connected?
        if (self.dataClient == None):
            try:
                (self.dataClient, self.address) = self.tcpData.accept ()
            except:
                # There was an error so nothing is trying to connect
                # just return to the main program
                return
            else:
                # We got a new client connecting!!!
                if (self.dataClient != None):
                    self.dataClient.setblocking (0)
                    self.tcpDataTimerLabel.config (bg = 'green')
                    self.RxDDataBuffer = ''
                else:
                    l.logMsg ('TCP data port connect error', level = 'alarm')
                    return
        # If we get this far, we have a client connected either for the first
        # time or just on a 10mS timer.  Try to grab some bytes
        try:
            self.RxD = self.dataClient.recv (1024)
        except socket.error as e:
            err = e.args [0]
            if (err == errno.EAGAIN) or (err == errno.EWOULDBLOCK):
                # Expected error if there's nothing received
                return
            else:
                # This is a real error while waiting for incoming
                # data
                l.logMsg ('TCP data port receive error ' + e, level = 'alarm')
                return
        else:
            # There was no error so either we got some bytes or
            # the client closed the connection
            if (len (self.RxD) == 0):
                # We need to close our connection which does not require any
                # code as such, we just need to zap the clientSocket
                # so the correct code gets executed next time around
                self.dataClient = None
                self.tcpDataTimerLabel.config (bg = c.normalGrey)
            else:
                # Append the incoming bytes to the string (decode
                # converts the bytes to a string)
                self.RxDDataBuffer = self.RxDDataBuffer + self.RxD.decode ()
                EOLPosition = self.RxDDataBuffer.find ('\r\n')
                if (EOLPosition == -1):
                    l.logMsg ('TCP data port input is not terminated correctly', level = 'alarm')
                else:
                    # Process the command we've just received
                    self.tcpProcessData (self.RxDDataBuffer[0:EOLPosition])
                    # Trim the command line off the begining of the buffer
                    self.RxDDataBuffer = self.RxDDataBuffer[EOLPosition + 2:]
                    if len (self.RxDDataBuffer) > 0:
                        l.logMsg ('TCP data port  RxDBuffer is not empty!')

    def tcpProcessData (self, RxD):
        # Process incoming data change commands
        args = RxD.split (' ')

    def readInputs (self):
        # Using a list of objects able to talk to the PIO boards,
        # update the global iState list
        # Pin zero of the board is on the left, at [0]

        # Go through each input board and read the state of the 16 pins
        # The 16 pins are read in two 8 bit reads
        for board in range (0, len (self.iObj)):
            # Form a 16 bit number from 2 * 8 bit numbers
            image = self.iObj[board].read_port (1) << 8
            image = image + self.iObj[board].read_port (0)
            # Now populate the global iState
            for pin in range (0, c.pinsPerBoard):
                if (pow (2, pin) & image) != 0:
                    g.iState[board][pin] = 'off'
                else:
                    g.iState[board][pin] = 'on'

    def readOutputs (self):
        # See notes on "readInputs" above. This does the same for the outputs
        for board in range (0, len (self.oObj)):
            image = self.oObj[board].read_port (1) << 8
            image = image + self.oObj[board].read_port (0)
            for pin in range (0, c.pinsPerBoard):
                if (pow (2, pin) & image) != 0:
                    g.oState[board][pin] = 'on'
                else:
                    g.oState[board][pin] = 'off'

    def updateInputs (self):
        # Refresh the on-screen state of the inputs if we need to

        # Set a flag indicating that at least one thing changed so we know if to do
        # an output to the TCP data client
        somethingChanged = False
        for board in range (0, len (c.iBoard)):
            for pin in range (0, c.pinsPerBoard):
                # Figure out the current full button text
                btnText = self.iText (board, pin)
                # See if it's changed from the current value
                if (self.iBtn[board][pin].cget ('text') != btnText):
                    # Update the button object
                    self.iBtn[board][pin].config (text = btnText)
                    g.oldiBtnText[board][pin] = btnText
                    # Set the state of the input pin...  This does not actually do anything
                    # apart from update the colours of the buttons on the UI
                    self.setInputPin (board, pin)
                    # Call a method in the deviceIOPage to see if this changed pin is
                    # being displayed.  If it is, then update it.
                    app.frames['deviceIOPage'].updateInput (board, pin)
                    somethingChanged = True
        if somethingChanged == True:
            self.tcpSendIOState ('IO update sent:  Change of input state')

    def updateOutputs (self):
        # Refresh the on-screen state of the outputs and also the actual output if required
        somethingChanged = False
        for board in range (0, len (c.oBoard)):
            for pin in range (0, c.pinsPerBoard):
                btnText = self.oText (board, pin)
                if (self.oBtn[board][pin].cget ('text') != btnText):
                    self.oBtn[board][pin].config (text = btnText)
                    g.oldoBtnText[board][pin] = btnText
                    # Set the state of the output pin even though it might be the same
                    # (e.g. If the change in text was the pin name)
                    self.setOutputPin (board, pin)
                    # Call a method in the deviceIOPage to see if this changed pin is
                    # being displayed.  If it is, then update it.
                    app.frames['deviceIOPage'].updateOutput(board, pin)
                    somethingChanged = True
        if somethingChanged == True:
           self.tcpSendIOState ('IO update sent:  Change of output state')

    def setOutputPin (self, bOput, pOput):
        # Set the supplied board / pin (starting from zero) to the correct state
        # Don't forget that the AB driver refers to pins starting from 1
        if (g.oForce[bOput][pOput] == 'force on'):
            self.oObj[bOput].write_pin (pOput + 1, 1)
            self.oBtn[bOput][pOput].config (bg = 'red3')
            self.oBtn[bOput][pOput].config (activebackground = 'red')
            self.oBtn[bOput][pOput].config (highlightbackground = 'blue')
        elif (g.oForce[bOput][pOput] == 'force off'):
            self.oObj[bOput].write_pin (pOput + 1, 0)
            self.oBtn[bOput][pOput].config (bg = c.normalGrey)
            self.oBtn[bOput][pOput].config (activebackground = c.brightGrey)
            self.oBtn[bOput][pOput].config (highlightbackground = 'blue')
        elif (g.oForce[bOput][pOput] == 'live'):
            if (g.oState[bOput][pOput] == 'on'):
                self.oObj[bOput].write_pin (pOput + 1, 1)
                self.oBtn[bOput][pOput].config (bg = 'red3')
                self.oBtn[bOput][pOput].config (activebackground = 'red')
                self.oBtn[bOput][pOput].config (highlightbackground = c.normalGrey)
            else:
                self.oObj[bOput].write_pin (pOput + 1, 0)
                self.oBtn[bOput][pOput].config (bg = c.normalGrey)
                self.oBtn[bOput][pOput].config (activebackground = c.brightGrey)
                self.oBtn[bOput][pOput].config (highlightbackground = c.normalGrey)
        else:
            l.logMsg ('Illegal g.oForce state', level = 'alarm')

    def setInputPin (self, bOput, pOput):
        # This is very similar to the output case above but this does not actually force any
        # hardware into a specific state.  It only updates the colours on the UI
        if (g.iForce[bOput][pOput] == 'force on'):
            self.iBtn[bOput][pOput].config (bg = 'red3')
            self.iBtn[bOput][pOput].config (activebackground = 'red')
            self.iBtn[bOput][pOput].config (highlightbackground = 'blue')
        elif (g.iForce[bOput][pOput] == 'force off'):
            self.iBtn[bOput][pOput].config (bg = c.normalGrey)
            self.iBtn[bOput][pOput].config (activebackground = c.brightGrey)
            self.iBtn[bOput][pOput].config (highlightbackground = 'blue')
        elif (g.iForce[bOput][pOput] == 'live'):
            if (g.iState[bOput][pOput] == 'on'):
                self.iBtn[bOput][pOput].config (bg = 'red3')
                self.iBtn[bOput][pOput].config (activebackground = 'red')
                self.iBtn[bOput][pOput].config (highlightbackground = c.normalGrey)
            else:
                self.iBtn[bOput][pOput].config (bg = c.normalGrey)
                self.iBtn[bOput][pOput].config (activebackground = c.brightGrey)
                self.iBtn[bOput][pOput].config (highlightbackground = c.normalGrey)
        else:
            l.logMsg ('Illegal g.iForce state', level = 'alarm')

    def configPorts(self):
        # Set up the objects that will interface to the ABE driver and then set their
        # direction

        # These lists contain the objects created by the program to interface to the
        # ABE driver
        oB = []
        iB = []

        # Let's do the inputs first
        for port in c.iBoard:
            # Append the port driver to the end of the port driver list
            iB = iB + [IOPi (port)]

        # Now let's set up the outputs
        for port in c.oBoard:
            oB = oB + [IOPi (port)]

        # Now we're going to set up all the input ports to have pull up
        for port in iB:
            port.set_port_direction(0, 0xFF)
            port.set_port_direction(1, 0xFF)
            port.set_port_pullups(0, 0xFF)
            port.set_port_pullups(1, 0xFF)

        # And now set all the outputs up
        for port in oB:
            port.set_port_direction(0, 0x00)
            port.set_port_direction(1, 0x00)
            port.write_port (0, 0x00)
            port.write_port (1, 0x00)

        return iB, oB

    def createTimers (self):
        # Initialise the timer.  For the moment, I create a little label top
        # left and hang the timer off that; I don't know how to create a
        # null widget
        self.ioTimerLabel = tk.Label (self, text = 'I/O Refresh')
        self.ioTimerLabel.grid (row = 13, column = 0)
        self.ioTimerLabel.after (1000, self.ioRefreshTimer)

        # Now create a timer which toggles the outputs
        self.toggleLabel = tk.Label (self, text = 'Toggle Test')
        self.toggleLabel.grid (row = 14, column = 0)
        self.toggleLabel.after (2000, self.refreshToggle)
        self.toggleBoard = 0
        self.togglePin = 0
        self.toggleTest = False

        # Set up a simple state machine that decides what to do when
        # The ioRefresh timer expires
        self.ioRefreshState = 0

    def ioRefreshTimer (self):
        # This routine gets called 10 times a second!
        self.ioTimerLabel.after (100, self.ioRefreshTimer)
        if self.ioRefreshState == 0:
            self.readInputs ()
            self.updateInputs ()
            # self.readOutputs ()
            self.updateOutputs ()
            # Toggle the on-screen prompt so you know it's working
            if (self.ioTimerLabel.cget ('bg') == 'green'):
                self.ioTimerLabel.config (bg = c.normalGrey)
            else:
                self.ioTimerLabel.config (bg = 'green')
            # if we're connected to the TCP client then output a digest
            # of the information
            self.tcpSendIOState ('IO update sent:  Periodic output')
        elif (self.ioRefreshState > 0) and (self.ioRefreshState < 9):
            self.readInputs ()
            self.updateInputs ()
        # Bump and wrap the state machine (if you can call it that :))
        self.ioRefreshState += 1
        if self.ioRefreshState == 10:
            self.ioRefreshState = 0

    def tcpSendIOState (self, reason):
        # Only do anything if the data client is connected
        if self.dataClient != None:
            # Log the reason for sending the I/O state if there is one
#            if len (reason) > 0:
#                l.logMsg (reason)
#            # Send the reason to the control client if it's connected
#            if (self.controlClient != None) and (len(reason) > 0):
#                self.controlClient.send ((str(dt.datetime.now ())[11:] + ' ' + reason + '\r\n').encode ())
#           # Then send a digest of the state, force and name
            self.dataClient.send (('g.iBoards = ' + str (len (c.iBoard)) + '\r\n').encode ())
            self.dataClient.send (('g.oBoards = ' + str (len (c.oBoard)) + '\r\n').encode ())

            for board in range (0, len (g.oState)):
                self.dataClient.send (('g.oState [' + str (board) + '] = ' + str (g.oState[board]) + '\r\n').encode ())
            for board in range (0, len (g.oForce)):
                self.dataClient.send (('g.oForce [' + str (board) + '] = ' + str (g.oForce[board]) + '\r\n').encode ())
            for board in range (0, len (g.oName)):
                self.dataClient.send (('g.oName [' + str (board) + '] = ' + str (g.oName[board]) + '\r\n').encode ())

            for board in range (0, len (g.iState)):
                self.dataClient.send (('g.iState [' + str (board) + '] = ' + str (g.iState[board]) + '\r\n').encode ())
            for board in range (0, len (g.iForce)):
                self.dataClient.send (('g.iForce [' + str (board) + '] = ' + str (g.iForce[board]) + '\r\n').encode ())
            for board in range (0, len (g.iName)):
                self.dataClient.send (('g.iName [' + str (board) + '] = ' + str (g.iName[board]) + '\r\n').encode ())

    def refreshToggle (self):
        # Only keep the test running after this go if the test is still
        # enabled.
        self.toggleLabel.after (100, self.refreshToggle)

        # Exit if the test is not running
        if self.toggleTest == False:
            return

        # Toggle the state of the current output pin
        if (g.oForce[self.toggleBoard][self.togglePin] == 'live'):
            g.oForce[self.toggleBoard][self.togglePin] = 'force on'
        else:
            g.oForce[self.toggleBoard][self.togglePin] = 'live'
        # Update the on-screen outputs
        self.updateOutputs ()

        # Toggle the state of the current input pin
        if (g.iForce[self.toggleBoard][self.togglePin] == 'live'):
            g.iForce[self.toggleBoard][self.togglePin] = 'force on'
        else:
            g.iForce[self.toggleBoard][self.togglePin] = 'live'
        # Update the on-screen outputs
        self.updateInputs ()

        # Point at the next pin wrapping both the board and pin if required
        self.togglePin += 1
        if (self.togglePin == c.pinsPerBoard):
            self.togglePin = 0
            self.toggleBoard += 1
            if (self.toggleBoard == len (c.oBoard)):
                self.toggleBoard = 0

    def createWidgets(self):
        # Create an array of buttons with titles for both the rows and cols
        # First create the row/col titles
        for board in range (0, len(c.oBoard)):
            self.lbl = tk.Label (self, text = 'OP ' + str (board))
            self.lbl.grid (row = board + 1, column = 0)
            for pin in range (0, c.pinsPerBoard):
                self.lbl = tk.Label (self, text = 'Pin ' + str (pin))
                self.lbl.grid (row = 0, column = pin + 1)

        # Now create an list of lists containing the board/pin buttons for each
        # output
        self.oBtn = []
        for board in range (0, len (c.oBoard)):
            # This is a blank list (which will contain a list of 16 items in a moment)
            self.oBtn.append ([])
            for pin in range (0, c.pinsPerBoard):
                # Add the new item.  I do this in two steps but this could be done without
                # the = 0 below; I just thought it made it easier to read.
                self.oBtn[board].append (0)
                self.oBtn[board][pin] = tk.Button (self, height = 4, width = 5,
                            text = self.oText (board, pin), anchor = 'w', justify = tk.LEFT,
                            background = c.normalGrey, activebackground = c.brightGrey,
                            command = lambda x = board, y = pin: self.outputPopUpCallBack (x, y))
                self.oBtn[board][pin].grid(row = board + 1, column = pin + 1)

        # Create a hard coded empty row which seperates the outputs and inputs
        self.lbl = tk.Label (self, text = ' ')
        self.lbl.grid (row = 5, column = 0)

        # Now do the same for the input pins
        for board in range (0, len(c.iBoard)):
            self.lbl = tk.Label (self, text = 'IP ' + str (board))
            self.lbl.grid (row = board + 7, column = 0)
            for pin in range (0, c.pinsPerBoard):
                self.lbl = tk.Label (self, text = 'Pin ' + str (pin))
                self.lbl.grid (row = 6, column = pin + 1)

        # Now create an list of lists containing the board/pin buttons for each
        # input
        self.iBtn = []
        for board in range (0, len (c.iBoard)):
            # This is a blank list (which will contain a list of 16 items in a moment)
            self.iBtn.append ([])
            for pin in range (0, c.pinsPerBoard):
                # Add the new item.  I do this in two steps but this could be done without
                # the = 0 below; I just thought it made it easier to read.
                self.iBtn[board].append (0)
                self.iBtn[board][pin] = tk.Button (self, height = 4, width = 5,
                            text = self.iText (board, pin), anchor = 'w', justify = tk.LEFT,
                            background = c.normalGrey, activebackground = c.brightGrey,
                            command = lambda x = board, y = pin : self.inputPopUpCallBack (x, y))
                self.iBtn[board][pin].grid(row = board + 7, column = pin + 1)

        # Create the buttons that allow movement to other pages, reboot and exit
        self.messageBtn = tk.Button (self, text = 'Messages', anchor = 'w', justify = tk.LEFT,
                            height = 2, background = c.normalGrey, activebackground = c.brightGrey,
                            command = lambda: self.controller.show_frame ('messagePage'))
        self.messageBtn.grid (row = 12, column = 1, rowspan = 3, columnspan = 2)

        self.deviceIOBtn = tk.Button (self, text = 'Device I/O', anchor = 'w', justify = tk.LEFT,
                            height = 2, background = c.normalGrey, activebackground = c.brightGrey,
                            command = lambda: self.controller.show_frame ('deviceIOPage'))
        self.deviceIOBtn.grid (row = 12, column = 3, rowspan = 3, columnspan = 2)

        self.deviceIOBtn = tk.Button (self, text = 'Exit', anchor = 'e', justify = tk.RIGHT,
                            height = 2, background = c.normalGrey, activebackground = c.brightGrey,
                            command = lambda: self.exitSoftware ())
        self.deviceIOBtn.grid (row = 12, column = 13, rowspan = 3, columnspan = 2)

        self.deviceIOBtn = tk.Button (self, text = 'Reboot', anchor = 'e', justify = tk.RIGHT,
                            height = 2, background = c.normalGrey, activebackground = c.brightGrey,
                            command = lambda: self.rebootMachine ())
        self.deviceIOBtn.grid (row = 12, column = 15, rowspan = 3, columnspan = 2)


        # Create a pop up menu to control the forced state of a selected pin
        self.outputPopUpMenu = tk.Menu (self, tearoff = 0)
        self.outputPopUpMenu.config (font = (None, 20))
        self.outputPopUpMenu.add_command (label = 'output')
        self.outputPopUpMenu.entryconfigure (0, state = tk.DISABLED)
        self.outputPopUpMenu.add_command (label = 'live', command = self.setOutputPinLive)
        self.outputPopUpMenu.add_command (label = 'force on', command = self.setOutputPinForceOn)
        self.outputPopUpMenu.add_command (label = 'force off', command = self.setOutputPinForceOff)

        self.inputPopUpMenu = tk.Menu (self, tearoff = 0)
        self.inputPopUpMenu.config (font = (None, 20))
        self.inputPopUpMenu.add_command (label = 'input')
        self.inputPopUpMenu.entryconfigure (0, state = tk.DISABLED)
        self.inputPopUpMenu.add_command (label = 'live', command = self.setInputPinLive)
        self.inputPopUpMenu.add_command (label = 'force on', command = self.setInputPinForceOn)
        self.inputPopUpMenu.add_command (label = 'force off', command = self.setInputPinForceOff)

        # Make the left mouse button run the following routine
#        self.bind ("<Button-1>", self.popup)

    def outputPopUpCallBack (self, b, p):
        # Given the current mouse location, fix the location that the menu will be placed
        x, y = self.fixPopUpLocation ()

        # We get the board and pin as parameters.  Make these visable to the selected menu
        # items through these variables
        g.popUpBoard = b
        g.popUpPin = p

        # There might already be another pop up menu being displayed so remove it.  This does
        # not seem to error if it's not being displayed which is good I guess
        self.inputPopUpMenu.unpost ()

        try:
            # Fix the name of the menu to be the name of the pin we're trying to change state
            # on then display the menu
            self.outputPopUpMenu.entryconfigure (0, label = g.oName[b][p])
            self.outputPopUpMenu.post (x, y)
        except:
            l.logMsg ('Unknown error while trying to present output pop up menu', level = 'alarm')

    def exitSoftware (self):
        sys.exit ()

    def rebootMachine (self):
        os.system ('sudo reboot')

    def inputPopUpCallBack (self, b, p):
        # Given the current mouse location, fix the location that the menu will be placed
        x, y = self.fixPopUpLocation ()

        g.popUpBoard = b
        g.popUpPin = p
        self.outputPopUpMenu.unpost ()

        try:
            self.inputPopUpMenu.entryconfigure (0, label = g.iName[b][p])
            self.inputPopUpMenu.post (x, y)
        except:
            l.logMsg ('Unknown error while trying to present input pop up menu', level = 'alarm')

    def setOutputPinLive (self):
        g.oForce[g.popUpBoard][g.popUpPin] = 'live'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateOutputs ()

    def setOutputPinForceOn (self):
        g.oForce[g.popUpBoard][g.popUpPin] = 'force on'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateOutputs ()

    def setOutputPinForceOff (self):
        g.oForce[g.popUpBoard][g.popUpPin] = 'force off'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateOutputs ()

    def setInputPinLive (self):
        g.iForce[g.popUpBoard][g.popUpPin] = 'live'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateInputs ()

    def setInputPinForceOn (self):
        g.iForce[g.popUpBoard][g.popUpPin] = 'force on'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateInputs ()

    def setInputPinForceOff (self):
        g.iForce[g.popUpBoard][g.popUpPin] = 'force off'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateInputs ()

    def fixPopUpLocation (self):
        # Given the current location of the mouse, fix it so that that
        # pop up menu appears at a useful place
        x = self.winfo_pointerx ()
        y = self.winfo_pointery ()
        x = x + 70                      # Shift it to the right and down a bit
        y = y + 70
        if (x > 1100):                  # If we're getting near the right of
            x = x - 240                 # the screen, move the menu way left
        if (y > 600):                   # Similarly if we're near the bottom
            y = y - 160                 # joggle us up a bit
        return x, y

    def oText (self, x, y):
        return (g.oState[x][y] + '\n' + g.oForce[x][y] + '\n' + g.oName[x][y])

    def iText (self, x, y):
        return (g.iState[x][y] + '\n' + g.iForce[x][y] + '\n' + g.iName[x][y])

def closeWindow ():
    # Close down the program
    app.frames['gridIOPage'].tcpDataClose ()          # Disconnect and TCP clients if they're connected
    app.frames['gridIOPage'].tcpControlClose ()
    l.logClose ()                                   # Close the log file
    sys.exit ()                                     # Return to the operating system

def testOKToRun ():
    # See if the program is already running.  This is a little bit interesting because if it is,
    # there will actually be 2 or more running at the same time so you can't just check to see
    # if 'python ioController.py is in the process table
    a = int (os.popen ('ps x|grep -c "[p]ython ioController.py"').read ())
    if (a > 1):
        print ("Program already running")
        sys.exit (1)

    # See if we have a valid DISPLAY environment variable.  This stops you attempting to run
    # the program without a valid X display attached to the terminal session
    try:
        os.environ ['DISPLAY']
    except KeyError:
        print ('No X Display accociated with this terminal session so program cannot run')
        sys.exit (1)

def main ():
    # Work out if the program is already running and exit if it is
    testOKToRun ()
    global app
    app = sampleApp ()                              # Set up the TK environment
    app.protocol ('WM_DELETE_WINDOW', closeWindow)  # Call this routine when someone exits the program

    # Read the IO and update the buttons as required.  Also send TCP output if required.
    app.frames['gridIOPage'].readInputs ()
    app.frames['gridIOPage'].readOutputs ()
    app.frames['gridIOPage'].updateInputs ()
    app.frames['gridIOPage'].updateOutputs ()

    l.logMsg ('')
    l.logMsg ('Starting on-screen message page')
    l.logMsg ('')
    l.logMsg ('IO Controller IP Address: ' + g.ioIPAddress)

    app.mainloop()                                  # and finally let tkInter run...

if __name__ == '__main__':
    main ()
