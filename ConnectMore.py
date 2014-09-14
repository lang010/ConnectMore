#
# Copyright (c) 2014, Liang Li <ll@lianglee.org; liliang010@gmail.com>,
# All rights reserved.
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the BSD license. See LICENSE.txt for details.
#
# It's a UI for Coudict(https://github.com/lang010/cloudict) based on Python 3.
# Other connect6 programs with similar commands are also supported.
# Enjoy Connect6;)
#
# Last Modified: 2014/09/14
#

from tkinter import *;
from tkinter.filedialog import *;
from tkinter import messagebox;
from subprocess import *;
from threading import *;
from time import *;
import os;
import random;

defaultEngineFile = '';
if os.name == 'nt':
    from subprocess import STARTUPINFO;
    defaultEngineFile = 'engines/cloudict.exe';

class Move:
    NONE = 0;
    BLACK = 1;
    WHITE = 2;
    EDGE = 19;
    def __init__(self, color = NONE, x1 = -1, y1 = -1, x2 = -1, y2 = -1):
        self.color = color;
        self.x1 = x1;
        self.y1 = y1;
        self.x2 = x2;
        self.y2 = y2;

    def __str__(self):
        return 'color: {0}, x1: {1}, y1: {2}, x2: {3}, y2: {4}'.format(self.color, self.x1, self.y1, self.x2, self.y2);

    def fromCmd(cmd, color = None):
        # print(cmd);
        # print(self);
        cmd = cmd.strip();
        if cmd.startswith('move '):
            cmd = cmd[5:].upper();
            if len(cmd) == 2:
                cmd = cmd*2;
            m = Move(color);
            m.x1 = ord(cmd[0]) - ord('A');
            m.y1 = ord(cmd[1]) - ord('A');
            m.x2 = ord(cmd[2]) - ord('A');
            m.y2 = ord(cmd[3]) - ord('A');
            return m;
        
        return None;

    def toCmd(self):  
        cmd = 'move ' + self.cmd() + '\n';
        print('Cmd:', cmd);
        return cmd;

    def toPlaceCmd(self):
        if self.color == Move.BLACK:
            cmd = 'black ';
        elif self.color == Move.WHITE:
            cmd = 'white ';
        else:
            return 'None Place Cmd\n';
        cmd += self.cmd() + '\n';
        # print('Cmd:', cmd);
        return cmd;

    def cmd(self):
        base = ord('A');
        return chr(base + self.x1) + chr(base + self.y1) + chr(base + self.x2) + chr(base + self.y2);

    def invalidate(self):
        self.color= None;
        self.x1 = -1;
        self.y1 = -1;
        self.x2 = -1;
        self.y2 = -1;

    def isValidated(self):
        if self.color != Move.BLACK and self.color != Move.WHITE:
            return False;
        if Move.isValidPosition(self.x1, self.y1) and Move.isValidPosition(self.x2, self.y2):
            return True;

        return False;

    def isValidPosition(x, y):
        if x >= 0 and x < Move.EDGE and y >= 0 and y < Move.EDGE:
            return True;
        return False;

class GameEngine:
    def __init__(self):
        self.fileName = defaultEngineFile;
        self.proc = None;
        self.move = Move();
        self.color = Move.NONE;
        self.setName('Unknown');

    def init(self, fileName = None, depth = None, vcf = None):
        if self.proc != None:
            self.proc.terminate();
            self.proc = None;
        if fileName != None and fileName.strip() != '':
            self.fileName = fileName;
        else:
            fileName = self.fileName;
        #print('init:', self.fileName);
        if os.name == 'nt':
            # Windows NT hide
            startupinfo =  STARTUPINFO();
            startupinfo.dwFlags |= STARTF_USESHOWWINDOW;
            self.proc = Popen(fileName, stdin=PIPE, stdout=PIPE, bufsize=0, startupinfo=startupinfo);
        else:
            self.proc = Popen(fileName, stdin=PIPE, stdout=PIPE, bufsize=0);

        # game engine name
        self.setName(fileName);
        self.proc.stdin.write(b'name\n');
        while True:
            msg = self.waitForNextMsg();
            if msg.startswith('name '):
                self.setName(msg.split(' ')[1]);
                break;

        if depth != None:
            cmd = 'depth ' + str(depth) + '\n';
            # print(cmd);
            self.proc.stdin.write(cmd.encode());
        if vcf != None:
            if vcf:
                cmd = 'vcf\n';
            else:
                cmd = 'unvcf\n';
            # print(cmd);
            self.proc.stdin.write(cmd.encode());
            
        self.move.invalidate();

        return True;

    def setName(self, name):
        self.name = self.shortName = name;
        if len(self.shortName) > 10 and self.shortName.find('.') > -1:
            ls = self.shortName.split('.');
            for i in ls:
                if i != '':
                    self.shortName = i;
                    break;
        if len(self.shortName) > 10:
            self.shortName = self.shortName[:8] + '...';

    def release(self):
        while self.proc != None:
            if self.proc.poll() == None:
                self.proc.terminate();
                sleep(0.5);
            else:
                self.proc = None;
        self.move.invalidate();

    def next(self, moveList = []):
        if self.proc != None:
            cmd = 'new xxx\n';
            self.proc.stdin.write(cmd.encode());
            # print('next stdin:', cmd)
            for m in moveList:
                cmd = m.toPlaceCmd();
                # print('next stdin:', cmd);
                self.proc.stdin.write(cmd.encode());

            cmd = 'next\n';
            self.proc.stdin.write(cmd.encode());
            # print('next stdin:', cmd);

    def waitForNextMsg(self):
        # print('Waiting');
        self.msg = self.proc.stdout.readline().decode();
        # print('out:', self.msg);
        return self.msg;

class GameState:

    Exit = -1;

    Idle = 0;
    AI2AI = 1;
    AI2Human = 2
    Human2Human = 3;

    WaitForEngine = 1;
    WaitForHumanFirst = 2;
    WaitForHumanSecond = 3;

    Win = 4;

class App(Frame):
    
        
    def __init__(self, master=None):
        Frame.__init__(self, master, width=640, height=700)
        self.pack();

        # Game state: -1 -> quit, 0 -> first, 1 -> second, 2 -> gameEngine 3;
        self.gameMode = GameState.Idle;
        self.gameState = GameState.Idle;

        self.initResource();

        self.createBoard();
        
        self.initBoard();

    def destroy(self):
        self.gameEngine.release();
        self.gameState = GameState.Exit;
        Frame.destroy(self);

    def initResource(self):

        # Images sets.
        self.images = {};
        im = self.images;
        im['go_u'] = PhotoImage(file='imgs/go_u.gif');
        im['go_ul'] = PhotoImage(file='imgs/go_ul.gif');
        im['go_ur'] = PhotoImage(file='imgs/go_ur.gif');
        im['go'] = PhotoImage(file='imgs/go.gif');
        im['go_l'] = PhotoImage(file='imgs/go_l.gif');
        im['go_r'] = PhotoImage(file='imgs/go_r.gif');
        im['go_d'] = PhotoImage(file='imgs/go_d.gif');
        im['go_dl'] = PhotoImage(file='imgs/go_dl.gif');
        im['go_dr'] = PhotoImage(file='imgs/go_dr.gif');
        im['go_-'] = PhotoImage(file='imgs/go_-.gif');
        im['go_b'] = PhotoImage(file='imgs/go_b.gif');
        im['go_w'] = PhotoImage(file='imgs/go_w.gif');

        im['angel'] = PhotoImage(file='imgs/Emotes-face-angel.png');
        im['laugh'] = PhotoImage(file='imgs/Emotes-face-laugh.png');
        im['plain'] = PhotoImage(file='imgs/Emotes-face-plain.png');
        im['raspberry'] = PhotoImage(file='imgs/Emotes-face-raspberry.png');
        im['sad'] = PhotoImage(file='imgs/Emotes-face-sad.png');
        im['smile'] = PhotoImage(file='imgs/Emotes-face-smile.png');
        im['smile-big'] = PhotoImage(file='imgs/Emotes-face-smile-big.png');
        im['surprise'] = PhotoImage(file='imgs/Emotes-face-surprise.png');
        im['uncertain'] = PhotoImage(file='imgs/Emotes-face-uncertain.png');
        im['wink'] = PhotoImage(file='imgs/Emotes-face-wink.png');

        self.faces = {};
        waiting = [im['angel'], im['raspberry'], im['smile'], im['wink']];
        self.faces[GameState.Idle] = waiting;
        self.faces[GameState.WaitForHumanFirst] = waiting;
        self.faces[GameState.WaitForHumanSecond] = waiting;
        waitingSad = [im['plain'], im['sad'], im['surprise'], im['uncertain'] ];
        self.faces['LowScore'] = waitingSad;
        searching = [im['plain'], im['surprise'], im['uncertain'] ];
        self.faces[GameState.WaitForEngine] = searching;
        won = [im['angel'], im['laugh'], im['raspberry'], im['smile'], im['smile-big'], im['wink'] ];
        self.faces['win'] = won;
        lost = [im['plain'], im['sad'], im['surprise'], im['uncertain'], ];
        self.faces['lose'] = lost;

        # Game engines
        self.gameEngine = GameEngine();
        self.searchThread = Thread(target = self.searching);
        self.searchThread.start();

        # Widgets
        self.canvas = Canvas(self, width=640, height=640);
        self.canvas.pack(side=LEFT, fill=BOTH, expand=1);
        # Button widgets
        self.controlFrame = LabelFrame(self);
        self.controlFrame.pack(fill=BOTH, expand=1);
        
        self.controlFrame.aiLevel = labelframe = LabelFrame(self.controlFrame, text='GameEngine AI Level');
        labelframe.pack(fill=X, expand=1);
        self.aiLevel = IntVar();
        #print(self.aiLevel.get());
        labelframe.lowRBtn = Radiobutton(labelframe, text="Low", variable=self.aiLevel, value=4);
        labelframe.lowRBtn.select();
        labelframe.lowRBtn.pack( anchor = W );
        labelframe.mediumRBtn = Radiobutton(labelframe, text="Medium", variable=self.aiLevel, value=5);
        labelframe.mediumRBtn.pack( anchor = W )
        labelframe.highRBtn = Radiobutton(labelframe, text="High", variable=self.aiLevel, value=6);
        labelframe.highRBtn.pack( anchor = W );
        self.vcf = IntVar();
        chbox = Checkbutton(labelframe, text = "With VCF", variable = self.vcf, );
        chbox.select();
        chbox.pack(anchor = W );
        # print(self.vcf.get());

        self.controlFrame.selectBlack = labelframe = LabelFrame(self.controlFrame, text='Black Player');
        labelframe.pack(fill=X, expand=1);
        labelframe.blackImg = Label(labelframe, image=self.images['go_b']);
        labelframe.blackImg.pack(side=LEFT, anchor = W);
        self.blackSelected = StringVar();
        labelframe.humanRBtn = Radiobutton(labelframe, text="Human", variable=self.blackSelected, value=' ');
        labelframe.humanRBtn.select();
        labelframe.humanRBtn.pack( anchor = W );
        labelframe.engineRBtn = Radiobutton(labelframe, text="GameEngine", variable=self.blackSelected, value='engine');
        labelframe.engineRBtn.pack( anchor = W );
        #print(self.blackSelected.get());
        
        self.controlFrame.selectWhite = labelframe = LabelFrame(self.controlFrame, text='White Player');
        labelframe.pack(fill=X, expand=1);
        labelframe.whiteImg = Label(labelframe, image=self.images['go_w']);
        labelframe.whiteImg.pack(side=LEFT, anchor = W);
        self.whiteSelected = StringVar();
        labelframe.humanRBtn = Radiobutton(labelframe, text="Human", variable=self.whiteSelected, value=' ');
        labelframe.humanRBtn.select();
        labelframe.humanRBtn.pack( anchor = W );
        labelframe.engineRBtn = Radiobutton(labelframe, text="GameEngine", variable=self.whiteSelected, value='engine');
        labelframe.engineRBtn.pack( anchor = W );
        
        self.controlFrame.gameContral = labelframe = LabelFrame(self.controlFrame, text='Game Contral');
        labelframe.pack(fill=X, expand=1);
        labelframe.newBtn = Button(labelframe, text='Start Game', command=self.newGame);
        labelframe.newBtn.pack(side=TOP, fill=X);
        labelframe.backBtn = Button(labelframe, text='Back Move', command=self.saveGame);
        labelframe.backBtn.pack(fill=X);
        labelframe.loadBtn = Button(labelframe, text='Load Engine', command=self.loadGameEngine);
        labelframe.loadBtn.pack(fill=BOTH);
        labelframe.quitBtn = Button(labelframe, text='Quit Game', command=root.destroy);
        labelframe.quitBtn.pack(fill=X);

        self.controlFrame.aiStatus = labelframe = LabelFrame(self.controlFrame, text='AI Status');
        labelframe.pack(side=BOTTOM, fill=BOTH, expand="yes");
        labelframe.name = Label(labelframe, text='Game Engine Name');
        labelframe.name.pack(side=TOP, anchor = W);
        labelframe.image = Label(labelframe, image=self.images['smile']);
        labelframe.image.pack(side=TOP, anchor = W);
        labelframe.info = Label(labelframe, text='');
        labelframe.info.pack(side=BOTTOM, anchor = W);

        #self.initGameEngine();

        self.updateStatus();

    def isVcf(self):
        vcf = True;
        if self.vcf.get() < 1:
            vcf = False;
        # print('VCF', vcf);
        return vcf;

    def loadGameEngine(self):
        fileName = filedialog.askopenfilename(title='Load executable file for new game engine ', initialdir='engines');
        print('Load game engine:', fileName);
        if len(fileName) > 0:
            self.initGameEngine(fileName);

    def initGameEngine(self, fileName=''):
        self.gameEngine.init(fileName, self.aiLevel.get(), self.isVcf());
        # Change the engine name
        shortName = self.gameEngine.shortName.capitalize();
        self.controlFrame.aiLevel['text'] = shortName + ' AI Level';
        self.controlFrame.selectBlack.engineRBtn['text'] = shortName;
        self.controlFrame.selectWhite.engineRBtn['text'] = shortName;
        name = self.gameEngine.name.capitalize();
        self.controlFrame.aiStatus.name['text'] = name;
        #root.title('Cloudict.Connect6 - ' + name);

    def createBoardUnit(self, x, y, imageKey):
        lb = Label(self.canvas, height=32, width=32);
        lb.x = x;
        lb.y = y;
        lb['image'] = self.images[imageKey];
        lb.initImage = self.images[imageKey];
        lb.bind('<Button-1>', self.onClickBoard);
        self.gameBoard[x][y] = lb;

        return lb;

    def createBoard(self):
        self.gameBoard = [ [ 0 for i in range(Move.EDGE) ] for i in range(Move.EDGE)];
        self.moveList = [];
        images = self.images;
        gameBoard = self.gameBoard;
        canvas = self.canvas;
        # Upper
        self.createBoardUnit(0, 0, 'go_ul');
        for j in range(1, 18):
            self.createBoardUnit(0, j, 'go_u');
        self.createBoardUnit(0, 18, 'go_ur');

        # Middle
        for i in range(1,18):
            gameBoard[i][0] = self.createBoardUnit(i, 0, 'go_l');
            for j in range(1,18):
                gameBoard[i][j] = self.createBoardUnit(i, j, 'go');

            gameBoard[i][18] = self.createBoardUnit(i, 18, 'go_r');

        # Block point in the board
        self.createBoardUnit(3, 3, 'go_-');
        self.createBoardUnit(3, 9, 'go_-');
        self.createBoardUnit(3, 15, 'go_-');
        self.createBoardUnit(9, 3, 'go_-');
        self.createBoardUnit(9, 9, 'go_-');
        self.createBoardUnit(9, 15, 'go_-');
        self.createBoardUnit(15, 3, 'go_-');
        self.createBoardUnit(15, 9, 'go_-');
        self.createBoardUnit(15, 15, 'go_-');

        # Down
        self.createBoardUnit(18, 0, 'go_dl');
        for j in range(1,18):
            self.createBoardUnit(18, j, 'go_d');
        self.createBoardUnit(18, 18, 'go_dr');

    def saveGame(self):
        pass;

    def initBoard(self):
        self.moveList.clear();
        gameBoard = self.gameBoard;
        for i in range(Move.EDGE):
            for j in range(Move.EDGE):
                gameBoard[i][j]['image'] = gameBoard[i][j].initImage;
                gameBoard[i][j].color = 0;
                gameBoard[i][j].grid(row=i, column=j);

    def connectedByDirection(self, x, y, dx, dy):
        gameBoard = self.gameBoard;
        cnt = 1;
        xx = dx; yy = dy;
        while Move.isValidPosition(x+xx, y+yy) and gameBoard[x][y].color == gameBoard[x+xx][y+yy].color:
            xx += dx; yy += dy;
            cnt += 1;
        xx = -dx; yy = -dy;
        while Move.isValidPosition(x+xx, y+yy) and gameBoard[x][y].color == gameBoard[x+xx][y+yy].color:
            xx -= dx; yy -= dy;
            cnt += 1;
        if cnt >= 6:
            return True;
        return False;
        
    def connectedBy(self, x, y):
        # Four direction
        if self.connectedByDirection(x, y, 1, 1):
            return True;
        if self.connectedByDirection(x, y, 1, -1):
            return True;
        if self.connectedByDirection(x, y, 1, 0):
            return True;
        if self.connectedByDirection(x, y, 0, 1):
            return True;
        return False;

    def isWin(self, move):
        if move.isValidated():
            return self.connectedBy(move.x1, move.y1) or self.connectedBy(move.x2, move.y2);
        return False;

    def nextColor(self):
        color = Move.BLACK;
        if len(self.moveList) % 2 == 1:
            color = Move.WHITE;
        return color;

    def waitForMove(self):
        color = self.nextColor();
        while True:
            msg = self.gameEngine.waitForNextMsg();
            move = Move.fromCmd(msg, color);
            # print('Wait move:', move);
            self.updateStatus();
            if move != None:
                break;
            
        return move

    def searching(self):
        while True:
            try:
                if self.gameMode == GameState.AI2AI or self.gameMode == GameState.AI2Human:
                    if self.gameState == GameState.WaitForEngine:
                        self.gameEngine.next(self.moveList);
                        move = self.waitForMove();
                        self.gameEngine.color = move.color;
                        self.makeMove(move);
                        if self.gameState == GameState.WaitForEngine and self.gameMode == GameState.AI2Human:
                            self.toGameState(GameState.WaitForHumanFirst);
                elif self.gameState == GameState.Exit:
                    break;
                else:
                    sleep(0.5);
            except Exception as e:
                print('Exception when searching: ' + e);
                sleep(0.5);

    def updateStatus(self):
        image = random.sample(self.faces.get(GameState.Idle), 1)[0];
        ls = self.faces.get(self.gameState);
        # According to gameState.
        if ls != None and len(ls) > 0:
            image = random.sample(ls, 1)[0];
            
        self.controlFrame.aiStatus.image['image'] = image;

        msg = 'Press start to game.';
        if self.gameState == GameState.Win:
            if self.winner == self.gameEngine.color:
                msg = 'I win!';
            else:
                msg = 'I lose!';
        elif self.gameState == GameState.WaitForHumanFirst:
            msg = 'Move the first...';
        elif self.gameState == GameState.WaitForHumanSecond:
            msg = 'Move the second...';
        elif self.gameState == GameState.WaitForEngine:
            msg = 'Thinking.';
            # Check format: Searching 31/37

            if self.gameEngine.msg.startswith('Searching '):
                s = self.gameEngine.msg.split(' ')[1];
                ls = s.split('/');
                cnt = float(ls[0])/float(ls[1]) * 20;
                msg += '.' * int(cnt);
        self.controlFrame.aiStatus.info['text'] = msg;

            
    def otherColor(self, color):
        if color == Move.BLACK:
            return Move.WHITE;
        elif color == Move.WHITE:
            return Move.BLACK;
        return Move.NONE;

    def newGame(self):
        self.gameEngine.release();
        self.initBoard();
        black = self.blackSelected.get().strip();
        white = self.whiteSelected.get().strip();
        if black == '' and white == '':
            self.toGameMode(GameState.Human2Human);
            self.toGameState(GameState.WaitForHumanFirst);
        elif black != '' and white != '':
            self.toGameMode(GameState.AI2AI);
            self.initGameEngine();
            self.toGameState(GameState.WaitForEngine);
        else:
            self.initGameEngine();
            self.toGameMode(GameState.AI2Human);
            if black != '':
                self.toGameState(GameState.WaitForEngine);
            else:
                self.toGameState(GameState.WaitForHumanFirst);

    def makeMove(self, move):
        if move.isValidated():
            self.placeStone(move.color, move.x1, move.y1);
            self.placeStone(move.color, move.x2, move.y2);
            self.moveList.append(move);
            # print('Made move:', move);
        return move;

    def placeStone(self, color, x, y):
        if color == Move.BLACK:
            imageKey = 'go_b';
        elif color == Move.WHITE:
            imageKey = 'go_w';
        else:
            return ;
        self.gameBoard[x][y].color = color;
        self.gameBoard[x][y]['image'] = self.images[imageKey];
        self.gameBoard[x][y].grid(row=x, column=y);
        if self.connectedBy(x, y):
            self.winner = color;
            self.toGameState(GameState.Win);
            if color == Move.BLACK:
                messagebox.showinfo("Black Win", "Black Win;) Impressive!")
            else:
                messagebox.showinfo("White Win", "White Win;) Impressive!")

    def isNoneStone(self, x, y):
        return self.gameBoard[x][y].color == Move.NONE;

    def toGameMode(self, mode):
        self.gameMode = mode;

    def toGameState(self, state):
        self.gameState = state;
        self.updateStatus();

    def onClickBoard(self, event):
        x = event.widget.x;
        y = event.widget.y;
        if not self.isNoneStone(x, y):
            return ;
        if self.gameMode == GameState.Human2Human:
            color = self.nextColor();
            if len(self.moveList) == 0:
                # First Move for Black
                self.move = Move(color, x, y, x, y);
                self.placeStone(self.move.color, x, y);
                self.moveList.append(self.move);
                self.toGameState(GameState.WaitForHumanFirst);
                
            elif self.gameState == GameState.WaitForHumanFirst:
                self.move = Move(color, x, y);
                self.placeStone(self.move.color, x, y);
                if self.gameState == GameState.WaitForHumanFirst:
                    self.toGameState(GameState.WaitForHumanSecond);
                
            elif self.gameState == GameState.WaitForHumanSecond:
                self.move.x2 = x;
                self.move.y2 = y;
                self.placeStone(self.move.color, x, y);
                self.moveList.append(self.move);
                if self.gameState == GameState.WaitForHumanSecond:
                    self.toGameState(GameState.WaitForHumanFirst);
            
            return ;
        
        if self.gameMode == GameState.AI2Human:
            color = self.nextColor();
            # print(color);
            if len(self.moveList) == 0 and self.gameState == GameState.WaitForHumanFirst:
                # First Move for Black
                self.move = Move(color, x, y, x, y);
                self.moveList.append(self.move);
                self.placeStone(self.move.color, x, y);
                self.toGameState(GameState.WaitForEngine);
                
            elif self.gameState == GameState.WaitForHumanFirst:
                self.move = Move(color, x, y);
                self.placeStone(self.move.color, x, y);
                if self.gameState == GameState.WaitForHumanFirst:
                    self.toGameState(GameState.WaitForHumanSecond);
                    
            elif self.gameState == GameState.WaitForHumanSecond:
                self.move.x2 = x;
                self.move.y2 = y;
                self.placeStone(self.move.color, x, y);
                self.moveList.append(self.move);
                if self.gameState == GameState.WaitForHumanSecond:
                    self.toGameState(GameState.WaitForEngine);

        return ;
        

root = Tk();

# create the application
app = App(root)

#
# here are method calls to the window manager class
#
app.master.title('Cloudict.Connect6')
# app.master.maxsize(840, 840)

# start the program
app.mainloop()


