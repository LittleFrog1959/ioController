# IO control program
# Latest version here   https://github.com/LittleFrog1959/ioController
# Credits here          https://github.com/LittleFrog1959/ioController/wiki/Credits
# Test change

import tkinter as tk
from tkinter import font  as tkfont

import socket
import os
import errno
import datetime as dt

# The AB Electronics driver for the PIO board
from IOPi import IOPi

# A globally visable pair lists describing the I2C ports used by the
# I/O boards
oBoard = [0x20, 0x22, 0x24, 0x26]
iBoard = [0x21, 0x23, 0x25, 0x27]

# Global creates:
# - A pair of lists containing the true state of the input or output pins
#       iState and oState. Each element can have the following values;
#           "null", "on", "off"
# - A pair of lists containing the old version of the 3 lines of text in
#   each UI button.  This is used to detect changes of state as well as
#   any forced state / name changes
# - A pair of lists containing the forced state of pins
#       iForce and oForce that can have the following values;
#           "live", "forced on", "forced off"
# - A pair of lists contained in the name of the pins
#       iName and oName which are inititally set to a simple string
#       of the form "[direction]button, pin"
oState = []
oldoBtnText = []
oForce = []
oName = []
for board in range (0, len(oBoard)):
    # Create a new row (which is the "board" axis)
    oState.append ([])
    oldoBtnText.append ([])
    oForce.append ([])
    oName.append ([])
    # Then populate each row with 16 values (for pin 0-15)
    for pin in range (0, 16):
        oState[board].append ('null')
        oldoBtnText[board].append ('')
        oForce[board].append ('live')
        oName[board].append ('O' + str (board) + "," + str (pin))

iState = []
oldiBtnText = []
iForce = []
iName = []
for board in range (0, len(iBoard)):
    iState.append ([])
    oldiBtnText.append ([])
    iForce.append ([])
    iName.append ([])
    for pin in range (0, 16):
        iState[board].append ('null')
        oldiBtnText[board].append ('')
        iForce[board].append ('live')
        iName[board].append ('I' + str (board) + "," + str (pin))

# Very simple logging system.  Just formats the supplied message with a timestamp
# and a level (which defaults to "debug").  Outputs the message to a TCP data client
# if it's connected
def log (message, level = 'debug'):
    t = str (dt.datetime.now ())
    m = t + " " + "{:<10}".format (level) + message
    print (m)
#    if dataClient != None:
#        dataClient.send (m + '\r\n')

class sampleApp (tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        try:
            displayReference = os.environ['DISPLAY']
        except:
            displayReference = ""

        if (displayReference == ":0.0"):
            self.geometry ('1280x800')
            self.config (cursor = "none")
            self.attributes('-fullscreen', True)
        else:
            self.geometry ('1280x800')

        container = tk.Frame (self)
        container.pack (side = 'top', fill = 'both', expand = True)
        container.grid_rowconfigure (0, weight = 1)
        container. grid_columnconfigure (0, weight = 1)

        self.frames = {}
        for F in (mainPage, alarmPage, rowIOPage):
            page_name = F.__name__
            frame = F (parent = container, controller = self)
            self.frames [page_name] = frame
            frame.grid (row = 0, column = 0, sticky = 'nsew')
        self.show_frame ('mainPage')

    def show_frame (self, page_name):
        frame = self.frames [page_name]
        frame.tkraise ()

class alarmPage (tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.labelx = tk.Label(self, text="This is page 1")
        self.labelx.pack(side="top", fill="x", pady=10)

        self.labelx.after (1000, self.toggleLabel)

        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("mainPage"))
        button.pack()

    def toggleLabel (self):
        self.labelx.after (1000, self.toggleLabel)
        log (str (oName[0][0]))
        if (self.labelx.cget ('text') == "Page 1"):
            self.labelx.config (text = "Page 1 +")
        else:
            self.labelx.config (text = "Page 1")

class rowIOPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 2")
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("mainPage"))
        button.pack()

class mainPage(tk.Frame):
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

        # Populate the bit maps for both inputs and outputs and then
        # send these to the UI
        self.readInputs ()
        self.readOutputs ()
        self.updateInputs ()
        self.updateOutputs ()

    def createTCPServers (self):
        # Before we start on the actual TCP stuff, work out the IP address
        # of eth0 which we're going to use to connect to the other devices
        # in the system
        IPAddress = os.popen ('ip addr show eth0').read().split ("inet ")[1].split ("/")[0]

        # Create two servers that can handle just one client connection
        # at a time
        #       tcpControl A bit like a CLI based interface for
        #                  setting up the IO controller
        #       tcpData    Sends/Receives I/O state information 
        self.tcpControl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpData = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the connection to a port
        self.tcpControl.bind ((IPAddress, 10000))
        self.tcpData.bind ((IPAddress, 10001))

        # Allow for the port to be re-used immediately
        self.tcpControl.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.tcpData.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

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

    def createTCPTimers (self):
        # Set up the Control port periodic timer
        self.tcpControlTimerLabel = tk.Label (self, text = "Control Client")
        self.tcpControlTimerLabel.grid (row = 11, column = 0)
        # Set up the client socket.  This is used as a crude state machine
        # when we service the TCP port every 10mS
        self.controlClient = None
        self.tcpControlTimerLabel.after (15, self.tcpControlTimer)

        # Repeat for the Data client
        self.tcpDataTimerLabel = tk.Label (self, text = "Data Client")
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
                    self.RxDControlBuffer = ""
                else:
                    log ("TCP control port connect error", level = 'alarm')
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
                log ("TCP control port receive error " + e, level = 'alarm')
                return
        else:
            # There was no error so either we got some bytes or
            # the client closed the connection
            if (len (self.RxD) == 0):
                # We need to close our connection which does not require any
                # code as such, we just need to zap the clientSocket
                # so the correct code gets executed next time around
                self.controlClient = None
                self.tcpControlTimerLabel.config (bg = '#d9d9d9')
            else:
                # Append the incoming bytes to the string (decode
                # converts the bytes to a string)
                self.RxDControlBuffer = self.RxDControlBuffer + self.RxD.decode ()
                EOLPosition = self.RxDControlBuffer.find ('\r\n')
                if (EOLPosition == -1):
                    log ('TCP control port input is not terminated correctly', level = 'alarm')
                else:
                    # Process the command we've just received
                    self.tcpProcessControl (self.RxDControlBuffer[0:EOLPosition])
                    # Trim the command line off the begining of the buffer
                    self.RxDControlBuffer = self.RxDControlBuffer[EOLPosition + 2:]
                    if len (self.RxDControlBuffer) > 0:
                        log ('TCP control port RxDBuffer is not empty!')

    def tcpProcessControl (self, RxD):
        # Process the supplied command
        args = RxD.split (' ')
        if args[0] == 'test':
            if args [1] == 'on':
                self.toggleTest = True
                self.toggleLabel.config (bg = 'green')
#                self.controlClient.send (("test enabled\r\n").encode ())
            elif args [1] == 'off':
                self.toggleTest = False
                self.toggleLabel.config (bg = '#d9d9d9')
#                self.controlClient.send (("test disabled\r\n").encode ())
        elif args[0] == 'exec':
            # Use the full supplied string but remove the word "exec "
            args = RxD[RxD.find (" "):].lstrip (" ")
            exec (args)
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
                    self.tcpControlTimerLabel.config (bg = 'green')
                    self.RxDDataBuffer = ""
                else:
                    log ("TCP data port connect error", level = 'alarm')
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
                log ("TCP data port receive error " + e, level = 'alarm')
                return
        else:
            # There was no error so either we got some bytes or
            # the client closed the connection
            if (len (self.RxD) == 0):
                # We need to close our connection which does not require any
                # code as such, we just need to zap the clientSocket
                # so the correct code gets executed next time around
                self.dataClient = None
                self.tcpControlTimerLabel.config (bg = 'green')
            else:
                # Append the incoming bytes to the string (decode
                # converts the bytes to a string)
                self.RxDDataBuffer = self.RxDDataBuffer + self.RxD.decode ()
                EOLPosition = self.RxDDataBuffer.find ('\r\n')
                if (EOLPosition == -1):
                    log ('TCP data port input is not terminated correctly', level = 'alarm')
                else:
                    # Process the command we've just received
                    self.tcpProcessData (self.RxDDataBuffer[0:EOLPosition])
                    # Trim the command line off the begining of the buffer
                    self.RxDDataBuffer = self.RxDDataBuffer[EOLPosition + 2:]
                    if len (self.RxDDataBuffer) > 0:
                        log ('TCP data port  RxDBuffer is not empty!')

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
            for pin in range (0, 16):
                if (pow (2, pin) & image) != 0:
                    iState[board][pin] = 'off'
                else:
                    iState[board][pin] = 'on'

    def readOutputs (self):
        # See notes on "readInputs" above. This does the same for the outputs
        for board in range (0, len (self.oObj)):
            image = self.oObj[board].read_port (1) << 8
            image = image + self.oObj[board].read_port (0)
            for pin in range (0, 16):
                if (pow (2, pin) & image) != 0:
                    oState[board][pin] = 'on'
                else:
                    oState[board][pin] = 'off'

    def updateInputs (self):
        # Refresh the on-screen state of the inputs if we need to

        # Set a flag indicating that at least one thing changed so we know if to do
        # an output to the TCP data client
        somethingChanged = False
        for board in range (0, len (iBoard)):
            for pin in range (0, 16):
                # Figure out the current full button text
                btnText = self.iText (board, pin)
                # See if it's changed from the current value
                if (self.iBtn[board][pin].cget ('text') != btnText):
                    # Update the button object
                    self.iBtn[board][pin].config (text = btnText)
                    oldiBtnText[board][pin] = btnText
                    # Set the state of the input pin...  This does not actually do anything
                    # apart from update the colours of the buttons on the UI
                    self.setInputPin (board, pin)
                    somethingChanged = True
        if somethingChanged == True:
            self.tcpSendIOState ('IO update sent:  Change of input state')

    def updateOutputs (self):
        # Refresh the on-screen state of the outputs and also the actual output if required
        somethingChanged = False
        for board in range (0, len (oBoard)):
            for pin in range (0, 16):
                btnText = self.oText (board, pin)
                if (self.oBtn[board][pin].cget ('text') != btnText):
                    self.oBtn[board][pin].config (text = btnText)
                    oldoBtnText[board][pin] = btnText
                    # Set the state of the output pin even though it might be the same
                    # (e.g. If the change in text was the pin name)
                    self.setOutputPin (board, pin)
                    somethingChanged = True
        if somethingChanged == True:
           self.tcpSendIOState ('IO update sent:  Change of output state')

    def setOutputPin (self, bOput, pOput):
        # Set the supplied board / pin (starting from zero) to the correct state
        # Don't forget that the AB driver refers to pins starting from 1
        if (oForce[bOput][pOput] == 'force on'):
            self.oObj[bOput].write_pin (pOput + 1, 1)
            self.oBtn[bOput][pOput].config (bg = "red3")
            self.oBtn[bOput][pOput].config (activebackground = "red")
            self.oBtn[bOput][pOput].config (highlightbackground = "blue")
        elif (oForce[bOput][pOput] == 'force off'):
            self.oObj[bOput].write_pin (pOput + 1, 0)
            self.oBtn[bOput][pOput].config (bg = "#d9d9d9")
            self.oBtn[bOput][pOput].config (activebackground = "#e9e9e9")
            self.oBtn[bOput][pOput].config (highlightbackground = "blue")
        elif (oForce[bOput][pOput] == 'live'):
            if (oState[bOput][pOput] == 'on'):
                self.oObj[bOput].write_pin (pOput + 1, 1)
                self.oBtn[bOput][pOput].config (bg = "red3")
                self.oBtn[bOput][pOput].config (activebackground = "red")
                self.oBtn[bOput][pOput].config (highlightbackground = "#d9d9d9")
            else:
                self.oObj[bOput].write_pin (pOput + 1, 0)
                self.oBtn[bOput][pOput].config (bg = "#d9d9d9")
                self.oBtn[bOput][pOput].config (activebackground = "#e9e9e9")
                self.oBtn[bOput][pOput].config (highlightbackground = "#d9d9d9")
        else:
            log ('Illegal oForce state', level = 'alarm')

    def setInputPin (self, bOput, pOput):
        # This is very similar to the output case above but this does not actually force any
        # hardware into a specific state.  It only updates the colours on the UI
        if (iForce[bOput][pOput] == 'force on'):
            self.iBtn[bOput][pOput].config (bg = "red3")
            self.iBtn[bOput][pOput].config (activebackground = "red")
            self.iBtn[bOput][pOput].config (highlightbackground = "blue")
        elif (iForce[bOput][pOput] == 'force off'):
            self.iBtn[bOput][pOput].config (bg = "#d9d9d9")
            self.iBtn[bOput][pOput].config (activebackground = "#e9e9e9")
            self.iBtn[bOput][pOput].config (highlightbackground = "blue")
        elif (iForce[bOput][pOput] == 'live'):
            if (iState[bOput][pOput] == 'on'):
                self.iBtn[bOput][pOput].config (bg = "red3")
                self.iBtn[bOput][pOput].config (activebackground = "red")
                self.iBtn[bOput][pOput].config (highlightbackground = "#d9d9d9")
            else:
                self.iBtn[bOput][pOput].config (bg = "#d9d9d9")
                self.iBtn[bOput][pOput].config (activebackground = "#e9e9e9")
                self.iBtn[bOput][pOput].config (highlightbackground = "#d9d9d9")
        else:
            log ('Illegal iForce state', level = 'alarm')

    def configPorts(self):
        # Set up the objects that will interface to the ABE driver and then set their
        # direction

        # These lists contain the objects created by the program to interface to the
        # ABE driver
        oB = []
        iB = []

        # Let's do the inputs first
        for port in iBoard:
            # Append the port driver to the end of the port driver list
            iB = iB + [IOPi (port)]

        # Now let's set up the outputs
        for port in oBoard:
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
        self.ioTimerLabel = tk.Label (self, text = "I/O Refresh")
        self.ioTimerLabel.grid (row = 13, column = 0)
        self.ioTimerLabel.after (1000, self.ioRefreshTimer)

        # Now create a timer which toggles the outputs
        self.toggleLabel = tk.Label (self, text = "Toggle Test")
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
            # Toggle the on-screen prompt so you know it's working
            if (self.ioTimerLabel.cget ('bg') == 'green'):
                self.ioTimerLabel.config (bg = '#d9d9d9')
            else:
                self.ioTimerLabel.config (bg = 'green')
            self.readInputs ()
            self.updateInputs ()
            # self.readOutputs ()
            self.updateOutputs ()
            # if we're connected to the TCP client then output a digest
            # of the information
#            self.tcpSendIOState ('IO update sent:  Periodic output')
            self.tcpSendIOState ('')
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
            # Send the reason to the control client if it's connected
 #           if (self.controlClient != None) and (len(reason) > 0):
 #               self.controlClient.send ((str(dt.datetime.now ())[11:] + ' ' + reason + '\r\n').encode ())
            # Then send a digest of the state, force and name
            self.dataClient.send (('iBoards = ' + str (len (iBoard)) + '\r\n').encode ())
            self.dataClient.send (('oBoards = ' + str (len (oBoard)) + '\r\n').encode ())

            for board in range (0, len (oState)):
                self.dataClient.send (('oState [' + str (board) + "] = " + str (oState[board]) + '\r\n').encode ())
            for board in range (0, len (oForce)):
                self.dataClient.send (('oForce [' + str (board) + "] = " + str (oForce[board]) + '\r\n').encode ())
            for board in range (0, len (oName)):
                self.dataClient.send (('oName [' + str (board) + "] = " + str (oName[board]) + '\r\n').encode ())

            for board in range (0, len (iState)):
                self.dataClient.send (('iState [' + str (board) + "] = " + str (iState[board]) + '\r\n').encode ())
            for board in range (0, len (iForce)):
                self.dataClient.send (('iForce [' + str (board) + "] = " + str (iForce[board]) + '\r\n').encode ())
            for board in range (0, len (iName)):
                self.dataClient.send (('iName [' + str (board) + "] = " + str (iName[board]) + '\r\n').encode ())

    def refreshToggle (self):
        # Only keep the test running after this go if the test is still
        # enabled.
        self.toggleLabel.after (100, self.refreshToggle)

        # Exit if the test is not running
        if self.toggleTest == False:
            return

        # Toggle the state of the current output pin
        if (oForce[self.toggleBoard][self.togglePin] == "live"):
            oForce[self.toggleBoard][self.togglePin] = "force on"
        else:
            oForce[self.toggleBoard][self.togglePin] = "live"
        # Update the on-screen outputs
        self.updateOutputs ()

        # Toggle the state of the current input pin
        if (iForce[self.toggleBoard][self.togglePin] == "live"):
            iForce[self.toggleBoard][self.togglePin] = "force on"
        else:
            iForce[self.toggleBoard][self.togglePin] = "live"
        # Update the on-screen outputs
        self.updateInputs ()

        # Point at the next pin wrapping both the board and pin if required
        self.togglePin += 1
        if (self.togglePin == 16):
            self.togglePin = 0
            self.toggleBoard += 1
            if (self.toggleBoard == len (oBoard)):
                self.toggleBoard = 0

    def createWidgets(self):
        # Create an array of buttons with titles for both the rows and cols
        # First create the row/col titles
        for board in range (0, len(oBoard)):
            self.lbl = tk.Label (self, text = 'OP ' + str (board))
            self.lbl.grid (row = board + 1, column = 0)
            for pin in range (0, 16):
                self.lbl = tk.Label (self, text = 'Pin ' + str (pin))
                self.lbl.grid (row = 0, column = pin + 1)

        # Now create an list of lists containing the board/pin buttons for each
        # output
        self.oBtn = []
        for board in range (0, len (oBoard)):
            # This is a blank list (which will contain a list of 16 items in a moment)
            self.oBtn.append ([])
            for pin in range (0, 16):
                # Add the new item.  I do this in two steps but this could be done without
                # the = 0 below; I just thought it made it easier to read.
                self.oBtn[board].append (0)
                self.oBtn[board][pin] = tk.Button (self, height = 4, width = 5,
                            text = self.oText (board, pin), anchor = 'w', justify = tk.LEFT,
                            background = "#d9d9d9", activebackground = "#e9e9e9",
                            command = lambda x = board, y = pin: self.outputPopUpCallBack (x, y))
                self.oBtn[board][pin].grid(row = board + 1, column = pin + 1)

        # Create a hard coded empty row which seperates the outputs and inputs
        self.lbl = tk.Label (self, text = " ")
        self.lbl.grid (row = 5, column = 0)

        # Now do the same for the input pins
        for board in range (0, len(iBoard)):
            self.lbl = tk.Label (self, text = 'IP ' + str (board))
            self.lbl.grid (row = board + 7, column = 0)
            for pin in range (0, 16):
                self.lbl = tk.Label (self, text = 'Pin ' + str (pin))
                self.lbl.grid (row = 6, column = pin + 1)

        # Now create an list of lists containing the board/pin buttons for each
        # input
        self.iBtn = []
        for board in range (0, len (iBoard)):
            # This is a blank list (which will contain a list of 16 items in a moment)
            self.iBtn.append ([])
            for pin in range (0, 16):
                # Add the new item.  I do this in two steps but this could be done without
                # the = 0 below; I just thought it made it easier to read.
                self.iBtn[board].append (0)
                self.iBtn[board][pin] = tk.Button (self, height = 4, width = 5,
                            text = self.iText (board, pin), anchor = 'w', justify = tk.LEFT,
                            background = "#d9d9d9", activebackground = "#e9e9e9",
                            command = lambda x = board, y = pin : self.inputPopUpCallBack (x, y))
                self.iBtn[board][pin].grid(row = board + 7, column = pin + 1)

        # Create the buttons that allow movement to other pages
        self.alarmBtn = tk.Button (self, text = "Alarms", anchor = 'w', justify = tk.LEFT,
                            background = '#d9d9d9', activebackground = '#e9e9e9',
                            command = lambda: self.controller.show_frame ('alarmPage'))
        self.alarmBtn.grid (row = 12, column = 1, rowspan = 2)

        self.rowIOBtn = tk.Button (self, text = "Row IO", anchor = 'w', justify = tk.LEFT,
                            background = '#d9d9d9', activebackground = '#e9e9e9',
                            command = lambda: self.controller.show_frame ('rowIOPage'))
        self.rowIOBtn.grid (row = 12, column = 3, rowspan =2)

        # Create a pop up menu to control the forced state of a selected pin
        self.outputPopUpMenu = tk.Menu (self, tearoff = 0)
        self.outputPopUpMenu.config (font = (None, 20))
        self.outputPopUpMenu.add_command (label = "output")
        self.outputPopUpMenu.entryconfigure (0, state = tk.DISABLED)
        self.outputPopUpMenu.add_command (label = "live", command = self.setOutputPinLive)
        self.outputPopUpMenu.add_command (label = "force on", command = self.setOutputPinForceOn)
        self.outputPopUpMenu.add_command (label = "force off", command = self.setOutputPinForceOff)

        self.inputPopUpMenu = tk.Menu (self, tearoff = 0)
        self.inputPopUpMenu.config (font = (None, 20))
        self.inputPopUpMenu.add_command (label = "input")
        self.inputPopUpMenu.entryconfigure (0, state = tk.DISABLED)
        self.inputPopUpMenu.add_command (label = "live", command = self.setInputPinLive)
        self.inputPopUpMenu.add_command (label = "force on", command = self.setInputPinForceOn)
        self.inputPopUpMenu.add_command (label = "force off", command = self.setInputPinForceOff)

        # Make the left mouse button run the following routine
#        self.bind ("<Button-1>", self.popup)

    def outputPopUpCallBack (self, b, p):
        # Given the current mouse location, fix the location that the menu will be placed
        x, y = self.fixPopUpLocation ()

        # We get the board and pin as parameters.  Make these visable to the selected menu
        # items through these variables
        self.popupBoard = b
        self.popupPin = p

        # There might already be another pop up menu being displayed so remove it.  This does
        # not seem to error if it's not being displayed which is good I guess
        self.inputPopUpMenu.unpost ()

        try:
            # Fix the name of the menu to be the name of the pin we're trying to change state
            # on then display the menu
            self.outputPopUpMenu.entryconfigure (0, label = oName[b][p])
            self.outputPopUpMenu.post (x, y)
        except:
            log ('Unknown error while trying to present output pop up menu', level = 'alarm')

    def inputPopUpCallBack (self, b, p):
        # Given the current mouse location, fix the location that the menu will be placed
        x, y = self.fixPopUpLocation ()

        self.popupBoard = b
        self.popupPin = p
        self.outputPopUpMenu.unpost ()

        try:
            self.inputPopUpMenu.entryconfigure (0, label = iName[b][p])
            self.inputPopUpMenu.post (x, y)
        except:
            log ('Unknown error while trying to present input pop up menu', level = 'alarm')

    def setOutputPinLive (self):
        oForce[self.popupBoard][self.popupPin] = 'live'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateOutputs ()

    def setOutputPinForceOn (self):
        oForce[self.popupBoard][self.popupPin] = 'force on'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateOutputs ()

    def setOutputPinForceOff (self):
        oForce[self.popupBoard][self.popupPin] = 'force off'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateOutputs ()

    def setInputPinLive (self):
        iForce[self.popupBoard][self.popupPin] = 'live'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateInputs ()

    def setInputPinForceOn (self):
        iForce[self.popupBoard][self.popupPin] = 'force on'
        self.event_generate ('<Motion>', warp = True, x = 0, y = 0)
        self.updateInputs ()

    def setInputPinForceOff (self):
        iForce[self.popupBoard][self.popupPin] = 'force off'
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
        return (oState[x][y] + '\n' + oForce[x][y] + '\n' + oName[x][y])

    def iText (self, x, y):
        return (iState[x][y] + '\n' + iForce[x][y] + '\n' + iName[x][y])

def main ():
    app = sampleApp ()                  # Set up the TK environment
    app.mainloop()                      # and let it run...

if __name__ == '__main__':
    main ()
