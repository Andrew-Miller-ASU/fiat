from flask import Flask, request
import cv2
import os
import time
import mediapipe as mp
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


app = Flask(__name__)

def calculate_angle(a, b, c):

    a = np.array(a) #First
    b = np.array(b) #Second
    c = np.array(c) #Third

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians*180 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


def sit_stand_processor(video_path, live_or_upload):
    #VIDEO FEED
    cap = cv2.VideoCapture(video_path)

    #sit-stand counter
    counter = 0
    stage = None

    #timer
    timer_start = False
    current_time = time.time()
    
    fps_start_time = time.time()
    
    frames = 0
    

    #Setup mediapipe instance
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                time.sleep(5)
                timer_start = False
                break  # End of video

            frames += 1
            fps_current_time = time.time()
            fps = frames / (fps_current_time - fps_start_time)
            multiplier = 1

            if live_or_upload == "upload":
                multiplier = fps / 30

            #detect stuff and render

            #recolor image to RBG
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            #make detections
            results = pose.process(image)
            #recolor image to BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            #extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark

                #get coordinates
                lShoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                lHip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                rHip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                lKnee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                rKnee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                lAnkle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                rAnkle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

                #calculate angle
                lAngle = calculate_angle(lHip, lKnee, lAnkle)
                rAngle = calculate_angle(rHip, rKnee, rAnkle)

                #visualize
                

                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                #Left hip
                cv2.putText(image, str(lAngle),
                            tuple(np.multiply(lKnee, [width, height]).astype(int)),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                #Right Hip
                #cv2.putText(image, str(rAngle),
                 #           tuple(np.multiply(rKnee, [width, height]).astype(int)),
                  #                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                  #counter text near shoulder
                counter_text = "Count: " + str(counter)
                cv2.putText(image, counter_text,
                            tuple(np.multiply(lShoulder, [width * 1.2, height]).astype(int)),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                #sit-stand counter logic
                if lAngle <= 150 and rAngle <= 150:
                    stage = "sit"
                if lAngle >= 175 and rAngle >= 175 and stage=="sit":
                    stage = "stand"
                    counter += 1
                if stage == "sit" and timer_start == False: 
                    timer_start = True
                    current_time = time.time()

                if timer_start:
                    timer_text = "Time: " + str(int(30 - (time.time() - current_time) * multiplier))
                    cv2.putText(image, timer_text,
                            tuple(np.multiply(lShoulder, [width * 1.2, height * 1.2]).astype(int)),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                
                    if (time.time() - current_time) * multiplier >= 30:

                        time.sleep(5)
                        timer_start = False
                        break

            except:
                pass

            #render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                                      mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2))

            

            cv2.imshow('Mediapipe Feed', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    return counter

def video_processor(video_path):

    # Initialize the HOG person detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # Open the video file
    
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Resize the frame (optional, but can improve performance)
        frame = cv2.resize(frame, (640, 480))

        # Detect people in the frame
        boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8), padding=(32, 32), scale=1.05)

        # Draw bounding boxes around detected people
        for (x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the resulting frame
        cv2.imshow('Video with People Detection', frame)

        # Check for 'q' key press to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close all windows
    cap.release()
    cv2.destroyAllWindows()






@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return "No video file part in the request", 400
     
    video = request.files['video']
    
    if video.filename == '':
        return "No selected video file", 400
    
    if video: 
          
       # process the file object here! 
       #############################################################################################################

       UPLOAD_FOLDER = 'uploads'
       os.makedirs(UPLOAD_FOLDER, exist_ok=True)
       app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

       filename = video.filename
       video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
       path_to_file = "uploads/" + filename
       #video_processor(path_to_file)
       reps = sit_stand_processor(path_to_file, "upload")
       #reps = sit_stand_processor(0)

       #############################################################################################################
       
       return_message = "Reps: " + str(reps)
       return return_message #video.filename #reps 
    return "failure"

@app.route('/live_record')
def live_record():

    reps = sit_stand_processor(0, "live")

    return_message = "Reps: " + str(reps)

    return return_message

if __name__ == "__main__":

    app.run(debug=True)
