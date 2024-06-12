import socket
import cv2
import numpy as np
import pickle
import time
'''This file contains network objects for inter-process communication for the project'''
class TCPclient:
    FORMAT = 'utf-8'
    HEADER = 64
    def __init__(self,server_address,port,client_id) -> None:
        self.__address = server_address
        self.__port = port
        self.__client_id = client_id
        self.__setup()
    
    def __setup(self):
        self.__socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.__socket.connect((self.__address,self.__port))
        
    def send(self,msg):
        message = pickle.dumps(msg)
        message_length = len(message)
        send_length = str(message_length).encode(self.FORMAT)
        send_length += b' ' *(self.HEADER - len(send_length))

        self.__socket.send(send_length)
        self.__socket.send(message)

        amount_received = 0
        amount_expected = len(message)
        # while amount_received < amount_expected:
        #     data = self.__socket.recv(1024)
        #     data = pickle.loads(data)
        #     amount_received += len(data)
        #     print('Received:',data)

    def close(self):
        self.__socket.close()
    

        
class UDPclient():
    TAIL = b'__end_of_transmission__'
    def __init__(self,port:int,server_host='localhost')-> None:
        
        self.__server_host = server_host
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__transmission_port = port
    
    def send_frame(self,frame:np.ndarray):
        _,img_encoded= cv2.imencode('.jpg',frame)
        data_whole = np.array(img_encoded).tobytes()
        chunk_size = 1024
        # split frame into chunks before sending
        for i in range(0,len(data_whole),chunk_size):
            chunk = data_whole[i:i+chunk_size]
            self.__socket.sendto(chunk, (self.__server_host,self.__transmission_port))
            time.sleep(0.001)
        self.__socket.sendto(self.TAIL,(self.__server_host,self.__transmission_port))#send tail message

