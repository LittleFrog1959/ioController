# Constants used by the testController and ioController programs

class constants ():
    # The number of pins on an ABE PIO board port
    pinsPerBoard = 16

    # A pair lists describing the I2C ports used by the I/O boards
    oBoard = [0x20, 0x22, 0x24, 0x26]
    iBoard = [0x21, 0x23, 0x25, 0x27]

    # The directory into which we put run time log files
    logDirectory = 'logs/'

    # The file extenion used by run time logs (the filename is the
    # date/time)
    logExtension = '.log'

    # The symbolic filename we create at program start so that you
    # can always go to a fixed place when looking for the latest log
    symbolicLogFilename = 'log.log'

    # Max age of log files in minutes.  Anything older than this is
    # deleted when the program starts.  This purge does NOT happen
    # when the program's running
    logAge = 10

    # The max number of cols per message for presentation on the messagePage.
    # If the message is longer than this then we need to create a multi-line message
    messageColMax = 130

    # The max number of messages we can have in the message text box
    # before we loose some off the bottom of the screen.
    messageRowMax = 45

    # Resolution of the touch screen
    touchScreenResolution = '1280x800'

    # TCP/IP ports
    tcpControlPort = 10000
    tcpDataPort = 10001

    # tkInter colours and other bits and bobs
    normalGrey = '#d9d9d9'
    brightGrey = "#e9e9e9"

    # Number of colomns on the rowsIO page
    fCount = 5

    # Name of the file which is used by the ioControler to sort out the
    # deviceIOPage
    deviceIOFilename = 'deviceIO.txt'

    # This is a list of pointers which I use so that the fields in g.tcpList
    # are named rather than numbered
    ipAddress = 0
    ipPort = 1
    duty = 2
    state = 3
    handle = 4
    connect = 5
    RxDBuffer = 6
    gotStart = 7
    systemName = 8
    timer = 9
    lastDT = 10

    # Titles of the above fields used to label up a nice table
    tcpListTitles = ['Address', 'Port', 'Duty', 'State', 'Handle', 'Connect', 'RxDBuffer', 'Got Start', 'System Name', 'Timer', 'Last DT']

    # In the above list, see "state", well here are the states you can have;
    createSocket = -1               # Need to create a socket object when time is right
    connectSocket = 0               # Need to attempt a connect when the time is right
    doComms = 1                     # We're connected, need to get on with it

    # The timeout when we attemp a TCP connect with the servers (i.e. IO controllers)
    connectTimeout = 0.5

    # Operation codes for findNextDataPort
    firstEntry = 0
    nextEntry = 1
    previousEntry = 2

    # Minimum screen size for Test Controller UI
    tcRows = 40
    tcCols = 150
