'''
File: vision_utils.py
Author: V. Stojkovic
Date: 2024-11-5
Description:
    This file contains utility functions for the vision module.
Methods:

'''
import cv2
import numpy as np
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

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

def draw_landmarks(image,results) -> None:
    '''
    Plot landmarks on the frame, takes image and results form mp_detection
    
    Parameters:
    - Image(numpy.ndarray): Numpy array containing the image
    - results(np.ndarray): Numpy array containing the results from mp_detection'''

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
    '''Extracts the keypoints from the results of mp_detection and returns them as a numpy array
    
    Parameters:
    - results(np.ndarray): Numpy array containing the results from mp_detection
    Returns:
    - keypoints(numpy.ndarray): Numpy array containing the keypoints'''
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*3)

    return np.concatenate([pose, lh, rh])

def motion_analysis(frame1:np.ndarray,frame2:np.ndarray,draw=False):
    '''Calculates the motion between two frames and returns the motion intensity and the new frame with rectangles drawn around the moving objects
    Parameters:
    - frame1(numpy.ndarray): Numpy array containing the first frame
    - frame2(numpy.ndarray): Numpy array containing the second frame
    - draw(bool): Whether to draw the rectangles around the moving objects
    Returns:
    - motion(numpy.ndarray): Numpy array containing the motion intensity
    - new_frame(numpy.ndarray): Numpy array containing the new frame with rectangles drawn around the moving objects'''

    # Convert the frames to grayscale
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