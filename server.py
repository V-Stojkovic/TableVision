import socket
import cv2
import numpy as np
import threading
import pickle
from queue import Queue
from PIL import Image
from customtkinter import CTkImage

class UDPserver:
    def __init__(self,port=5050,host='localhost',buffer=2048,result_queue:Queue|None = None) -> None:
        self.__BUFFER = buffer
        self.__port = port
        self.__host = host
        self.__socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.__result_queue = result_queue
        
    def send(self,msg:str):
        message = msg.encode('utf-8')
        self.__socket.sendto(message,(self.__host,self.__port))

    def run(self):
        self.__socket.bind((self.__host,self.__port))
        print('UDP SERVER RUNNING ON:{}'.format(self.__port))
        frame_data = b''
        count = 0
        while True:
            chunk,addr = self.__socket.recvfrom(self.__BUFFER)
            if chunk == b'__end_of_transmission__':
                #try to display the frame
                print('frame received')
                img_encoded = np.frombuffer(frame_data, dtype=np.uint8)
                img = cv2.imdecode(img_encoded, cv2.IMREAD_COLOR)
                if img is not None:
                    img_converted =  cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                    if self.__result_queue:
                        img = Image.fromarray(img_converted)
                        img = CTkImage(img,size=(800,600))
                        self.__result_queue.put(img)

                frame_data = b''
            else:
                frame_data += chunk
            

            
            
class TCPserver:
    HEADER = 64
    FORMAT = 'utf-8'
    DISCONNECT_MSG = '!DISCONNECT'

    def __init__(self,port,address,results:Queue|None=None) -> None:
        self.__address = (address,port)
        self.__server_adress = address
        self.__socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.__socket.bind(self.__address)
        self.result_queue = results

    def send(self,msg,conn,addr):
        '''sends message back to client'''
        data = pickle.dumps(msg)
        conn.sendall(data)

    def __handleClient(self,conn, addr):
        print(f'NEW CONNECTION ESTABLISHED WITH:{addr}')
        connected = True
        while connected:
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length)
                msg = pickle.loads(msg)
                if msg == self.DISCONNECT_MSG:
                    connected = False
                print(f'SYSTEM: MESSAGE RECIEVED FROM [{addr}]: {msg}')
                
                self.result_queue.put(msg)
                
        conn.close()

    def start(self):

        self.__socket.listen()
        print(f'SERVER: LISTENING ON:{self.__server_adress}')
        while True:
            conn,addr = self.__socket.accept()
            if self.result_queue is not None:
                thread = threading.Thread(target=self.__handleClient, args=(conn,addr))
                thread.start()
            else:
                thread = threading.Thread(target=self.__handleClient, args=(conn,addr))
                thread.start()
            print(f'NUMBER OF CONNECTIONS:{threading.active_count()-1}')
            

