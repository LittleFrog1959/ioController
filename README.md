# ioController
Input/Output (IO) Controller based on RPi4 and AB Electronics PIO boards.

Presents a TCP/IP socket server.  This interface can be used to exchange real time information on the state of the I/O.

This project is a front end to another project which uses Robot Framework to provide an automated test environment for real time system testing.

You can find information about Robot Framework here https://robotframework.org/

## Background
A long time ago I used to work here; https://www.petards.com/ and even longer ago here https://www.appliedsoftware.co.uk/.  I worked on automated test systems and the development of harnesses which could be placed around development projects for the purposes of of proving functional correctness.

It was a long time ago and the ideas that I had never really got followed through as much as I'd hoped...  So this project is a play-time relearning project to see if I can get further this time.

## Test Harness
The complete system will feature the following elements;
1. A number of IO Controllers (the subject of this repo).
1. A single Test Controller

The I/O Controllers interface to the outside world through simple volt free contacts (for outputs) and opto isolators (for inputs).  They have very limited internal functionality, simply presenting an interface to the Test Controller.

The Test Controller has three pieces of functionality;
1. Exchange information with the IO Controllers.
1. Run an emulation of the "real world" in a number of scenarios
1. Run RF which manages the tests and collects / presents results

