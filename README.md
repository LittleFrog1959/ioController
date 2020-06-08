# ioController
Input/Output (IO) Controller based on RPi4 and AB Electronics PIO boards.

Presents a TCP/IP socket server to a Test Controller.  This interface can be used to exchange real time information on the state of the I/O.

This project is a front end to another project which uses Robot Framework to provide an automated test environment for real time system testing (i.e. the Test Controller).

## Background
A long time ago I used to work here; https://www.petards.com/ and even longer ago here https://www.appliedsoftware.co.uk/.  I worked on automated test systems and the development of harnesses which could be placed around development projects for the purposes of of proving functional correctness.

It was a long time ago and the ideas that I had never really got followed through as much as I'd hoped...  So this project is a play-time & relearning exercise to see if I can get further this time.

## Test Harness
The complete system will feature the following elements;
1. A number of IO Controllers (the subject of this repo).
1. A single Test Controller

The I/O Controllers interface to the outside world through simple volt free contacts (for outputs) and opto isolators (for inputs).  They have very limited internal functionality, simply presenting an interface to the Test Controller.

The Test Controller has three pieces of functionality;
1. Exchange information with the IO Controllers.
1. Run an emulation of the "real world" in a number of scenarios
1. Run RF which manages the tests and collects / presents results

## Information
From here, you need to take a look at the repo wiki which is here; https://github.com/LittleFrog1959/ioController/wiki.  You can find information about Robot Framework here https://robotframework.org/

## Real time?
Well no...  It's not real time...  The response of the system to I/O state changes is about 250mS which is not really real time is it?

