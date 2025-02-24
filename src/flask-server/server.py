from flask import Flask, request
import cv2
import os

app = Flask(__name__)


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
       video_processor(path_to_file)

       #############################################################################################################
       #video.save()

       return video.filename 
    return "failure"

if __name__ == "__main__":

    app.run(debug=True)
