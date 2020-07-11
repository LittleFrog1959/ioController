# This is a first attempt at a fully formed interface to the IO Controllers
# which will form the link between the real world IO and Robot Framework.

# The program starts off with a list of IO Controllers to connect to and every
# once in a while it attempts to connect to them.  Once it succeeds, it then
# sets up the correct interface depending on whether the link is with a Control Port
# or a Data Port (there is one of each on every IO Controller).

import curses
import sys
import socket
import time
import datetime as dt
import errno
import os

import globals
g = globals.testGlobals ()

import constants
c = constants.constants ()

# Create a dump file for debug messages
dump = open ('dump.txt', 'w')

def logMsg (port, m):
    # Send a message to the log file and flush it every time (which is not
    # amazing performance wise).  Trim the port to always be 10 chars wide
    lPort = (str (port) + ' ' * 10) [0:10]
    dump.write (str (dt.datetime.now ())[17:] + ' ' + lPort + m + '\n')
    dump.flush ()

def printTCPList ():
    # Go through every list in the big list
    for row, port in enumerate (g.tcpList):
        # Go throuh every item in the inner list
        for col, value in enumerate (port):
            # Print the field title
            ui.addstr (0, col * 14, c.tcpListTitles[col])
            # Print the first 13 chars of the field contents
            field = g.tcpList[row][col]
            # Naff way of formatting each field to show best for me
            if col == c.ipAddress:
                # Print the whole of the D digit of the IP Address
                pass
            elif col == c.ipPort:
                # Print the whole of the port number
                pass
            elif col == c.duty:
                if field == 'c':
                    field = 'Control'
                elif field == 'd':
                    field = 'Data'
            elif col == c.state:
                if field == c.createSocket:
                    field = 'Create'
                elif field == c.connectSocket:
                    field = 'Connect'
                elif field == c.doComms:
                    field = 'Comms'
                else:
                    field = 'State error'
            elif col == c.handle:
                # Don't change handle
                pass
            elif col == c.connect:
                # Only print the seconds part of the time
                field = str (field)[17:]
            elif col == c.RxDBuffer:
                # Print the length of the buffer
                field = str (len (g.tcpList[row][c.RxDBuffer]))
            elif col == c.gotStart:
                # Only print if we're on a data port
                if g.tcpList[row][c.duty] == 'd':
                    pass
                else:
                    # Zap control ports because it does not make sense
                    field = ""
            elif col == c.systemName:
                # Just print the name
                pass
            elif col == c.timer:
                # Print the DELTA time (not a dt!)
                if field != None:
                    field = str (field)[5:]
            elif col == c.lastDT:
                # Print the last part of the dt
                if field != None:
                    field = str (field)[17:]
            else:
                field = 'Illegal field'
            ui.addstr (row + 1, col * 14, str (field)[0:13])
            # Silly way of clearing out old contents of field
            ui.clrtoeol ()
    ui.refresh ()

def populateConnectTimes ():
    # Populate tcpList with the next time to try to create a connection
    logMsg ('', 'len(g.tcpList) ' + str (len (g.tcpList)))

    for pointer in range (0, len (g.tcpList)):
        logMsg (pointer, 'Setting up connect timer')
        # Put a second between each attempt to connect  using seconds = pointer
        g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = pointer)

def printRow (pr, rowList):
    # Print the list of items on the supplied row
    for pointer in range (0, len (rowList)):
        ui.addstr (pr, pointer * 8, rowList [pointer])
        ui.clrtoeol ()

def printLists ():
    # Print nicely formated lists that should have been loaded by the exec command in printLine
    # Start of the table to get out of the way of the raw text printout
    lRow = 10
    ui.addstr (lRow, 0, 'Current Data Port pointer ' + str (g.currentDataPort))
    ui.clrtoeol ()
    ui.addstr (lRow, 30, 'Current Data Port name ' + str (g.tcpList[g.currentDataPort][c.systemName]))
    ui.clrtoeol ()
    ui.addstr (lRow, 70, 'Output boards ' + str (g.ioData[g.currentDataPort].oBoards))
    ui.clrtoeol ()
    ui.addstr (lRow, 100, 'Input boards ' + str (g.ioData[g.currentDataPort].iBoards))
    ui.clrtoeol ()

    lRow += 2

    # Single loop to print all the output information
    # Only do this if the loop counter (i.e. The number of output boards on this system)
    # is legal
    if g.ioData[g.currentDataPort].oBoards != None:
        for ptr in range (0, g.ioData[g.currentDataPort].oBoards):
            printRow (lRow + 0, g.ioData[g.currentDataPort].oState[ptr])
            printRow (lRow + 1, g.ioData[g.currentDataPort].oForce[ptr])
            printRow (lRow + 2, g.ioData[g.currentDataPort].oName[ptr])
            lRow += 3

    lRow += 1
    # Single loop to print all the input information
    if g.ioData[g.currentDataPort].iBoards != None:
        for ptr in range (0, g.ioData[g.currentDataPort].iBoards):
            printRow (lRow + 0, g.ioData[g.currentDataPort].iState[ptr])
            printRow (lRow + 1, g.ioData[g.currentDataPort].iForce[ptr])
            printRow (lRow + 2, g.ioData[g.currentDataPort].iName[ptr])
            lRow += 3

    # DEBUG
#    ui.addstr (37, 0, 'current data port ' + str (g.currentDataPort))
#    for ptr in range (0, len (g.ioData)):
#        ui.addstr (38 + ptr, 0,  str (g.ioData[ptr].iName[0][0]))
#    ui.refresh ()

def addChannel (pointer, lineOfText):
    # Remove the leading g and replace it with g.ioData[pointer]
    return 'g.ioData[' + str (pointer) + ']' + lineOfText[1:]

def processDataLines (pointer, m):
    # pointer points to the correct entry in ioData and tcpList for the link we're
    # working with.  m contains the (potentially multi line) text string from
    # the remote end
    # This function could end up printing many lines of text...
    while (m.find ("\n")) != -1:
        # Slice off the string to process without the \r\n
        lineOfText = m[0:m.find ("\n") - 1]

        if (lineOfText.find ('g.iBoards') == 0) & (g.ioData[pointer].iBoards == None):
            # Create the lists needed to hold input information
            logMsg (pointer, 'Loading up iBoards on entry')
            # edit the supplied text to include a reference to the g.ioData list
            # and then exec it
            exec (addChannel (pointer, lineOfText))
            # Now we can create the correct number of entries in the ioData list
            for p in range (0, g.ioData[pointer].iBoards):
                g.ioData[pointer].iState.append ([])
                g.ioData[pointer].iForce.append ([])
                g.ioData[pointer].iName.append ([])

        elif (lineOfText.find ('g.oBoards') == 0) & (g.ioData[pointer].oBoards == None):
            # Create the lists needed to hold input information
            logMsg (pointer, 'Loading up oBoards on entry')
            exec (addChannel (pointer, lineOfText))
            # Now we can create the correct number of entries in the ioData list
            for p in range (0, g.ioData[pointer].oBoards):
                g.ioData[pointer].oState.append ([])
                g.ioData[pointer].oForce.append ([])
                g.ioData[pointer].oName.append ([])

        elif (g.ioData[pointer].iBoards != None) & (g.ioData[pointer].oBoards != None):
            # It is only safe to exec general lines of output once iBoards and oBoards
            # are populated
            # Under these circumstances, don't keep exec-ing the i/oBoard statements
            if (lineOfText.find ('g.iBoards = ') == -1) & (lineOfText.find ('g.oBoards = ') == -1):
                exec (addChannel (pointer, lineOfText))
#            else:
#                logMsg (pointer, 'Passing over i/oBoards exec')
        else:
            # We have to dump the lineOfText because it did not satify one
            # of the above conditions
            logMsg (pointer, 'Throwing away the following line of text on entry')
            logMsg (pointer, lineOfText)

        # If we're processing the last line of text for a given IO Controller and we have valid
        # settings for oBoards and iBoards AND the connection we're servicing is the displayed
        # system then print it all out
        if (lineOfText.find ('g.iName [3]') == 0) & \
                (g.ioData[pointer].iBoards != None) & \
                (g.ioData[pointer].oBoards != None):
            # Work out how long it is since the last time we read from this IO Controller
            if g.tcpList[pointer][c.lastDT] != None:
                g.tcpList[pointer][c.timer] = dt.datetime.now () - g.tcpList[pointer][c.lastDT]
            # Now update the time since the last time we were here
            g.tcpList[pointer][c.lastDT] = dt.datetime.now ()
            # If we're on the correct page then update the screen
            if (g.currentDataPort == pointer):
                printLists ()

        # Now trim off what we just printed remembering that it's \r\n at the
        # end of the line
        m = m[m.find ("\n") + 1:]
    return m

def checkKeyboard ():
    # See if the keyboard was pressed
    ch = ui.getch ()

    # Check for no key pressed
    if ch == curses.ERR:
        return

    elif ch == ord ('q'):
        # Quit the program
        curses.endwin ()
        sys.exit ()

    elif ch == ord ('1'):
        # Hard coded to use the first port in the list (which must be a Control Port)
        # Send out a command to change the name of the first input
        g.tcpList[0][c.handle].send ('exec g.iName[0][0] = "ZERO"\r\n'.encode ())
#        g.tcpList[2][c.handle].send ('exec g.iName[0][0] = "TWO"\r\n'.encode ())
#        g.tcpList[4][c.handle].send ('exec g.iName[0][0] = "FOUR"\r\n'.encode ())
#        g.tcpList[6][c.handle].send ('exec g.iName[0][0] = "SIX"\r\n'.encode ())

    elif ch == ord ('2'):
        # As above with a different text
        g.tcpList[0][c.handle].send ('exec g.iName[0][0] = "Dave"\r\n'.encode ())
#        g.tcpList[2][c.handle].send ('exec g.iName[0][0] = "Dave"\r\n'.encode ())
#        g.tcpList[4][c.handle].send ('exec g.iName[0][0] = "Dave"\r\n'.encode ())
#        g.tcpList[6][c.handle].send ('exec g.iName[0][0] = "Dave"\r\n'.encode ())

    elif ch == ord ('3'):
        # Send a massive command to the first port in the list which updates the names
        # of all the inputs at once.
        io = ['exec g.oName [', 'exec g.iName [']

        # Build the output string here
        sendThis = ""

        # Do the outputs then the inputs
        for direction in io:
            # Each board:  Hard coded to 4 boards!
            for board in range (0, 4):
                sendThis = sendThis + direction + str(board) + '] = ['

                # Each pin on the board
                for pin in range (0, c.pinsPerBoard):
                    sendThis = sendThis + '"' + str (dt.datetime.now ())[17:] + '", '

                # Remove trailing "' " before adding CRLF
                sendThis = sendThis[0:-2] + ']\r\n'

        g.tcpList[0][c.handle].send (sendThis.encode ())

    elif ch == ord ('5'):
        # Send a syntactically invalid command to the IO Controller
        g.tcpList[0][c.handle].send ('exec lobsters are lovely\r\n'.encode ())

    elif ch == ord ('+'):
        # Increment the current IO Controller we're looking at
        findNextDataPort (c.nextEntry)
        printLists ()

    elif ch == ord ('-'):
        # Decrement the current IO controller we're looking at
        findNextDataPort (c.previousEntry)
        printLists ()

def findNextDataPort (direction):
    # OK, this is simple once you've got your head around it.  We have a list called tcpList
    # which controls all the TCP connections to IO Controllers.  We also have g.currentDataPort
    # which points at the DATA PORT entry in tcpList which we're current displaying.
    # So this routine takes a look at the current value in g.currentDataPort then depending on
    # the value in direction, will do one of the following things;
    # + Find the next data port wrapping if required
    # - Find the previous data port wrapping if required
    # 0 Find the first data port
    # In all cases, g.currentDataPort exits with the correct value
    # If there are no Data Ports then exit silently
    # If there is only one Data Port then g.currentDataPort will remain unchanged

    if direction == c.firstEntry:
        # Find the first entry in tcpList
        for pointer in range (0, len (g.tcpList)):
            if g.tcpList[pointer][c.duty] == 'd':
                g.currentDataPort = pointer
                return
        logMsg ('', 'Could not find data port')

    elif direction == c.nextEntry:
        # Find the next entry in tcpList
        pointer = g.currentDataPort
        # Search loop
        while True:
            # Point at the next entry in the list wrapping if required
            pointer += 1
            if pointer == len (g.tcpList):
                pointer = 0
            # If we're back where we started from, exit without changing anything
            if pointer == g.currentDataPort:
                return
            # If we have a match then exit loading up the new currentDataPort value
            # on the way
            if g.tcpList[pointer][c.duty] == 'd':
                break
        # Update the magic value
        g.currentDataPort = pointer

    elif direction== c.previousEntry:
        # Find the previous entry in tcpList
        pointer = g.currentDataPort

        # Search loop
        while True:
            # Point at the previous entry in the list wrapping if required
            pointer -= 1
            if pointer == -1:
                pointer = len (g.tcpList) - 1
            # If we're back where we started from, exit without changing anything
            if pointer == g.currentDataPort:
                return
            # If we have a match then exit loading up the new currentDataPort value
            # on the way
            if g.tcpList[pointer][c.duty] == 'd':
                break
        # Update the magic value
        g.currentDataPort = pointer

    else:
        logMsg('', 'Illegal direction in findNextDataPort')

def stateCreateSocket (pointer):
    # Is it time to create a socket object?
    if g.tcpList[pointer][c.connect] < dt.datetime.now ():
        logMsg (pointer, 'Attempting to create socket object')
        try:
            g.tcpList[pointer][c.handle] = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
            logMsg (pointer, 'Created socket object')
            # Set the timeout for connect attempts
            g.tcpList[pointer][c.handle].settimeout (c.connectTimeout)
            # Jog the state to the next thing to do and try in a couple of seconds
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
            g.tcpList[pointer][c.state] = c.connectSocket
        except Exception as ex:
            # Create failed (which I don't think should ever happen!)
            logMsg (pointer, 'Failed to create socket object')
            # Reset the time to try again and leave the state alone
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
            g.tcpList[pointer][c.state] = c.createSocket
            template = "An exception of type {0} occurred. Arguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logMsg (pointer, message)

def stateConnectClient (pointer):
    if g.tcpList[pointer][c.connect] < dt.datetime.now ():
        # Attempt the connect making the full IP address up from a couple of sources and
        # dropping in the TCP port to use
        logMsg (pointer, 'Attempting connect')
        try:
            g.tcpList[pointer][c.handle].connect ((g.tcpAddress + g.tcpList[pointer][c.ipAddress], g.tcpList[pointer][c.ipPort]))
        # TODO:  Need to add error processing for 
        #    Type = OSError,  Arguments = 113, No route to host
        #    Type = ConnectionRefusedError, Arguments = 111, Connection refused
        #    Type = timeout (note case), Arguments malformed?
        #    Type = BlockingIOError, Arguments = 114, Operation already in progress
        #    Type = ConnectionAbortedError, Arguments = 103, Software caused connection abort
        except Exception as ex:
            # Connect failed
            logMsg (pointer, 'Failed to connect on entry')
            # Reset the time to try again and leave the state alone
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
            g.tcpList[pointer][c.state] = c.connectSocket
            template = "An exception of type {0} occurred. Arguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logMsg (pointer, message)
        else:
            # Jog the state to the next thing to do.  I don't update the dwell timer
            # becuase we're straight into it...
            g.tcpList[pointer][c.state] = c.doComms
            logMsg (pointer, 'Got connected')
            # Now set the timeout to zero which effectively makes attempts to read
            # the input buffer non-blocking
            g.tcpList[pointer][c.handle].settimeout (0)
            # Reset the receive buffer and a boolean that's used by the receive side of the
            # data interface to work out when it's in sync with the incoming data feed
            g.tcpList[pointer][c.RxDBuffer] = ""
            g.tcpList[pointer][c.gotStart] = False

def stateConnected (pointer):
    # Try to read any chars waiting in the input buffer and convert them from a byte stream
    # into a string using default encoding
    try:
        RxD = g.tcpList[pointer][c.handle].recv (1024).decode ()

    except socket.error as e:
        err = e.args [0]
        if (err == errno.EAGAIN) or (err == errno.EWOULDBLOCK):
            # Expected error if there's nothing received
            pass

    except Exception as ex:
        # Buffer read failed
        logMsg (pointer, 'Failed read')
        # Reset the time to try again and leave the state alone
        template = "An exception of type {0} occurred. Arguments:{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logMsg (pointer, message)
        logMsg (pointer, 'Closing the connection and waiting a bit before attempting reconnect')
        # So there was a real error.  Close the connection and reset the
        # state machine to the bit where we have a handle but are not
        # connected.  Also set the timer so we leave it a bit before retrying
        g.tcpList[pointer][c.handle].close ()
        g.tcpList[pointer][c.gotStart] = False
        g.tcpList[pointer][c.state] = c.createSocket
        g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)

    else:
        # See if we actually got anything in
        if len (RxD) == 0:
            # This means that the client disconnected so log the fault and reset the
            # state machine right back to closing the port (which seems to distroy the
            # object) then waiting a bit before trying again
            logMsg (pointer, 'Client disconnected on entry')
            g.tcpList[pointer][c.handle].close ()
            g.tcpList[pointer][c.gotStart] = False
            g.tcpList[pointer][c.state] = c.createSocket
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)

        else:
            # What ever the port type, append the newly arrived string
            # to the buffer
            g.tcpList[pointer][c.RxDBuffer] = g.tcpList[pointer][c.RxDBuffer] + RxD

            if g.tcpList[pointer][c.duty] == 'c':
                # It's a control port
                logMsg (pointer, 'Control port received the following')
                logMsg (pointer, RxD)

            elif g.tcpList[pointer][c.duty] == 'd':
                # It's a data port.  Work out if we have to try to get in sync
                if g.tcpList[pointer][c.gotStart] == False:
                    # Try to get in sync
                    if g.tcpList[pointer][c.RxDBuffer].find ('g.iBoards') != -1:
                        # Delete everything up to the string we just found
                        g.tcpList[pointer][c.RxDBuffer] = \
                        g.tcpList[pointer][c.RxDBuffer][g.tcpList[pointer][c.RxDBuffer].find ('g.iBoards'):]
                        g.tcpList[pointer][c.gotStart] = True
                        logMsg (pointer, 'Got Start')
                # Now print as many whole lines as we can find in the buffer
                # and update the remainder (if there is any) back into the buffer
                g.tcpList[pointer][c.RxDBuffer] = processDataLines (pointer, g.tcpList[pointer][c.RxDBuffer])

            else:
                logMsg (pointer, 'Invalid port duty')

def main (ui, *args):
    # Create a couple of blank lines in the log so we can see a new start clearly when doing
    # a "tail -F dump.txt" on the file
    logMsg ('', '')
    logMsg ('', 'Starting new log file')
    logMsg ('', '')

    # Find the first Data Port in tcpList and make g.currentDataPort point at it
    findNextDataPort (c.firstEntry)

    # Populate tcpList with the next time to try to create a connection
    populateConnectTimes ()

    # This is the main loop of the program which is basically running around the ports
    # as quickly as possible figuring out what's to do next on each of them
    while (True):

        # See if the keyboard has been pressed
        checkKeyboard ()

        # Print out the state of tcpList
        printTCPList ()

        # Look at the state of each entry in tcpList
        for pointer in range (0, len (g.tcpList)):

            # Are we waiting to create a socket object?
            if g.tcpList[pointer][c.state] == c.createSocket:
                stateCreateSocket (pointer)

            # Are we waiting to connect to the IO Controller?
            elif g.tcpList[pointer][c.state] == c.connectSocket:
                stateConnectClient (pointer)

            # We're connected...
            elif g.tcpList[pointer][c.state] == c.doComms:
                stateConnected (pointer)

            else:
                logMsg (pointer, 'Illegal state')

if __name__ == "__main__":
    # Before we try to start a curses session, check that the terminal is big enough
    cols, rows = os.get_terminal_size ()
    if (cols < c.tcCols) or (rows < c.tcRows):
        print ("Can't start program as terminal is only;")
        print ("rows = " + str (rows))
        print ("cols = " + str (cols))
        print ("And it needs to be;")
        print ("rows = " + str (c.tcRows))
        print ("cols = " + str (c.tcCols))
        sys.exit ()

    # Create a screen device which does not echo keypresses to the screen
    # or wait for ENTER before returning keystrokes then call our application
    # in a way that makes the terminal recover if the program crashes
    ui = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    ui.nodelay (True)       # keyboard check is non-blocking
    curses.wrapper (main)
    logMsg ('', 'Program end')

