'''
File: vision.py
Author: V. Stojkovic
Date: 2024-11-5
Description:
    This file contains the main code for the vision module.'''
# Standard library imports
import queue
import threading
import warnings

# Third-party imports
import cv2
import mediapipe as mp  # type: ignore
import numpy as np
from tensorflow import keras
from tensorflow.keras.layers import Dense, Dropout, LSTM  # type: ignore
from tensorflow.keras.models import Sequential  # type: ignore
from tensorflow.keras.optimizers.legacy import Adam  # type: ignore

# Local application imports
import client
import server
from vision_utils import draw_landmarks, extract_keypoints, motion_analysis, mp_detection




warnings.filterwarnings('ignore')

HEIGHT = 800
WIDTH = 600

actions = np.array(['3-points-scored','2-point','1-Point','Stop_for_foul','Stop_for_violation','Start_clock','point-left','point-right'])

def load_model(path_to_weights:str) -> Sequential:
    '''
    Creates the layers of the model and loads the weights from training
    
    Parameters:
    - path_to_weights(String): Path to the file where the weights are stored
    
    Returns:
    '''
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(40,258)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(actions.shape[0], activation='softmax'))
    optimizer = Adam(learning_rate=0.0001)
    model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    model.load_weights(path_to_weights)
    return model



# Initialize the cameras
try:
    cam1 = cv2.VideoCapture(0)
    cam2 = cv2.VideoCapture(1)
except Exception as e:
    print(f"Error initializing cameras: {e}")
    cam1 = None
    cam2 = None
if cam1 is None or cam2 is None:
    print("Error: One or both cameras could not be initialized.")
    exit(1)
# Set the resolution of the cameras
cam1.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cam1.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cam2.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cam2.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
# Set the frame rate of the cameras 

transmit = False
sequence1 = []
sequence2 = []
sentence1 = []
sentence2 = []
threshold = 0.5 # minimum confidence for signal

_,frame_a0 = cam1.read()
_,frame_b0 = cam2.read()
TCP_res = queue.Queue()
TCP_server = server.TCPserver(port=5002,address='localhost',results=TCP_res)
TCP_client = client.TCPclient(port=5006,server_address='localhost',client_id='Vision') #for TCP communication to the server
TCP_client.send('CLIENT: VISION CONNECTED')
UDP_agent = client.UDPclient(5050)# for UDP communication with GUI.py only
model = load_model('/Users/vukstojkovic/Documents/Project/Scripts/weights.best3.hdf5')
server_thread = threading.Thread(target=TCP_server.start)
server_thread.start()

while True:
    if TCP_res.empty(): 
        pass
    else:
        msg = TCP_res.get()
        print('VISION:MESSAGE RECIEVED',msg)
        if msg == 'SEND_FRAMES':
            transmit = True
        else:
            transmit = False

    print(transmit)
            
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        ret1,frame_a1 = cam1.read()
        ret2,frame_b1 = cam2.read()

        if transmit and ret1 and ret2 :
            #attempt to send frames to game.py
            send_frame_a1 = cv2.rotate(frame_a1,cv2.ROTATE_90_COUNTERCLOCKWISE)
            send_frame_b1 = cv2.rotate(frame_b1,cv2.ROTATE_90_COUNTERCLOCKWISE)
            UDP_agent.send_frame(send_frame_a1)
            UDP_agent.send_frame(send_frame_b1)

        motion1,img1 = motion_analysis(frame_a0,frame_a1)
        motion2,img2 = motion_analysis(frame_b0,frame_b1)

        results1,image1 = mp_detection(frame_a1, holistic)
        results2,image2 = mp_detection(frame_b1, holistic)
        
        draw_landmarks(image1,results1)
        draw_landmarks(image2,results2)

        img1 = cv2.rotate(image1,cv2.ROTATE_90_COUNTERCLOCKWISE)
        img2 = cv2.rotate(image2,cv2.ROTATE_90_COUNTERCLOCKWISE)

        landmarks1= extract_keypoints(results1)
        landmarks2= extract_keypoints(results2)
        
        sequence1.append(landmarks1)
        sequence2.append(landmarks2)
        sequence1 = sequence1[-40:]
        sequence2 = sequence2[-40:]

        if len(sequence1) == 40:
            res = model.predict(np.expand_dims(sequence1,axis=0))[0]

            if res[np.argmax(res)] > threshold and actions[np.argmax(res)] != 'Start_clock':
                if len(sentence1) >0:
                    if actions[np.argmax(res)] != sentence1[-1]:
                        sentence1.append(actions[np.argmax(res)])
                else:
                    sentence1.append(actions[np.argmax(res)])
                

            if len(sentence1) > 2:
                sentence1 = sentence1[-2:]
        try:
            cv2.rectangle(img1, (0,0), (800, 40), (245, 117, 16), -1)
            cv2.putText(img1, ' '.join(sentence2[-1]), (3,30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        except IndexError:
            cv2.rectangle(img1, (0,0), (800, 40), (245, 117, 16), -1)
            cv2.putText(img1,'NO SIGNAL', (3,30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        if len(sequence2) == 40:
            res = model.predict(np.expand_dims(sequence2,axis=0))[0]

            if res[np.argmax(res)] > threshold and actions[np.argmax(res)] != 'Start_clock':

                if len(sentence2) >0:
                    if actions[np.argmax(res)] != sentence2[-1]:
                        sentence2.append(actions[np.argmax(res)])
                else:
                    sentence2.append(actions[np.argmax(res)])
                

            if len(sentence2) > 2:
                sentence2 = sentence2[-2:]
        try:
            cv2.rectangle(img2, (0,0), (800, 40), (245, 117, 16), -1)
            cv2.putText(img2, ' '.join(sentence2[-1]), (3,30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        except IndexError:
            cv2.rectangle(img2, (0,0), (800, 40), (245, 117, 16), -1)
            cv2.putText(img2,'NO SIGNAL', (3,30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        if motion1 > motion2:
            cv2.rectangle(img1,(800,0),(1200,40),(0,255,0),-1)
            cv2.putText(img1,'MOTION PRIORITY',(800,10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        else:
            cv2.rectangle(img2,(800,0),(1200,40),(0,255,0),-1)
            cv2.putText(img2,'MOTION PRIORITY',(800,10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        frame_a0 = frame_a1
        frame_b0 = frame_b1

    if cv2.waitKey(10) & 0xff == ord('q'):
        break