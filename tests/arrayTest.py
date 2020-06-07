# Create a totally empty list
l = []

for board in range (0, 4):
    l.append ([])
    for pin in range (0, 16):
        # Then for each pin, create a new entry inside that top level
        # row for each pin
        l[board].append (0)

print (l)

