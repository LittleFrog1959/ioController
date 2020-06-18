import tkinter as tk

top = tk.Tk ()

sb = tk.Scrollbar (top)
sb.pack (side = tk.RIGHT, fill = tk.Y)

myList = tk.Listbox (top, yscrollcommand = sb.set)

for line in range (0, 30):
    myList.insert (tk.END, "Number " + str (line))

myList.pack (side = tk.LEFT)
sb.config (command = myList.yview)

tk.mainloop ()
