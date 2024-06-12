import tkinter as tk
import time
from pathlib import Path
from typing import Optional, Tuple, Union
import customtkinter as ctk
from PIL import Image, ImageOps
import server
import client
import queue
import threading
'''This module is the frontend of the TableVision project'''
__author__ = 'Vuk Stojkovic'
__copyrights__ = '2023, Vuk Stojkovic'


#Load Images from assets folder
PATH = Path(__file__).resolve().parent.joinpath('assets')
PAUSE = ctk.CTkImage(Image.open(PATH.joinpath('pause.png')),size=(100,100))
PAUSE_HOVER = ctk.CTkImage(Image.open(PATH.joinpath('Pause_hover.png')),size=(100,100))
PLAY= ctk.CTkImage(Image.open(PATH.joinpath('play.png')),size=(100,100))
PLAY_HOVER= ctk.CTkImage(Image.open(PATH.joinpath('Play_hover.png')),size=(100,100))
POSS_ARROW = Image.open(PATH.joinpath('Possesion_left.png'))
POSS_ARROW_RIGHT = ctk.CTkImage(ImageOps.mirror(POSS_ARROW),size=(130,130))
POSS_ARROW_LEFT= ctk.CTkImage(POSS_ARROW,size=(130,130))
CIRCLE_FULL=ctk.CTkImage(Image.open(PATH.joinpath('CircleFull.png')),size=(100,100))
CIRCLE_EMPTY=ctk.CTkImage(Image.open(PATH.joinpath('CircleEmpty.png')),size=(100,100))
TO_IMAGE = ctk.CTkImage(Image.open(PATH.joinpath('TO_image.png')),size=(130,130))
TO_HOVER = ctk.CTkImage(Image.open(PATH.joinpath('TO_hover_image.png')),size=(130,130))
TO_CLICKED = ctk.CTkImage(Image.open(PATH.joinpath('TO_clicked_image.png')),size=(130,130))
CAMERA_ICON = ctk.CTkImage(Image.open(PATH.joinpath('Video_Camera.png')),size=(200,200))

#Set default theme from custome JSON in line with my chosen colour scheme
ctk.set_default_color_theme(PATH.joinpath('redtheme.JSON'))

class MyTabView(ctk.CTkTabview):
    def __init__(self,master,net_agent:client.TCPclient|None= None, **kwargs):
        '''
        Initialises the tab view object
        
        Parameters:
        - master(customtkinter.CTk): The master window to which the tab view belongs
        - net_agent(client.TCPclient): A TCPclient object which will communicate with the server
        - **kwargs: any additional keyword arguments associated with the customtkiner CTkTabView object
        
        Returns:
        None
        '''
        super().__init__(master,**kwargs)
        self._command = self.checkTab
        self.networkagent = net_agent
        self.__recv = False
        self.__udp_running =False
        self.frameQueue = queue.Queue()
        self.udp_recv = server.UDPserver(result_queue=self.frameQueue)
        self.add('Game')
        self.add('Open CV Feed')
        self.add('Logs')
        self.create_Game_tab()
        self.createLogTab()
        self.__create_CV_View_tab()   
    def updateClock(self,seconds:str):
        '''
        Updates the value displayed on the clock widget
        
        Parameters:
        - seconds(Int): The number of seconds to be displayed
        
        Returns:
        None'''
        print('UPDATING CLOCK')
        mins,secs = divmod(seconds,60)
        timeformat = '{:02d}:{:02d}'.format(mins,secs)
        self.__seconds.set(timeformat)
    def setPeriod(self,value):
        '''
        Updates the value for the period of play
        
        Parameters:
        - value(any): The value for the period of play'''
        self.__q_no_label.configure(text=value)

    def checkTab(self):
        '''
        Checks which tab is currently being displayed and messages the server accordingly
        
        Returns:
        None
        '''
        if self.get() == 'Open CV Feed':
            try:
                self.networkagent.send(['SEND_FRAMES'])
                self.__recv = True
                cv_thread = threading.Thread(target=self.getFrames)
                cv_thread.start()
            except BrokenPipeError:
                print('CONNECTION NOT ESTABLISHED')
        else:
            try:
                self.networkagent.send(['STOP_FRAMES'])
                self.__recv=False
            except BrokenPipeError:
                print('CONNECTION BROKEN')

    def getFrames(self):
        '''
        Runs the UDP server if it is not already running and retrieves frames from frame queue and updates the appropriate ImageButton
        
        Returns:
        None
        '''
        if not self.__udp_running:
            server_thread = threading.Thread(target=self.udp_recv.run)
            server_thread.start()
            
            self.__udp_running = True
        count = 0
        while self.__recv:
            if self.frameQueue.empty():
                pass
            else:
                # print('TRYING TO DISPLAY FRAME')
                frame = self.frameQueue.get()
                if count%2 ==0:
                    self.updateImage(new_image1=frame)
                    # print('IMAGE1 UPDATED')
                else:
                    self.updateImage(new_image2=frame)
                    # print('IMAGE2 UPDATED')
                count +=1

    def create_Game_tab(self):
        '''
        Instantiates widgets which belong to the game tab
        
        Returns:
        None
        '''
        self.__seconds = ctk.StringVar()
        self.__seconds.set('01:00')
        self.__home_score = ctk.CTkLabel(self.tab('Game'),
                                         text='0',
                                         fg_color='transparent'
                                         ,text_color='red'
                                         ,font=ctk.CTkFont('Terminal',
                                                           150,
                                                           weight='bold'))
        self.__away_score = ctk.CTkLabel(self.tab('Game'),
                                         text='0',
                                         fg_color='transparent',
                                         text_color='red',
                                         font=ctk.CTkFont('Terminal',
                                                          150,
                                                          weight='bold'))

        self.__home_score.place(relx= 0.05,
                                rely=0.1)
        self.__away_score.place(relx= 0.79,
                                rely=0.1)

        self.__home_label = ctk.CTkLabel(self.tab('Game'),
                                         text='HOME',
                                         fg_color='transparent',
                                           text_color='white',
                                           font=ctk.CTkFont('Terminal',
                                                            70))
        
        self.__away_label = ctk.CTkLabel(self.tab('Game'),
                                         text='AWAY',
                                         fg_color='transparent',
                                         text_color='white',
                                         font=ctk.CTkFont('Terminal',70))

        self.__home_label.place(relx=0.07, rely= 0.4)
        self.__away_label.place(relx=0.81, rely= 0.4)

        self.__q_no_label = ctk.CTkLabel(self.tab('Game'),
                                         text='0',
                                         fg_color='transparent',
                                         text_color='white',
                                         font=ctk.CTkFont('Terminal',
                                                          100,
                                                          weight='bold'))
        self.__q_no_label.place(relx = 0.45,rely= 0.1,relwidth = 0.11)

        self.__poss_arrow = ctk.CTkLabel(self.tab('Game'),text='',image=POSS_ARROW_LEFT)
        self.__poss_arrow.place(relx= 0.37,rely=0.1)

        self.__clock_label = ctk.CTkLabel(self.tab('Game'),
                                  textvariable = self.__seconds,
                                  text_color='red',
                                  fg_color='transparent',
                                  font=ctk.CTkFont('Terminal',120,weight='bold'))
        self.__clock_label.place(relx=0.35,rely=0.4,relheight=0.2,relwidth=0.3)

        self.__home_foul_label = ctk.CTkLabel(self.tab('Game'),
                                              text='0',
                                              fg_color='transparent',
                                              text_color='orange',
                                              font=ctk.CTkFont('Terminal',
                                                               100,
                                                               weight = 'bold'))
        
        self.__away_foul_label = ctk.CTkLabel(self.tab('Game'),
                                              text='0',
                                              fg_color='transparent',
                                              text_color='orange',
                                              font=ctk.CTkFont('Terminal',
                                                               100,
                                                               weight = 'bold'))

        self.__home_foul_label.place(relx =0.12,rely = 0.78)
        self.__away_foul_label.place(relx =0.85,rely = 0.78)
        self.clock = Clock(self.__clock_label,self.__seconds,self.networkagent)

    def flipPossession(self):
        '''
        Changes the oreination of the possession arrow
        
        Returns:
        None'''
        if self.__poss_arrow.cget('image') == POSS_ARROW_LEFT:
            self.__poss_arrow.configure(image=POSS_ARROW_RIGHT)
            self.__poss_arrow.place(relx =0.56,rely=0.1)
        elif self.__poss_arrow.cget('image') == POSS_ARROW_RIGHT:
            self.__poss_arrow.configure(image=POSS_ARROW_LEFT)
            self.__poss_arrow.place(relx =0.37,rely=0.1)
    
    def __create_CV_View_tab(self):
        '''
        Creates the CV_view tab by instantiating and placing the relevant widgets
        
        Returns:
        None
        '''
        
        self.__cam1_feed = ctk.CTkLabel(self.tab('Open CV Feed'),image=CAMERA_ICON,fg_color='grey',text='',corner_radius=5)
        self.__cam1_feed.place(relx = 0.01,rely=0.01,relwidth=0.48,relheight = 0.98)
        
        self.__cam2_feed = ctk.CTkLabel(self.tab('Open CV Feed'), image=CAMERA_ICON,fg_color='grey',text='',corner_radius=5)
        self.__cam2_feed.place(relx=0.51,rely=0.01,relwidth=0.48,relheight=0.98)
    
    def updateImage(self,new_image1:ctk.CTkImage|None=None,new_image2: ctk.CTkImage |None = None):
        '''
        Changes the image(s) in the cv_view frame
        
        Parameters:
        - new_image1 (customtkinter.CTkImage): Image to be displayed in the left slot. Default is None
        - new_image2 (customtkinter.CTkImage): Image to be displayed in the right slot. Default is None

        Returns:
        None'''
        if new_image1:
            self.__cam1_feed.configure(image=new_image1)
            self.__cam1_feed.configure(fg_color = 'transparent')
        if new_image2:
            self.__cam2_feed.configure(image=new_image2)
            self.__cam2_feed.configure(fg_color = 'transparent')
    
    def createLogTab(self):
        '''
        Instantiates an instance of the TableView object in the Log Tab

        Returns:
        None
        '''
        self.table = TableView(master=self.tab('Logs'))
        self.table.place(relx=0,rely=0,relwidth=1,relheight=1)

       

    def updateScore(self,team:str,value:int):
        '''
        Updates the score label
        
        Parameters:
        - team(String): The team for which the score needs to be updated
        - value(Integer): The amount that needs to be added. To reduced a score a negative integer can be passed
        
        Returns:
        None
        '''
        if team.lower() =='home':
            current = self.__home_score.cget('text')
            self.__home_score.configure(text=str(int(current)+value))
        else:
            current=self.__away_score.cget('text')
            self.__away_score.configure(text=str(int(current)+value))
    
    def addFoul(self,team:str):
        '''
        Incriments the team foul count for the team specified in the parameters
        
        Parameters:
        - team(string): The team for which the foul count should be incrimented
        
        Returns:
        None'''
        if team.lower() =='home':
            current = self.__home_foul_label.cget('text')
            if current < 5:
                new = int(current) +1
                if new >5:
                    self.__home_foul_label.configure(text_color='red')
                self.__home_foul_label.configure(text=str(new))
        else:
            current = self.__away_foul_label.cget('text')
            if current < 5:
                new = int(current) +1
                if new >5:
                    self.__away_foul_label.configure(text_color ='red')
                self.__away_foul_label.configure(text=str(new))

    def reset(self,score=False,foul=False):
        '''
        Resets the value of specified cateogry in parameters
        
        Parameters:
        - score(Bool): If True the score for each team will be set to 0
        - foul(Bool): If True the foul count for each team will be set to 0
        
        Returns:
        None'''
        if score:
            self.updateScore(team='home',
                             value=(int(self.__home_score.cget('text'))*-1)) #resets score by adding the -current_score
            self.updateScore(team='away',
                             value=(int(self.__home_score.cget('text'))*-1)) #resets score by adding the -current_score
        if foul:
            self.__home_foul_label.configure(text='0')
            
class ImageButton(ctk.CTkLabel):
    '''Custom Button which can display an image'''
    def __init__(self, master=None,
                  default_image:ctk.CTkImage|None=None
                  ,hover_image:ctk.CTkImage|None=None
                  ,clicked_image:ctk.CTkImage|None=None
                  ,clicked_hover:ctk.CTkImage|None=None
                  ,command=None,**kwargs):
        '''
        Initialises the ImageButton object
        
        Parameters:
        - master (customtkiner.CTk): The master customtkiner window in which the button will be placed
        - default_image (customtkinter.CTkImage): Default image to be displayed
        - hover_image (customtkinter.CTkImage): Image to be displayed when the mouse is hovering over the button and it has not been clicked
        - clicked_image (customtkiner.CTkImage): Image to be displayed when the button has been clicked
        - clicked_hover (customtkiner.CTkImage): Image to be displayed when the button has been clicked and the mouse is hovering
        - command (any): The function to be executed when the button has been clicked. Default is None
        - **kwargs: any additional keyword arguments associated with customtkinter.CTkLabel
        
        Returns:
        None'''
        super().__init__(master,**kwargs)
        self.command = command
        # Load the default and hover images
        self.default_image = default_image
        self.hover_image = hover_image
        self.clicked_image =clicked_image
        self.clicked_hover = clicked_hover
        self.configure(image =default_image)
        self.clicked = False 

        # Bind the button events
        self.bind("<Button-1>", self.on_button_click)
        self.bind("<Enter>", self.on_mouse_enter)
        self.bind("<Leave>", self.on_mouse_leave)

    def on_button_click(self, event):
        '''
        Switches the image to the clicked version of the button and executes the command binded to the button
        
        Returns: 
        None'''
        if self.command:
            self.command()
        if self.clicked:
            self.configure(image =self.hover_image)
            self.clicked = False
        else:
            if self.clicked_image:
                self.configure(image =self.clicked_hover)
            self.clicked = True  
    
    def on_mouse_enter(self, event):
        '''
        Switches to the hovered image version if it has been provided
        
        Returns:
        None 
        '''
        if self.hover_image:
            if self.clicked:
                self.configure(image=self.clicked_hover)
            else:
                self.configure(image=self.hover_image)   

    def on_mouse_leave(self, event):
        '''
        Switches back to a non-hover image once the mouse is no longer above the button
        
        Returns:
        None
        '''

        if self.clicked:
            if self.clicked_image:
                self.configure(image=self.clicked_image)
        else:
            self.configure(image=self.default_image)

class TableView(ctk.CTkFrame):
    def __init__(self,master=None,**kwargs):
        '''
        Initialises the TableView object
        
        Parameters:
        - master(customtkinter.CTk): the master customtkiner window in which the object will be placed
        - **kwargs: any additional keyword arguments
        Returns:
        None
        '''

        super().__init__(master,**kwargs)
        self.rows =0
        self.columns =0
        self.width = kwargs.get('width')
        self.height = kwargs.get('height')
        
        self.__createHeader()
        self.most_recent = ctk.CTkLabel(self,text='Most recent signal',fg_color='white',text_color='black')
        self.most_recent.place(relx=0.01,rely=0.01,relheight=0.98,relwidth=0.2)
    
    def __createHeader(self):
        '''
        Creates the header for the table
        
        Returns:
        None
        '''

        self.createRow(['Quarter No.','Time','Signal'])

    def createRow(self,data:list):
        '''
        Creates a new row in the table
        
        Parameters:
        - data(list): data contents of the row to be added
        
        Returns:
        None
        '''
        self.rows += 1
        if self.rows ==1:
            row_colour= 'black'
            text ='white'
        elif self.rows %2 == 0:
            row_colour = 'grey'
            text= 'black'
        else:
            row_colour = 'white'
            text= 'black'
        if len(data) > self.columns:
            self.columns = len(data)
        row = []
        for i,e in enumerate(data):
            row.append(ctk.CTkLabel(self,text=e,fg_color=row_colour,text_color=text))
            row[i].place(relx=0.38+(i*0.2),rely =0.01+(0.05*self.rows),relwidth =0.2,relheight=0.05)
        
class ControlFrame(ctk.CTkFrame):
    def __init__(self,master,network_agent:client.TCPclient |None = None,**kwargs):
        '''
        Initialises the ControlFrame object
        
        Parameters:
        - master(customtkinter.CTk): The master customtkinter root
        - network_agent(client.TCPclient): The network agent for TCP communication. Default to None
        - **kwargs: any additional keyword arguments

        Returns:
        None
        '''

        super().__init__(master,**kwargs)
        self.__network_agent = network_agent
        
        self.pause_btn = ImageButton(self,
                                     command = self.pause,
                                     width= 50, height = 50,
                                     default_image=PAUSE,
                                     hover_image=PAUSE_HOVER,
                                     text='',clicked_image=PLAY,
                                     clicked_hover=PLAY_HOVER)
        self.pause_btn.place(relx=0.45,rely =0.01,relheight=0.98,relwidth = 0.1)

        self.TO_home = ImageButton(self,
                                   default_image=TO_IMAGE,
                                   hover_image=TO_HOVER,
                                   clicked_image=TO_CLICKED,
                                   command=lambda: self.Timeout('HOME'),
                                   width=80,height=80,text='')
        
        self.TO_home.place(relx= 0.01,rely=0.01,relheight=0.98)

        self.TO_away = ImageButton(self,
                                   default_image=TO_IMAGE,
                                   hover_image=TO_HOVER,
                                   clicked_image=TO_CLICKED,
                                   command=lambda: self.Timeout('AWAY'),
                                   width=80,height=80,text='')
        self.TO_away.place(relx=0.9,rely=0.01,relheight=0.98)

        self.sub_home = ctk.CTkButton(self,
                                      command=self.callSub,
                                      text = 'Substitution',
                                      fg_color='red',
                                      font=ctk.CTkFont('Terminal',40,weight='bold'))
        self.sub_away = ctk.CTkButton(self,
                                      command=self.callSub,
                                      text = 'Substitution',
                                      fg_color='red',
                                      font=ctk.CTkFont('Terminal',40,weight='bold'))

        self.sub_home.place(relx = 0.15, rely= 0.2, relheight = 0.6,relwidth = 0.2)
        self.sub_away.place(relx = 0.65, rely = 0.2, relheight = 0.6, relwidth = 0.2)

    def callSub(self):
        '''
        Sends a message to the server requesting a substitution
        
        Returns:
        None
        '''
        try:
            self.__network_agent.send(['SUBS'])
        except BrokenPipeError:
            print('CONNECTION BROKEN')

    def Timeout(self,team:str):
        '''
        Sends a message to the server requesting a time-out
        
        Parameters:
        - team(string): Specifies which team has requested the time-out
        Returns:
        None
        '''
        try:
            self.__network_agent.send(['TIME-OUT-REQUEST',team])
        except BrokenPipeError:
            print('CONNECTION BROKEN')
    def pause(self):
        '''
        Sends a message to the server to either start or stop the clock
        
        Returns: 
        None
        '''
        try:
            if self.pause_btn.clicked:
                self.__network_agent.send(['START CLOCK'])
            else: 
                self.__network_agent.send(['STOP FOR VIOLATION'])
        except BrokenPipeError:
            print('CONNECTION BROKEN')

class timeOutWindow(ctk.CTkToplevel):
    def __init__(self,length:int|None=None, *args, fg_color: str | Tuple[str, str] | None = None, **kwargs):
        '''
        Initialises the timeOutWindow object and begins a count up
        
        Parameters:
        - length(int): the length of time the window should be up for
        - fg_color(string or tuple): the foreground color of the window
        - **kwargs: any additional keyword arguments
        
        Returns:
        None
        '''

        super().__init__(*args, fg_color=fg_color, **kwargs)

        self.geometry(f'400x300+{(self.winfo_screenwidth() - self.winfo_reqwidth()) // 2}+{(self.winfo_screenheight() - self.winfo_reqheight()) // 2}') # Places the window in the centre of the screen
        self.grab_set()
        self.focus_set()
        self.overrideredirect(True)

        self.__totalTime = 0
        self.timer = Clock()
        team = kwargs.get('team')
        self.__timevar = ctk.StringVar()
        self.__timevar.set('00:00')
        self.__info_label = ctk.CTkLabel(self,text='TIME OUT {}'.format(team),
                                         font=ctk.CTkFont('Terminal',size=80,weight='bold'))
        self.__info_label.place(relx= 0.3,rely = 0.05,relwidth = 0.4,relheight = 0.2)

        self.__time_remaining = ctk.CTkLabel(self,textvariable=self.__timevar,
                                             text_color='orange',
                                             font=ctk.CTkFont('Terminal',size=80,weight='bold'))
        self.__time_remaining.place(relx= 0.35, rely=0.3, relwidth = 0.3, relheight= 0.3)

        timeoutThread = threading.Thread(target=self.__countup)
        timeoutThread.start()

        

    def __countup(self,length=60):
        '''
        Counts up every second up until the threshold had been reached
        
        Parameters:
        - lenght(int): the length of time the window should be displayed for default set at 60
        
        Returns:
        None
        '''
        while self.__totalTime < length:
            self.__totalTime +=1
            mins, secs = divmod(self.__totalTime, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            self.__timevar.set(timeformat)
            time.sleep(1)
        self.destroy() # destroys the pop-up window


class SetUpWindow(ctk.CTkToplevel):
    
    def __init__(self,network_agent:client.TCPclient|None =None, **kwargs):
        '''
        Initialises the Set-up window and places all relevant widgets
        
        Parameters:
        - network_agent(client.TCPClient): A client object which will communicate with the server
        - **kwargs: any additional keyword arguments

        Returns:
        None
        '''
        super().__init__(**kwargs)
        self.overrideredirect(True)
        
        self.PLACEHOLDER = ctk.StringVar(value='select value')
        self.__net_agent = network_agent
        self.geometry(f'400x300+{(self.winfo_screenwidth() - self.winfo_reqwidth()) // 2}+{(self.winfo_screenheight() - self.winfo_reqheight()) // 2}')
        # self.grab_set()
        # self.focus_set()
        
        self.fiba= False
        self.nba= False

        self.__team1 = ctk.CTkEntry(self,placeholder_text='Team 1',fg_color='grey',state='normal')
        self.__team1.place(relx=0.1,rely=0.2)

        self.__team2 = ctk.CTkEntry(self,placeholder_text='Team 2',fg_color='grey',state='normal')
        self.__team2.place(relx =0.6,rely=0.2)

        self.__landing_label = ctk.CTkLabel(master=self,
                                            text='Game Setup',
                                            font=ctk.CTkFont('Terminal',size=25,weight='bold'))
        self.__landing_label.place(relx=0.35,rely=0.05)

        self.__mins_label = ctk.CTkLabel(self,text='Quarter Length (mins):')
        self.__mins_label.place(relx=0.2,rely=0.45)

        self.__mins_box = ctk.CTkComboBox(self,values=['select value','5','6','7','8','9','10','12'],
                                          fg_color='grey')
        self.__mins_box.place(relx=0.6,rely=0.45,relwidth=0.3)
        
        self.__half_time_label = ctk.CTkLabel(self,text='Half-time Length:')
        self.__half_time_label.place(relx=0.2,rely=0.6)

        self.__half_time = ctk.CTkComboBox(master=self,values=['select value','5','10','15'],
                                           fg_color='grey')
        self.__half_time.place(relx=0.6,rely=0.6,relwidth=0.3)

        self.__overtime_label = ctk.CTkLabel(self,text='Overtime Length:')
        self.__overtime_label.place(relx=0.2,rely=0.75)

        self.__overtime_box = ctk.CTkComboBox(self,values=['select value','2','3','4','5'],
                                              fg_color='grey')
        self.__overtime_box.place(relx=0.6,rely=0.75,relwidth=0.3)

        self.__fiba_reg_btn = ctk.CTkButton(self,text='FIBA reg.',
                                            command=self.__set_FIBA)
        self.__fiba_reg_btn.place(relx=0.2,rely=0.3,relwidth=0.2)

        self.__NBA_reg_btn = ctk.CTkButton(self,text='NBA reg.',command=self.__set_NBA)
        self.__NBA_reg_btn.place(relx=0.6,rely=0.3,relwidth=0.2)

        self.__apply_btn = ctk.CTkButton(self,text='CONFIRM',
                                         command= self.__apply,
                                         font= ctk.CTkFont('Terminal',size=12,weight='bold'))
        self.__apply_btn.place(relx=0.6, rely =0.9,relwidth=0.3)

        self.__cancel_btn= ctk.CTkButton(self,text='Cancel',
                                         command=self.destroy,
                                         font= ctk.CTkFont('Terminal',size=12,weight='bold'))
        self.__cancel_btn.place(relx=0.2, rely =0.9,relwidth=0.3)

    def __set_NBA(self):
        '''
        Sets all values in accordance with NBA regulation and 
        changes the value of the combo-boxes accoridingly

        Returns:
        None
        '''
        if not self.nba:
            mins = ctk.StringVar(value ='12')
            ht = ctk.StringVar(value ='15')
            ot = ctk.StringVar(value ='5')
            self.__mins_box.configure(variable=mins)
            self.__half_time.configure(variable=ht)
            self.__overtime_box.configure(variable=ot)
        else:
            self.__init__(network_agent=self.__net_agent)

    def __set_FIBA(self):
        '''
        Sets all values in accordance with FIBA regulation and
        changes the value of the combo-boxes accordingly
        
        Returns:
        None
        '''
        if not self.fiba:
            mins = ctk.StringVar(value ='10')
            ht = ctk.StringVar(value ='15')
            ot = ctk.StringVar(value ='5')
            self.__mins_box.configure(variable=mins)
            self.__half_time.configure(variable=ht)
            self.__overtime_box.configure(variable=ot)
            self.fiba = True
        else:
            self.__init__(self.__net_agent)
    
    def __apply(self):
        '''
        Sends the values from the combo-boxes to the server
        
        Returns:
        None
        '''
        try:
            mins = self.__mins_box.get()
            ht = self.__half_time.get()
            ot = self.__overtime_box.get()
            team1= self.__team1.get()
            team2= self.__team2.get()
        except AttributeError:
            self.__landing_label.configure(text='FILL IN ALL VALUES',text_color='red')
            self.__landing_label.place(relx=0.3,rely=0.05)

        if mins != self.PLACEHOLDER and ht != self.PLACEHOLDER and ot != self.PLACEHOLDER and team1 !='' and team2 != '':
            self.__net_agent.send(['SETUP',
                                        ('mins',mins),
                                    ('half-time',ht),
                                    ('over-time',ot),
                                    ('Team 1',team1),
                                    ('Team 2',team2)])
            self.grab_release()
            self.destroy()
        else:
            self.__landing_label.configure(text='FILL IN ALL VALUES',text_color='red')
            self.__landing_label.place(relx=0.3,rely=0.05)

class Clock():

    def __init__(self,seconds_label:ctk.CTkLabel,seconds_var:ctk.StringVar,net_agent:client.TCPclient):
        '''
        Initialises the Clock object
        
        Parameters:
        - seconds_label (customtkinter.CTkLabel): The label which displays the time
        - seconds_var (customtkinter.CTkLabel): The stringvar holding the value for seconds_label
        - net_agent (client.TCPclient): Handles TCP communication when time runs out
        '''
        self.__seconds_label = seconds_label
        self.__seconds_var = seconds_var
        self.period = 1
        self.__running = False
        self.__pause_flag = threading.Event()
        self.__remaining_seconds= 0
        self.__sender = net_agent
    def update_timer(self):
        '''
        Updates the value on the timer
        
        Returns:
        None'''
        while self.__remaining_seconds > 0 and self.__running:
            if not self.__pause_flag.is_set():
                mins, secs = divmod(self.__remaining_seconds, 60)
                timeformat = '{:02d}:{:02d}'.format(mins, secs)
                self.__seconds_var.set(timeformat)
                time.sleep(1)
                self.__remaining_seconds -= 1
        if self.__remaining_seconds == 0:
            self.__seconds_var.set('TIMER FINISHED')
            self.__seconds_label.configure(text_color ='red')
            self.__sender.send(['END OF PERIOD'])

    def set_clock(self,value:int):
        '''
        Sets value of clock 
        
        Parameters:
        value (int) - number of seconds to be set on the clock
        
        Returns:
        None
        '''
        self.__remaining_seconds = 0
        self.__remaining_seconds = value
    def start_timer(self):
        '''
        Starts the timer if it is not already running
        
        Returns:
        None
        '''
        if not self.__running:
            self.__running = True
            self.__pause_flag.clear()
            self.update_thread = threading.Thread(target=self.update_timer)
            self.update_thread.start()
            self.after(1000, self.check_update_thread)

    def check_update_thread(self):
        '''
        checks whether the timer has been paused
        
        Returns:
        None'''
        if self.update_thread and not self.update_thread.is_alive():
            self.__running = False
        else:
            self.after(1000, self.check_update_thread)

    def pause_timer(self):
        '''
        Pauses the timer
        
        Returns:
        None'''
        self.__pause_flag.set()

class App(ctk.CTk):
    WIDTH= 3024
    HEIGHT= 1964
    def __init__(self):
        '''
        Initialises the App object
        
        Returns:
        None
        '''
        
        super().__init__()
        self.title('TableVision')
        self.geometry('3024x1964')

        self.__setup = False
        self.toplevel_window = None

        self.TCPres = queue.Queue()
        self.__listener = server.TCPserver(port=5001,address='localhost',results=self.TCPres)
        events_thread = threading.Thread(target=self.handleEvents)
        events_thread.start()        
        try:
            self.client = client.TCPclient(port=5006,client_id=1,server_address='localhost')
            self.client.send('CLIENT: GUI CONNECTED')

        except ConnectionRefusedError:
            print('SERVER IS NOT RUNNING')

        self.__setup = ctk.CTkButton(self,text='SETUP'
                                     ,font= ctk.CTkFont(family='Terminal',size=40),
                                     command=self.run_setup)
        self.__setup.place(relx=0.01,rely=0.01,relwidth = 0.2,relheight=0.08)

        self.__start_btn = ctk.CTkButton(self,text='START',
                                         command=self.__start,state='disabled',
                                         font= ctk.CTkFont(family='Terminal',size=40))
        self.__start_btn.place(relx=0.79,rely=0.01,relwidth=0.2,relheight =0.08)

        self.__landing_label = ctk.CTkLabel(self,text='TEAM 1 VS TEAM 2',font=('Terminal',40))
        self.__landing_label.place(relx=0.5,rely=0.05,anchor= tk.CENTER)

        self.__tabView = MyTabView(self,net_agent=self.client)
        self.__tabView.place(relx=0.01,rely=0.1,relwidth = 0.98,relheight =0.65)

        self.__controlFrame = ControlFrame(self,self.client)
        self.__controlFrame.place(relx= 0.01, rely=0.82,relwidth= 0.98,relheight = 0.15)

        
        self.protocol('WM_DELETE_WINDOW',self.__on_close)

    def handleEvents(self):
        '''
        Handles incoming signals from TCP clients
        
        Returns:
        None
        '''
        listenerThread= threading.Thread(target=self.__listener.start)
        listenerThread.start()
        print('BEGINING HANDLING OF EVENTS')
        while True:
            if self.TCPres.empty():
                pass
            else:

                msg = self.TCPres.get()
                print(f'MESSAGE RECIEVED:{msg}')
                header = msg[0]
                msg.remove(header)
                if header == '1-POINT-SCORED':
                    self.__tabView.updateScore(msg[0],1)
                elif header == '2-POINTS-SCORED':
                    self.__tabView.updateScore(msg[0],2)
                elif header == '3-POINTS-SCORED':
                    self.__tabView.updateScore(msg[0],3)
                elif header == 'AWAY-FOUL':
                    self.__tabView.addFoul('AWAY')
                elif header == 'HOME-FOUL':
                    self.__tabView.addFoul('HOME')
                elif header == 'STOP CLOCK':
                    self.__tabView.pauseClock()
                elif header == 'START CLOCK':
                    self.__tabView.clock.start_timer()
                elif header == 'SET CLOCK':
                    print(f'GUI: SETTING PERIOD {msg[0]}\nTIME {msg[1]}')
                    self.__tabView.setPeriod(msg[0])
                    self.__tabView.updateClock(int(msg[1])*60)
                elif header == 'HOME':
                    self.__tabView.updateScore('HOME',int(msg[0]))
                elif header == 'AWAY':
                    self.__tabView.updateScore('AWAY',int(msg[0]))
                elif header == 'TIME-OUT-HOME':
                    _ = timeOutWindow(team='HOME')
                elif header == 'TIME-OUT-AWAY':
                    _ = timeOutWindow(team='AWAY')
                
                
    def run_setup(self):
        '''
        Runs the setup window

        Returns:
        None
        '''
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = SetUpWindow(network_agent=self.client)
        else:
            self.toplevel_window.focus()
        self.__setup = True
        self.__start_btn.configure(state='normal')
    
    def __start(self):
        """
        Run the application.

        Returns:
        None
        """
        if self.__setup:
            self.client.send(['START GAME'])
        self.__start_btn.configure(state='disabled')
    def __on_close(self):
        """
        Handle the closing event of the application.

        Returns:
        None
        """
        self.client.send(['!DISCONNECT'])
        del(self.client)
        self.destroy()

if __name__ =='__main__':
    app = App()
    app.mainloop() 