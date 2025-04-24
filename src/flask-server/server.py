from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import os
import cv2
import numpy as np
import mediapipe as mp
import time
from mediapipe.framework.formats import landmark_pb2

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# State variables
last_stage = None
current_stage = None
counter = 0
timer_start = False
start_time = None
multiplier = 1
begin_test = False

def calculate_angle(a, b, c):
    """Utility to calculate joint angle between three points."""
    a = np.array(a)  # First
    b = np.array(b)  # Mid
    c = np.array(c)  # Last

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle

def calculate_distance(a, b):
    a = np.array(a)
    b = np.array(b)

    distance = np.sqrt((b[1] - a[1])**2 + (b[0] - a[0])**2)

    return distance * 1000  #distance is a small number <1. multiply by 1000 for easier management

def sit_stand_processor(input_path, output_path, live_or_upload):
    """
    Reads `input_path`, analyzes each frame for sit-stand,
    draws overlays, writes annotated frames to `output_path`.
    Returns final repetition count.
    Important note: live_or_upload should be a string, live for live recordings and
    upload for uploaded video. This is how the function will know whether to adjust for
    frame rate or not. Adjustment is unnecessary for live videos.
    """
    cap = cv2.VideoCapture(input_path)      # This will be an int 0 for live processing and a filepath for uploaded videos.

    # Prepare output video writer
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    fps_in = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # If the original video's FPS is 0 or None, fallback to 30
    if fps_in <= 0:
        fps_in = 30

    out = cv2.VideoWriter(output_path, fourcc, fps_in, (width, height))

    counter = 0
    stage = None
    timer_start = False
    start_time = None
    begin_test = False

    fps_start_time = time.time()
    sitting_timer = time.time()

    frames = 0
    multiplier = 1

    with mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:

        while True:
            ret, frame = cap.read()
            if not ret:
                timer_start = False
                break




            if live_or_upload == "upload":          # We only need to adjust for processing speed if we are processing an uploaded
                                                    # video.
                begin_test = True
                frames += 1                     # Calculate frame rate to adjust timer for the processing speed
                fps_current_time = time.time()
                fps = frames / (fps_current_time - fps_start_time)

                multiplier = fps / 30

            # Recolor image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Pose detection
            results = pose.process(image)

            # Recolor back to BGR (for drawing)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Extract landmark data
            try:
                landmarks = results.pose_landmarks.landmark

                lShoulder = [
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
                ]
                lHip = [
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
                ]
                rHip = [
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y
                ]
                lKnee = [
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
                ]
                rKnee = [
                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y
                ]
                lAnkle = [
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
                ]
                rAnkle = [
                    landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y
                ]

                # Calculate angles
                lAngle = calculate_angle(lHip, lKnee, lAnkle)
                rAngle = calculate_angle(rHip, rKnee, rAnkle)

                """ Visualization: put the left knee angle as text
                cv2.putText(
                    image,
                    f'{int(lAngle)}',
                    tuple(np.multiply(lKnee, [width, height]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                )
                    """
                # Show rep count near left shoulder
                counter_text = f"Count: {counter}"
                cv2.putText(
                    image,
                    counter_text,
                    (int(lShoulder[0]*width), max(0, int(lShoulder[1]*height - 20))),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                )

                if not begin_test:



                    if (lAngle <= 145 or rAngle <= 145):

                        if stage != "sit":
                            stage = "sit"
                            sitting_timer = time.time()
                        elif (time.time() - sitting_timer >= 3):
                            begin_test = True
                    else:
                        stage = None
                        sitting_timer = time.time()



                # Sit-stand logic
                if (lAngle <= 150 or rAngle <= 150) and begin_test:
                    stage = "sit"
                    # Start the timer if we haven't yet
                    if not timer_start:
                        timer_start = True
                        start_time = time.time()

                if (lAngle >= 170 or rAngle >= 170) and stage == "sit" and begin_test:
                    stage = "stand"
                    counter += 1

                # If we have been in the "sit" stage for more than 30s, break out
                if timer_start:
                    elapsed = int(30 - (time.time() - start_time) * multiplier)     # Count down from 30 as an int.
                                                                                    # Multiplier is our frame rate / 30
                                                                                    # for the 30 seconds we want to process.
                                                                                    # Multiplier is 1 when we are live processing
                    # Render a timer
                    cv2.putText(
                        image,
                        f"Time: {elapsed}s, Stage: {stage}, Begin_test: {begin_test}",
                        (int(lShoulder[0]*width), int(lShoulder[1]*height + 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                    )
                    if elapsed <= 0:            # Stop after 30 seconds, aka when the timer counts from 30 to 0.
                        # We can stop analysis here if desired
                        time.sleep(3)
                        break

            except:
                pass

            # Draw pose landmarks on the frame
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(thickness=2, circle_radius=2)
                )

            cv2.imshow('Frailty Indicator Analysis Tool', image)        # Show the video or live processing

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

            # Write the annotated frame to output
            out.write(image)

        cap.release()
        out.release()
        cv2.destroyAllWindows()         # This is needed to ensure the program terminates all unused processing windows.
                                        # Without this, you'll have an error that causes the server to be unable to process
                                        # videos sequentually.

    return counter

def process_frame(image):
    """During live processing, this function will be called once for every input frame recorded on the front-end. It handles
    tracking of the test stage (sit or stand), timer, and repetition count using global state variables. It returns the analyzed
    frame as output."""

    global last_stage, current_stage, counter, timer_start, start_time, multiplier, begin_test, sitting_timer

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if not results.pose_landmarks:
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8'), counter

    landmarks = results.pose_landmarks.landmark

    # Return the frame without incrementing the counter if neither the left nor right hip are in view
    # Ensures a repetition is not erroneously counted when only a user's upper body is visible
    #if not (landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].visibility > 0.75 or landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].visibility > 0.75):
    #    _, buffer = cv2.imencode('.jpg', image)
    #    return base64.b64encode(buffer).decode('utf-8'), counter


    lShoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
    rShoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                 landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
    lHip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
    rHip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
            landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
    lKnee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
             landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
    rKnee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
             landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
    lAnkle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
              landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
    rAnkle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
              landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
    lElbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
              landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
    rElbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
              landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
    lWrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
              landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
    rWrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
              landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

    height, width, _ = image.shape

    lHipAngle = calculate_angle(lShoulder, lHip, lKnee)
    rHipAngle = calculate_angle(rShoulder, rHip, rKnee)
    #lElbowAngle = calculate_angle(lShoulder, lElbow, lWrist)
    #rElbowAngle = calculate_angle(rShoulder, rElbow, rWrist)
    distance1 = calculate_distance(lWrist, rShoulder)
    distance2 = calculate_distance(rWrist, lShoulder)
    hipVisible = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].visibility > 0.75 or landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].visibility > 0.75

    cv2.putText(image, f'Count: {counter}, Stage: {current_stage}, Begin_test: {begin_test}', (int(lShoulder[0]*width), max(0, int(lShoulder[1]*height - 20))),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    """ Visualization: put the left knee angle as text
                cv2.putText(
                    image,
                    f'{int(lAngle)}',
                    tuple(np.multiply(lKnee, [width, height]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                )
                    """
    """ cv2.putText(
                    image,
                    f'{int(distance1)}',
                    tuple(np.multiply(lElbow, [width, height]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                )
    """
    if begin_test:

        # Start the timer if we haven't yet
        if not timer_start:
            timer_start = True
            start_time = time.time()

        # Detection of sit stage
        if (lHipAngle <= 150 or rHipAngle <= 150):
            last_stage = current_stage
            current_stage = "sit"

        # Detection of stand stage
        if (lHipAngle >= 170 or rHipAngle >= 170):
            last_stage = current_stage
            current_stage = "stand"

        # Detection of repetition completion (transition from sit to stand stage)
        if last_stage == "sit" and current_stage == "stand":
            last_stage = "stand"
            current_stage = None    # Reset current_stage so that a repetition is never counted twice (user must return to the sitting stage before the above condition can be triggered again)
            counter += 1
            emit('play_sound', {'sound': 'rep_counted'}, broadcast=True)

    else: # If the test has not started yet, check conditions to see if it should be started
        # Sit detection
        if hipVisible and (lHipAngle <= 150 or rHipAngle <= 150):
                current_stage = "sit"

                # Check if the user's arms are crossed with hands touching the shoulders
                if distance1 <= 150 and distance2 <= 150:
                    emit('play_sound', {'sound': 'countdown'}, broadcast=True)  # Play 3-second countdown and "test started" notification
                    begin_test = True                                           # Start the test

    if timer_start:
        time_remaining = int(30 - (time.time() - start_time) * multiplier)

        # Display the value of the timer on the screen
        cv2.putText(image, f'Time: {time_remaining}s',
                    (int(lShoulder[0]*width), int(lShoulder[1]*height + 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if time_remaining <= 0:
            return None, counter

    # Pose landmarks that will be shown on the output frame
    pose_landmarks_to_show = [
        # Exclude all landmarks above the shoulder
        lmk if idx >= mp_pose.PoseLandmark.LEFT_SHOULDER.value else None
        for idx, lmk in enumerate(results.pose_landmarks.landmark)
    ]

    filtered_landmarks = landmark_pb2.NormalizedLandmarkList(
        landmark=[
            lmk if lmk is not None else landmark_pb2.NormalizedLandmark()
            for lmk in pose_landmarks_to_show
        ]
    )

    # Pose connections that will be shown on the output frame
    pose_connections_to_show = [
        conn for conn in mp_pose.POSE_CONNECTIONS
        # Exclude all connections above the shoulder
        if conn[0] >= mp_pose.PoseLandmark.LEFT_SHOULDER.value and conn[1] >= mp_pose.PoseLandmark.LEFT_SHOULDER.value
    ]

    mp_drawing.draw_landmarks(
        image,
        filtered_landmarks,
        pose_connections_to_show,
        mp_drawing.DrawingSpec(thickness=2, circle_radius=2),
        mp_drawing.DrawingSpec(thickness=2, circle_radius=2)
    )

    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8'), counter

@app.route('/videos', methods=['GET'])
def list_videos():

    all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    videos = [f for f in all_files if f.lower().endswith(video_extensions) and '_processed' not in f]
    return jsonify(videos), 200

@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_video(filename):
    """Serve any video from the uploads folder."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/analyze', methods=['POST'])
def analyze_sit_stand():
    """
    Single endpoint that:
      1) Receives file from 'video' form-data.
      2) Saves original video.
      3) Performs the Mediapipe analysis headlessly.
      4) Saves processed video with "_processed" appended.
      5) Returns JSON: { original: "...", processed: "...", reps: N }
    """
    if 'video' not in request.files:
        return "No video file part in the request", 400

    video = request.files['video']
    if video.filename == '':
        return "No selected video file", 400

    filename = video.filename
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(original_path)

    # Build output filename
    # e.g. myvideo.mp4 => myvideo_processed.mp4
    name, ext = os.path.splitext(filename)
    processed_filename = f"{name}_processed{ext}"
    processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)

    # Run analysis
    reps = sit_stand_processor(original_path, processed_path, "upload")

    return jsonify({
        "success": "Analysis Complete!",
        "original": "Original: " + filename,
        "processed": "Processed: " + processed_filename,
        "reps": "Reps: " + str(reps)
    }), 200


@app.route('/live_analyze')
def live_analyze_sit_stand():
    """
    Single endpoint that:
      1) Prepares a video filename using the date and time for a live processing.
      2) Performs the Mediapipe analysis headlessly.
      3) Saves processed video with "_processed" appended.
      4) Returns JSON: { original: "...", processed: "...", reps: N }
    """


    # Build output filename
    # e.g. myvideo.mp4 => myvideo_processed.mp4
    name = "live_video_" + str(date.today()) + "_" + str(int(time.time()))
    ext = ".mp4"
    processed_filename = f"{name}_processed{ext}"
    processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)

    # Run analysis
    reps = sit_stand_processor(0, processed_path, "live")

    return jsonify({
        "success": "Live Analysis Complete!",
        "original": "Original: webcam recording",
        "processed": "Processed: " + processed_filename,
        "reps": "Reps: " + str(reps)
    }), 200

@socketio.on('connect')
def handle_connect():
    global last_stage, current_stage, counter, timer_start, start_time, multiplier, begin_test, sitting_timer
    last_stage = None
    current_stage = None
    counter = 0
    timer_start = False
    start_time = None
    multiplier = 1
    begin_test = False
    sitting_timer = None

@socketio.on('frame')
def handle_frame(data):
    if data.startswith('data:image/jpeg;base64,'):
        data = data.replace('data:image/jpeg;base64,', '')
    frame = base64.b64decode(data)
    np_img = np.frombuffer(frame, dtype=np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    processed_frame, reps = process_frame(image)

    emit('processed_frame', {
        'image': processed_frame,
        'reps': reps
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)