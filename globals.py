# globals used by the ioController and testController programs.  Note that
# there are two classes here; one for the IO Controller and the other for the
# Test Controller.

import constants
c=constants.constants ()

class ioGlobals ():
    # The IP address of the io controller is learned as the program
    # starts
    ioIPAddress = None

    # The number of messages sent to the messagePage.  This is used to
    # cause a simple scroll of the text widget (i.e. The oldest msg deleted)
    messageRows = 0

    # Used by the pop up menu to pass across the board/pin we're going to
    # alter
    popUpBoard = 0
    popUpPin = 0

    # Global creates:
    # - A pair of lists containing the true state of the input or output pins
    #   iState and oState. Each element can have the following values;
    #           "null", "on", "off"
    #   The states on and off are populated by the code that interfaces to the
    #   ABE boards.  The state null is used to show that the field has not
    #   been populated with a legal state from the ABE driver.
    # - A pair of lists containing the old version of the 3 lines of text in
    #   each UI button.  This is used to detect changes of state as well as
    #   any forced state / name changes
    # - A pair of lists containing the forced state of pins
    #   iForce and oForce that can have the following values;
    #           "live", "forced on", "forced off"
    # - A pair of lists contained in the name of the pins
    #   iName and oName which are inititally set to a simple string
    #       of the form "[direction]button, pin"
    oState = []
    oldoBtnText = []
    oForce = []
    oName = []
    for board in range (0, len(c.oBoard)):
        # Create a new row (which is the "board" axis)
        oState.append ([])
        oldoBtnText.append ([])
        oForce.append ([])
        oName.append ([])
        # Then populate each row with 16 values (for pin 0-15)
        for pin in range (0, c.pinsPerBoard):
            oState[board].append ('null')
            oldoBtnText[board].append ('')
            oForce[board].append ('live')
            oName[board].append ('O' + str (board) + ',' + str (pin))

    iState = []
    oldiBtnText = []
    iForce = []
    iName = []
    for board in range (0, len(c.iBoard)):
        iState.append ([])
        oldiBtnText.append ([])
        iForce.append ([])
        iName.append ([])
        for pin in range (0, c.pinsPerBoard):
            iState[board].append ('null')
            oldiBtnText[board].append ('')
            iForce[board].append ('live')
            iName[board].append ('I' + str (board) + ',' + str (pin))


# Here are the globals used by the Test Controller program.  It's all
# very much like the IO Controller end but the massive lists describing
# the state of the IO have another dimension to them...  Which controller
# they relate to...
class ioInformation ():
    iBoards = None
    oBoards = None

    oState = []
    oldoBtnText = []
    oForce = []
    oName = []
    for board in range (0, len(c.oBoard)):
        # Create a new row (which is the "board" axis)
        oState.append ([])
        oldoBtnText.append ([])
        oForce.append ([])
        oName.append ([])
        # Then populate each row with 16 values (for pin 0-15)
        for pin in range (0, c.pinsPerBoard):
            oState[board].append ('null')
            oldoBtnText[board].append ('')
            oForce[board].append ('live')
            oName[board].append ('O' + str (board) + ',' + str (pin))

    iState = []
    oldiBtnText = []
    iForce = []
    iName = []
    for board in range (0, len(c.iBoard)):
        iState.append ([])
        oldiBtnText.append ([])
        iForce.append ([])
        iName.append ([])
        for pin in range (0, c.pinsPerBoard):
            iState[board].append ('null')
            oldiBtnText[board].append ('')
            iForce[board].append ('live')
            iName[board].append ('I' + str (board) + ',' + str (pin))

class testGlobals ():
    # The first part of the network address, leaving the subnet part to the list
    # below.
    tcpAddress = '192.168.1.'

    # Extend the globals to include a list of ports to connect to
    tcpList = ['61', 10000, 'c', c.createSocket, None, None, "", False], \
              ['61', 10001, 'd', c.createSocket, None, None, "", False], \
              ['62', 10000, 'c', c.createSocket, None, None, "", False], \
              ['62', 10001, 'd', c.createSocket, None, None, "", False], \
              ['63', 10000, 'c', c.createSocket, None, None, "", False], \
              ['63', 10001, 'd', c.createSocket, None, None, "", False], \
              ['64', 10000, 'c', c.createSocket, None, None, "", False], \
              ['64', 10001, 'd', c.createSocket, None, None, "", False]

    # Create a list which is made up of a class called "testGlobals" found in the
    # globals module.  There's one of these for each entry in tcpList
    ioData = []
    for pointer in range (0, len (tcpList)):
        ioData.append (ioInformation ())

