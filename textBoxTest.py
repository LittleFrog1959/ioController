import tkinter as tk
import datetime as dt

linesOfText = [0]

def textBoxCallBack ():
    text.after (1000, textBoxCallBack)
    print (linesOfText[0])
    linesOfText[0] += 1
    if linesOfText[0] > 3:
        text.delete ('1.0', '2.0')
        linesOfText[0] = 4
    text.insert (tk.END, str (dt.datetime.now ()) + "\n")

root = tk.Tk ()
text = tk.Text (root)
text.after (1000, textBoxCallBack)
text.pack ()

text.tag_add ('firstLine', '1.0', '2.0')
text.tag_add ('start', '1.8', '1.13')
text.tag_configure ('here', background = 'yellow', foreground = 'blue')
text.tag_configure ('start', background = 'black', foreground = 'green')
root.mainloop ()
