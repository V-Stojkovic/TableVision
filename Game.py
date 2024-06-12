import time
from server import TCPserver
import client
from typing import Union
from queue import Queue
from threading import Thread
'''This file acts as the back-end of the project and links the cameras to the GUI, communication with other two files through TCP'''

class Team():
    def __init__(self,name) -> None:
        self.name = name
        self.__coach = None
        self.__players = {}
        self.__fouls = 0
        self.__to_taken =0
    def addTO(self):
        self.__to_taken += 1
    def getTO(self):
        return self.__to_taken
    def addFoul(self):
        self.__fouls +=1
    def resetFoul(self):
        self.__fouls = 0
    def setCoach(self,coach:str):
        self.__coach= coach
    def getCoach(self):
        return self.__coach
    def addPlayer(self,number:int):
        self.__players[number]= 0
    def getPlayerFouls(self,number):
        found = False
        for key in self.__players:
            if key == number:
                return self.__players[key]
                found = True
        if not found:
            print('PLAYER NOT FOUND')
            return None



class Game():
    def __init__(self,home_team:Team,away_team:Team):
        self.home= home_team
        self.away= away_team
        self.__home_score = 0
        self.__away_score = 0
        self.__periods = {'1':None,
                          '2':None,
                          'Half Time':None,
                          '3':None,
                          '4':None,
                          'OT':None}
        self.__current_period_index = 0
        self.__current_period = list(self.__periods.keys())[self.__current_period_index]
        self.__current_period = '1'
        self.__setup = False
        self.__running = False
        self.__finished = False
    def mainloop(self):

        TCPresults = Queue()
        server = TCPserver(5006,'localhost',TCPresults)
        sever_thread = Thread(target=server.start)
        sever_thread.start()
        connections = {'client':False,
                       'vision':False}
        while True:
            if TCPresults.empty():
                continue
            else:
            
                connect_msg = TCPresults.get_nowait()
                print(connect_msg)

                if connect_msg == 'CLIENT: GUI CONNECTED':
                    connections['client'] =True
                if connect_msg == 'CLIENT: VISION CONNECTED':
                    connections['vision'] =True
            if connections['client'] and connections['vision']:
                print('CONNECTIONS COMPLETE')
                break
        sender = client.TCPclient('localhost',5001,client_id=1)
        vision_sender = client.TCPclient('localhost',5002,client_id=1)

        while not self.__finished:
            # get the most recent signal that has been sent
            if TCPresults.empty():
                pass
            else:
                most_recent_signal = TCPresults.get()
                print(most_recent_signal)
            
                header = most_recent_signal[0]
                most_recent_signal.remove(header)

                next_stop_actions = [] # this list stores actions to be perfomed when the clock has stopped, timeout or subs
                print('MSG RECVIEVED:',header)
                if header == 'SETUP':

                    self.__periods['1'] = most_recent_signal[0][1]
                    self.__periods['2'] = most_recent_signal[0][1]
                    self.__periods['3'] = most_recent_signal[0][1]
                    self.__periods['4'] = most_recent_signal[0][1]
                    self.__periods['Half Time'] = most_recent_signal[1][1]
                    self.__periods['OT'] = most_recent_signal[2][1]
                    self.home.name = most_recent_signal[3][1]
                    self.away.name = most_recent_signal[3][1]
                    self.__setup = True
                    self.__current_period_index = 0
                    print(self.__periods)
                    sender.send(['SET CLOCK',self.__current_period,self.__periods[self.__current_period]])
                    print('SERVER: SET UP COMPLETE')

                elif header == 'SEND_FRAMES':
                    print('SERVER: SENDING FRAME REQUEST')
                    vision_sender.send('SEND_FRAMES')
                
                elif header == 'STOP_FRAMES':
                    print('SERVER:STOPPING FRAME REQUEST')
                    vision_sender.send('STOP_FRAMES')

                if self.__setup:
                    if header == '2-POINTS-SCORED':
                        direction = most_recent_signal[0]
                        if direction =='A' and self.__current_period < 3:
                            self.__home_score +=2
                            sender.send(['HOME','2'])
                        elif direction == 'B' and self.__current_period >2 :
                            self.__home_score +=2
                            sender.send(['HOME','2'])
                        else: 
                            self.__away_score += 2
                            sender.send(['AWAY','2'])

                    elif header == '1-POINT-SCORED':
                        direction = most_recent_signal[0]
                        if direction =='A' and self.__current_period < 3: # checking motion detection based on which way the team is scoring
                            self.__home_score +=1
                            sender.send(['HOME','1'])
                        elif direction == 'B' and self.__current_period >2 :
                            self.__home_score +=1
                            sender.send(['HOME','1'])
                        else: 
                            self.__away_score += 2
                            sender.send(['AWAY','2'])

                    elif header == '3-POINTS SCORED':
                        direction = most_recent_signal[0]
                        if direction =='A' and self.__current_period < 3:
                            self.__home_score +=3
                            sender.send(['HOME','3'])
                        elif direction == 'B' and self.__current_period >2 :
                            self.__home_score +=3
                            sender.send(['HOME','3'])
                        else: 
                            self.__away_score += 3
                            sender.send(['AWAY','3'])

                    elif header == 'STOP FOR FOUL':
                        if self.__running:
                            if most_recent_signal[0] == 'LEFT':
                                self.away.addFoul()
                                sender.send(['AWAY-FOUL'])
                            else:
                                self.home.addFoul()
                                sender.send(['HOME-FOUL'])
                        self.__running = False
                    
                    elif header == 'SUBS':
                        if 'SUBSTITUTION' not in next_stop_actions:
                            next_stop_actions.append('SUBSTITUTION')

                    elif header == 'TIMEOUT-REQUESTED':
                        if most_recent_signal[0] == 'HOME':
                            if (self.home.getTO() > 2 and (self.__periods ==' 1' or self.__periods=='2')) or (self.home.getT0()>3 and (self.__periods =='3' or self.__periods=='4')):
                                next_stop_actions.append('TIME OUT HOME')
                                self.home.addTO()
                            else:
                                pass
                        elif most_recent_signal[0] =='AWAY':
                            if (self.away.getTO() > 2 and (self.__periods ==' 1' or self.__periods=='2')) or (self.away.getT0()>3 and (self.__periods =='3' or self.__periods=='4')):
                                next_stop_actions.append('TIME OUT AWAY')
                                self.away.addTO()
                            else:
                                pass
                            
                    elif header == 'TIME-OUT-CANCELLED':
                        try:
                            next_stop_actions.remove('TIME OUT HOME')
                            next_stop_actions.remove('TIME OUT AWAY')
                        except ValueError:
                            pass

                    elif header == 'STOP FOR VIOLATION':
                        if self.__running:
                            sender.send(['STOP CLOCK'])
                            if len(next_stop_actions)>0:
                                sender.send(next_stop_actions)
                        self.__running = False

                    elif header == 'START CLOCK':
                        if not self.__running:
                            sender.send(['START CLOCK'])
                        self.__running = True
            
                    elif header == 'END OF PERIOD':
                        if self.__current_period_index < len(list(self.__periods.keys())):
                            self.__current_period_index += 1 # updates index
                            self.__current_period = list(self.__periods.key())[self.__current_period_index] # updates server side current period
                            sender.send(['SET CLOCK',self.__current_period,self.__periods[self.__current_period]]) #sends update message to clock
                        else:
                            self.__finished = True
                    
if __name__ == '__main__':
    home_team = Team('Home Team')
    away_team = Team('Away Team')
    game = Game(home_team,away_team)
    game.mainloop()