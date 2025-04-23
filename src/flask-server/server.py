from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import os
import cv2
import numpy as np
import mediapipe as mp
import time
from datetime import date

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --------------------------------------------------------------------------------
# Mediapipe initialization:
#   We use static_image_mode=True for real-time frames to avoid timestamp mismatch.
#   This doesn't affect the offline 'sit_stand_processor' approach for /analyze.
# --------------------------------------------------------------------------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    static_image_mode=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Folder setup
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --------------------------------------------------------------------------------
# STATE for LIVE processing
# (Upload/Record uses 'sit_stand_processor()', does not rely on these states)
# --------------------------------------------------------------------------------
stage = None
counter = 0
timer_start = False # True or false for timer start. 
start_time = None
multiplier = 1 # Multiplier for fps
sit_detected_time = None # When sit is deteced for voice logic
countdown_in_progress = False # Countdown boolean for voice logic 
in_test_phase = False # This is a state for voice logic 
last_good_sit_time = None # This needs to exist for a buffer (in case a person shifts slighly)

# --------------------------------------------------------------------------------
# UTILS
#  calculate_angle - Calculates angle between Left or right knee (a), left or right hip(b), and 
#   left or right ankle(c).
#  reset_state - Resets states for LiveProcessing 
# --------------------------------------------------------------------------------
def calculate_angle(a, b, c):
    """Utility to calculate joint angle between three points."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle

def reset_state():
    """Reset global state for a fresh live session."""
    global stage, counter, timer_start, start_time, multiplier
    global sit_detected_time, countdown_in_progress, in_test_phase
    stage = None
    counter = 0
    timer_start = False
    start_time = None
    multiplier = 1
    sit_detected_time = None
    countdown_in_progress = False
    in_test_phase = False
    last_good_sit_time = None

# --------------------------------------------------------------------------------
# SIT-STAND PROCESSOR (OFFLINE/BATCH) for /analyze or /live_analyze
#   - Processes a video from disk or webcam, writes output with overlay,
#     returns final repetition count.  NO VOICE LOGIC HERE.
# --------------------------------------------------------------------------------
def sit_stand_processor(input_path, output_path, live_or_upload):
    """
    Reads `input_path`, analyzes each frame for sit-stand,
    draws overlays, writes annotated frames to `output_path`.
    Returns final repetition count.

    `live_or_upload` is a string:
       - 'live' if reading from camera device (0)
       - 'upload' if a user-uploaded video file
    """
    cap = cv2.VideoCapture(input_path)  # int(0) for live, file path for upload
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    fps_in = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = 0
    frames_with_landmarks = 0


    # If the original video's FPS is invalid, fallback to 30
    if fps_in <= 0:
        fps_in = 30

    out = cv2.VideoWriter(output_path, fourcc, fps_in, (width, height))

    # Local counters for offline analysis
    local_counter = 0
    local_stage = None
    local_timer_start = False
    local_start_time = None

    fps_start_time = time.time()
    frames = 0
    local_multiplier = 1

    with mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as local_pose:

        while True:
            ret, frame = cap.read()
            if not ret:
                local_timer_start = False
                break

            # If analyzing an uploaded video (not truly live),
            # we do a rough fps-based multiplier to simulate 30s counting
            if live_or_upload == "upload":
                frames += 1
                fps_current_time = time.time()
                fps_val = frames / (fps_current_time - fps_start_time)
                local_multiplier = fps_val / 30

            # Recolor
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb.flags.writeable = False

            results = local_pose.process(frame_rgb)

            frame_rgb.flags.writeable = True
            annotated = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark
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

                lAngle = calculate_angle(lHip, lKnee, lAnkle)
                rAngle = calculate_angle(rHip, rKnee, rAnkle)

                # Show rep count (near left hip right now)
                cv2.putText(
                    annotated,
                    f'Count: {local_counter}',
                    (width - 220, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 255, 255), 
                    2
                )

                # Sit-stand logic
                if lAngle <= 145 and rAngle <= 145:
                    local_stage = "sit"
                    if not local_timer_start:
                        local_timer_start = True
                        local_start_time = time.time()

                if lAngle >= 170 and rAngle >= 170 and local_stage == "sit":
                    local_stage = "stand"
                    local_counter += 1

                # 30s countdown from the moment we detect first sit
                if local_timer_start:
                    elapsed = int(30 - (time.time() - local_start_time) * local_multiplier)
                    cv2.putText(
                        annotated,
                        f"Time: {elapsed}s",
                        (width - 220, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, 
                        (255, 255, 255), 
                        2
                    )
                    if elapsed <= 0:
                        break

            except Exception:
                pass

            # Draw landmarks
            if results.pose_landmarks:
                frames_with_landmarks += 1
                mp_drawing.draw_landmarks(
                    annotated,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(thickness=2, circle_radius=2)
                )

            cv2.imshow('Frailty Analysis', annotated)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

            out.write(annotated)

        cap.release()
        out.release()
        cv2.destroyAllWindows()

    return local_counter, frames, frames_with_landmarks


# --------------------------------------------------------------------------------
# FLASK ROUTES
# --------------------------------------------------------------------------------
@app.route('/videos', methods=['GET'])
def list_videos():
    all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    videos = [f for f in all_files if f.lower().endswith(video_extensions) and '_processed' not in f]
    return jsonify(videos), 200

@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/analyze', methods=['POST'])
def analyze_sit_stand():
    """
    1) Receives 'video' form-data from upload.
    2) Saves original video.
    3) Processes it with 'sit_stand_processor' (offline).
    4) Saves processed video with '_processed'.
    5) Returns JSON with the result.
    """
    
    if landmark_frames == 0:
        return warning
    
    if 'video' not in request.files:
        return "No video file part in the request", 400

    video = request.files['video']
    if video.filename == '':
        return "No selected video file", 400

    filename = video.filename
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(original_path)

    name, ext = os.path.splitext(filename)
    processed_filename = f"{name}_processed{ext}"
    processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)

    # run offline analysis
    reps, total_frames, landmark_frames = sit_stand_processor(original_path, processed_path, "upload")
    warning = "Pose detected, all good!"
    if landmark_frames == 0:
        warning = "No pose detected in any frame. Please try again with better camera positioning or lighting."

    

    return jsonify({
        "success": "Analysis Complete!",
        "original": "Original: " + filename,
        "processed": "Processed: " + processed_filename,
        "reps": "Reps: " + str(reps),
        "warning": warning
    }), 200

@app.route('/live_analyze')
def live_analyze_sit_stand():
    """
    Uses 'sit_stand_processor' with input_path=0
    to capture from webcam, writes annotated frames to disk, returns results.
    This is an alternative to the real-time socket approach,
    used by the 'RecordPage' if desired.
    """
    name = "live_video_" + str(date.today()) + "_" + str(int(time.time()))
    ext = ".mp4"
    processed_filename = f"{name}_processed{ext}"
    processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)

    reps = sit_stand_processor(0, processed_path, "live")

    return jsonify({
        "success": "Live Analysis Complete!",
        "original": "Original: webcam recording",
        "processed": "Processed: " + processed_filename,
        "reps": "Reps: " + str(reps)
    }), 200

# --------------------------------------------------------------------------------
# LIVE PROCESSING VIA SOCKETS
# --------------------------------------------------------------------------------
@socketio.on('connect')
def handle_connect():
    reset_state()

@socketio.on('countdown_finished')
def handle_countdown_finished():
    global timer_start, start_time, in_test_phase
    if not timer_start and not in_test_phase:
        timer_start = True
        start_time = time.time()
        in_test_phase = True
        # e.g., instruct start
        socketio.emit('voice_instruction', {'type': 'start_test'})

def process_frame(image):
    """
    Real-time (static_image_mode) posture detection for the live feed.
    """
    global stage, counter, timer_start, start_time, multiplier
    global sit_detected_time, countdown_in_progress, in_test_phase, last_good_sit_time

    # Convert to RGB for Mediapipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if not results.pose_landmarks:
        # Return the unmodified frame
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8'), counter, None

    landmarks = results.pose_landmarks.landmark

    # Check hips are visible
    if not (landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].visibility > 0.75 or
            landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].visibility > 0.75):
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8'), counter, None

    # Extract keypoints
    lShoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
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

    height, width, _ = image.shape

    # Angles
    lAngle = calculate_angle(lHip, lKnee, lAnkle)
    rAngle = calculate_angle(rHip, rKnee, rAnkle)

    # Draw repetition count near left shoulder
    cv2.putText(
        image,
        f'Count: {counter}',
        (int(lShoulder[0] * width), max(0, int(lShoulder[1]*height - 20))),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    events = []

    # If test hasn't begun, detect a stable sit
    if not in_test_phase:
        if lAngle <= 155 and rAngle <= 155:
            # Valid sit position is detected.
            if sit_detected_time is None:
                sit_detected_time = time.time()
                last_good_sit_time = time.time()
                events.append("sit_detected")
            else:
                # Update the last time we saw a good sit position
                last_good_sit_time = time.time()
            # Once a full 5 seconds of sustained sit, start countdown if not already started.
            if not countdown_in_progress and (time.time() - sit_detected_time > 3):
                countdown_in_progress = True
                events.append("start_countdown")
        else:
            # Posture not in a proper sit.
            if countdown_in_progress:
                # If we're in a countdown, allow a 1-second grace period
                if last_good_sit_time is not None and (time.time() - last_good_sit_time > 0.5):
                    sit_detected_time = None
                    countdown_in_progress = False
                    events.append("sit_lost")
            else:
                if sit_detected_time is not None:
                    sit_detected_time = None
                    events.append("sit_lost")

    # If test started, do the usual 30s countdown logic
    if timer_start and in_test_phase:
        elapsed = int(30 - (time.time() - start_time) * multiplier)
        cv2.putText(
            image,
            f'Time: {elapsed}s',
            (int(lShoulder[0]*width), int(lShoulder[1]*height + 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # Track the sit→stand transitions
        global stage
        if lAngle >= 165 and rAngle >= 165 and stage == "sit":
            stage = "stand"
            counter += 1
        elif lAngle <= 155 and rAngle <= 155:
            stage = "sit"

        if elapsed <= 5:
            events.append("final_countdown")
        if elapsed <= 0:
            final_count = counter
            reset_state()
            events.append("test_complete")
            return None, final_count, events

    # Draw pose
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(thickness=2, circle_radius=2),
        mp_drawing.DrawingSpec(thickness=2, circle_radius=2)
    )

    # Encode final annotated frame
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8'), counter, events

@socketio.on('frame')
def handle_frame(data):
    """Handles each incoming frame from the live page via SocketIO."""
    if data.startswith('data:image/jpeg;base64,'):
        data = data.replace('data:image/jpeg;base64,', '')
    frame = base64.b64decode(data)
    np_img = np.frombuffer(frame, dtype=np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    processed_frame, reps, events = process_frame(image)

    # Send processed frame to client
    emit('processed_frame', {
        'image': processed_frame,
        'reps': reps
    })

    if events:
        for event in events:
            socketio.emit('voice_instruction', {'type': event})

# --------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
