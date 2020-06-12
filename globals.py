# globals used by the ioController and testController programs

import constants
c=constants.constants ()

class globals ():
    # The number of messages sent to the messagePage.  This is used to
    # cause a simple scroll of the text widget (i.e. The oldest msg deleted)
    messageRows = 0


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


