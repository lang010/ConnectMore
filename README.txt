Copyright (c) 2014, Liang Li <ll@lianglee.org; liliang010@gmail.com>.
All rights reserved.

License: BSD-style

================================================================================

About Cloudict
--------------

ConnectMore is a UI for Cloudict of the game Connect6, written by Python 3.
Other connect6 programs with similar commands are also supported.

For Cloudict, please see:
    https://github.com/lang010/cloudict

For the computer game Connect6, please see:
    http://en.wikipedia.org/wiki/Connect6

![screenshot](http://i.imgur.com/OL2kxZf.png)

    Have fun! :-)

================================================================================

Compile Notes
-------------

* This python 3 script depends on some standard modules, including:
    Tk/tcl
    subprocess
    threading
    time
    os
    random  

================================================================================

Runtime Notes
-------------

This program will create a process to run the game engine, default is Cloudict.
It will send commands into the engine's stdin, and read its output from stdout by pipelines.
The commands as follows:

    name        - print the name of the Game Engine.
    new xxx     - start a new game and set it to White.
    black XXXX  - place the black stone on the position XXXX in the board.
    white XXXX  - place the write stone on the XXXX in the board, X is the A-S.
    next        - the engine will search the move for next.
    depth d     - set the alpha beta search depth, default is 6.
    vcf         - set vcf for searching.
    unvcf       - unset vcf.

