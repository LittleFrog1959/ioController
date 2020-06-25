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

import globals
g = globals.testGlobals ()
g.toggle = False

import constants
c = constants.constants ()

# Create a dump file for debug messages
dump = open ('dump.txt', 'w')

def logMsg (m):
    # Send a message to the log file and flush it every time (which is not
    # amazing performance wise)
    dump.write (str (dt.datetime.now ())[17:] + ' ' + m + '\n')
    dump.flush ()

def printTCPList ():
    for row, port in enumerate (g.tcpList):
        for col, value in enumerate (port):
            ui.addstr (row, col * 10, str (g.tcpList[row][col]))
    ui.refresh ()

def populateConnectTimes ():
    # Populate tcpList with the next time to try to create a connection
    logMsg ('len(g.tcpList) ' + str (len (g.tcpList)))

    for pointer in range (0, len (g.tcpList)):
        logMsg ('pointer ' + str (pointer))
        # Put a second between each attempt to connect  using seconds = pointer
        g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = pointer)

def printRow (pr, rowList):
    # Print the list of items on the supplied row
    for pointer in range (0, len (rowList)):
        ui.addstr (pr, pointer * 8, rowList [pointer])
        ui.clrtoeol ()

def printLists (pointer):
    # Print nicely formated lists that should have been loaded by the exec command in printLine
    # Start of the table to get out of the way of the raw text printout
    lRow = 1 + (pointer * 8)
    ui.addstr (lRow, 0, 'g.iBoards ' + str (g.ioData[pointer].iBoards))
    ui.addstr (lRow, 20, 'g.oBoards ' + str (g.ioData[pointer].oBoards))

    # Toggle the state of the on-screen activity indicator
    if g.toggle == False:
        ui.addstr (lRow, 40, ' ')
        g.toggle = True
    else:
        ui.addstr (lRow, 40, '*')
        g.toggle = False

    ui.clrtoeol ()
    lRow += 1
    # Single loop to print all the output information
    for ptr in range (0, g.ioData[pointer].oBoards):
        printRow (lRow + 0, g.ioData[pointer].oState[ptr])
        printRow (lRow + 1, g.ioData[pointer].oForce[ptr])
        printRow (lRow + 2, g.ioData[pointer].oName[ptr])
        lRow += 3

    # Single loop to print all the input information
    for ptr in range (0, g.ioData[pointer].iBoards):
        printRow (lRow + 0, g.ioData[pointer].iState[ptr])
        printRow (lRow + 1, g.ioData[pointer].iForce[ptr])
        printRow (lRow + 2, g.ioData[pointer].iName[ptr])
        lRow += 3

    ui.refresh ()

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
            logMsg ('Loading up iBoards on entry ' + str (pointer))
            # edit the supplied text to include a reference to the g.ioData list
            # and then exec it
            exec (addChannel (pointer, lineOfText))
            for p in range (0, g.ioData[pointer].iBoards):
                g.ioData[pointer].iState.append ([])
                g.ioData[pointer].iForce.append ([])
                g.ioData[pointer].iName.append ([])

        elif (lineOfText.find ('g.oBoards') == 0) & (g.ioData[pointer].oBoards == None):
            # Create the lists needed to hold input information
            logMsg ('Loading up oBoards on entry ' + str (pointer))
            exec (addChannel (pointer, lineOfText))
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
#                logMsg ('Passing over i/oBoards exec')
        else:
            # We have to dump the lineOfText because it did not satify one
            # of the above conditions
            logMsg ('Throwing away the following line of text on entry ' + str(pointer))
            logMsg (lineOfText)

        # If we're processing iBoards and we already have valid entries for it and oBoards
        # Then we must be at the start of a frame of data values so print them to the screen
        if (lineOfText.find ('g.iName [3]') == 0) & (g.ioData[pointer].iBoards != None) & (g.ioData[pointer].oBoards != None):
            printLists (pointer)

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
        g.tcpList[0][c.handle].send ('exec g.iName[0][0] = "June"\r\n'.encode ())

    elif ch == ord ('2'):
        # As above with a different text
        g.tcpList[0][c.handle].send ('exec g.iName[0][0] = "Dave"\r\n'.encode ())

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

    elif ch == ord ('4'):
        # Start / stop the test
        if g.testOne == False:
            g.testOne = True
        else:
            g.testOne = True

    elif ch == ord ('5'):
        # Send a syntactically invalid command to the IO Controller
        g.tcpList[0][c.handle].send ('exec lobsters are lovely\r\n'.encode ())

def stateCreateSocket (pointer):
    # Is it time to create a socket object?
    if g.tcpList[pointer][c.connect] < dt.datetime.now ():
        logMsg ('Attempting to create socket object on list item ' + str (pointer))
        try:
            g.tcpList[pointer][c.handle] = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
            logMsg ('Created socket object on entry ' + str (pointer))
            # Set the timeout for connect attempts
            g.tcpList[pointer][c.handle].settimeout (1)
            # Jog the state to the next thing to do and try in a couple of seconds
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
            g.tcpList[pointer][c.state] = c.connectSocket
        except Exception as ex:
            # Create failed (which I don't think should ever happen!)
            logMsg ('Failed to create socket object on entry ' + str (pointer))
            # Reset the time to try again and leave the state alone
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
            g.tcpList[pointer][c.state] = c.createSocket
            template = "An exception of type {0} occurred. Arguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logMsg (message)

def checkTests ():
    # Run a test which toggles all the IO as quickly as possible
    return

def stateConnectClient (pointer):
    if g.tcpList[pointer][c.connect] < dt.datetime.now ():
        # Attempt the connect making the full IP address up from a couple of sources and
        # dropping in the TCP port to use
        logMsg ('Attempting connect on list item ' + str (pointer))
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
            logMsg ('Failed to connect on entry ' + str (pointer))
            # Reset the time to try again and leave the state alone
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
            g.tcpList[pointer][c.state] = c.connectSocket
            template = "An exception of type {0} occurred. Arguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logMsg (message)
        else:
            # Jog the state to the next thing to do.  I don't update the dwell timer
            # becuase we're straight into it...
            g.tcpList[pointer][c.state] = c.doComms
            logMsg ('Got connected on entry ' + str (pointer))
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
        logMsg ('Failed read on entry ' + str (pointer))
        # Reset the time to try again and leave the state alone
        template = "An exception of type {0} occurred. Arguments:{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logMsg (message)
        logMsg ('Closing the connection and waiting a bit before attempting reconnect')
        # So there was a real error.  Close the connection and reset the
        # state machine to the bit where we have a handle but are not
        # connected.  Also set the timer so we leave it a bit before retrying
        g.tcpList[pointer][c.handle].close ()
        g.tcpList[pointer][c.state] = c.createSocket
        g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
    else:
        # See if we actually got anything in
        if len (RxD) == 0:
            # This means that the client disconnected so log the fault and reset the
            # state machine right back to closing the port (which seems to distroy the
            # object) then waiting a bit before trying again
            logMsg ('Client disconnected on entry ' + str (pointer))
            g.tcpList[pointer][c.handle].close ()
            g.tcpList[pointer][c.state] = c.createSocket
            g.tcpList[pointer][c.connect] = dt.datetime.now () + dt.timedelta (seconds = 2)
        else:
            # What ever the port type, append the newly arrived string
            # to the buffer
            g.tcpList[pointer][c.RxDBuffer] = g.tcpList[pointer][c.RxDBuffer] + RxD
            if g.tcpList[pointer][c.duty] == 'c':
                # It's a control port
                logMsg ('Control port received the following on entry: ' + str (pointer))
                logMsg (RxD)
            elif g.tcpList[pointer][c.duty] == 'd':
                # It's a data port.  Work out if we have to try to get in sync
                if g.tcpList[pointer][c.gotStart] == False:
                    # Try to get in sync
                    if g.tcpList[pointer][c.RxDBuffer].find ('g.iBoards') != -1:
                        # Delete everything up to the string we just found
                        g.tcpList[pointer][c.RxDBuffer] = \
                        g.tcpList[pointer][c.RxDBuffer][g.tcpList[pointer][c.RxDBuffer].find ('g.iBoards'):]
                        g.tcpList[pointer][c.gotStart] = True
                        logMsg ('Got Start on entry ' + str (pointer))
                # Now print as many whole lines as we can find in the buffer
                # and update the remainder (if there is any) back into the buffer
                g.tcpList[pointer][c.RxDBuffer] = processDataLines (pointer, g.tcpList[pointer][c.RxDBuffer])
            else:
                logMsg ('Invalid port duty on entry ' + str (pointer))

def main (ui, *args):
    # Create a couple of blank lines in the log so we can see a new start clearly when doing
    # a "tail -F dump.txt" on the file
    logMsg ('')
    logMsg ('Starting new log file')
    logMsg ('')

    # Populate tcpList with the next time to try to create a connection
    populateConnectTimes ()

    # Print out the starting state of the tcpList
    printTCPList ()

    # This is the main loop of the program which is basically running around the ports
    # as quickly as possible figuring out what's to do next on each of them
    while (True):
        # See if the keyboard has been pressed
        checkKeyboard ()

        # See if we're running a test
        checkTests ()

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
                logMsg ('Illegal state on entry ' + str (pointer))


if __name__ == "__main__":
    # Create a screen device which does not echo keypresses to the screen
    # or wait for ENTER before returning keystrokes then call our application
    # in a way that makes the terminal recover if the program crashes
    ui = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    ui.nodelay (True)       # keyboard check is non-blocking
    curses.wrapper (main)
    logMsg ('Program end')

