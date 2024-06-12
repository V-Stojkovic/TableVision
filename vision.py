import cv2
import mediapipe as mp # type: ignore
import numpy as np 
import playsound

import warnings
import client
import server
from tensorflow import keras
from tensorflow.keras.models import Sequential #type: ignore
from tensorflow.keras.layers import LSTM, Dense, Dropout #type: ignore
from tensorflow.keras.optimizers.legacy import Adam # type:ignore
import threading
import queue
import logging




warnings.filterwarnings('ignore')
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
HEIGHT = 800
WIDTH = 600

cam1 = cv2.VideoCapture(0)
cam2 = cv2.VideoCapture(1)

actions = np.array(['3-points-scored','2-point','1-Point','Stop_for_foul','Stop_for_violation','Start_clock','point-left','point-right'])
def load_model(path_to_weights:str) -> Sequential():
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

def mp_detection(image:np.ndarray,model):
    '''takes an image and trained model and extracts features, returns results followed by image'''
    image = cv2.cvtColor(
        image, cv2.COLOR_BGR2RGB
        )
    image.flags.writeable = False
    results = model.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(
        image, cv2.COLOR_RGB2BGR
        )
    return results, image

def draw_landmarks(image,results):
    '''
    Plot landmarks on the frame, takes image and results form mp_detection
    
    Parameters:
    - Image(numpy.ndarray): Numpy array containing the image
    - results()'''
    mp_drawing.draw_landmarks(
        image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(26, 204, 16), thickness = 2, circle_radius =4),
        mp_drawing.DrawingSpec(color=(255,255,255), thickness=2, circle_radius=2)
    )
    mp_drawing.draw_landmarks(
        image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(26, 204, 16), thickness=2, circle_radius=4), 
        mp_drawing.DrawingSpec(color=(255,255,255), thickness=2, circle_radius=2)
    )
    mp_drawing.draw_landmarks(
        image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(80,22,10), thickness=2, circle_radius=4), 
        mp_drawing.DrawingSpec(color=(255,255,255), thickness=2, circle_radius=2)
    )
def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
    # face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468*3)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*3)
    return np.concatenate([pose, lh, rh])
def motion_analysis(frame1:np.ndarray,frame2:np.ndarray,draw=False):
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Calculate the absolute difference between the current and previous frame
    diff = cv2.absdiff(gray1, gray2)

    # Apply a threshold to highlight the regions with significant differences
    _, threshold = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # Find contours of the thresholded image
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Calculate the total area of motion
    total_motion_area = sum(cv2.contourArea(contour) for contour in contours if cv2.contourArea(contour) > 100)

    # Normalize the motion intensity between 0 and 1
    normalized_motion = min(total_motion_area / (frame2.shape[0] * frame2.shape[1]), 1.0)
    new_frame = frame2
    if draw:
        for contour in contours:
            if cv2.contourArea(contour) > 5000:  # Adjust the area threshold as needed
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(new_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return normalized_motion, new_frame
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
            print('VISION: TRYING TO SEND FRAMES')
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