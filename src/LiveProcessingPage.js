import React, { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';
import scores from './images/Sit-Stand-Scores.png';
import { Link } from "react-router-dom";

const socket = io('http://localhost:5000');
socket.io.opts.forceNew = true;

const LiveProcessingPage = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  // === State ===
  const [processedFrame, setProcessedFrame] = useState(null);
  const [reps, setReps] = useState(0);
  const [sessionEnded, setSessionEnded] = useState(false);
  const [initialInstructionGiven, setInitialInstructionGiven] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  // === Text-to-Speech Helper ===
  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.lang = 'en-US';
    speechSynthesis.speak(utterance);
  };

  // === 5→1 Spoken Countdown ===
  const performCountdown = async () => {
    for (let i = 5; i >= 1; i--) {
      speak(i.toString());
      await new Promise(res => setTimeout(res, 1000));
    }
  };

  // === useEffect for camera & socket logic ===
  useEffect(() => {
    let isMounted = true;

    // Start the camera & intervals
    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (!isMounted) return;

        // Save stream, attach to video element
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }

        // Prepare canvas for capturing frames
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        // Repeatedly grab frames and emit to server
        const sendFrame = () => {
          if (!videoRef.current || videoRef.current.readyState !== 4 || sessionEnded || !isRunning) return;

          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          canvas.toBlob((blob) => {
            const reader = new FileReader();
            reader.onloadend = () => {
              socket.emit('frame', reader.result);
            };
            reader.readAsDataURL(blob);
          }, 'image/jpeg');
        };

        intervalRef.current = setInterval(sendFrame, 100);
      } catch (err) {
        console.error("Error accessing webcam:", err);
      }
    };

    // Only init camera if user clicked 'Start'
    if (isRunning) {
      initCamera();

      // Speak initial instruction only once
      if (!initialInstructionGiven) {
        speak("Please get into a sitting position to begin the test.");
        setInitialInstructionGiven(true);
      }

      // Listen for processed frames from server
      socket.off('processed_frame').on('processed_frame', (data) => {
        if (data.image === null) {
          // Means server signaled test end
          setSessionEnded(true);
          setProcessedFrame(null);
          return;
        }
        setProcessedFrame(`data:image/jpeg;base64,${data.image}`);
        setReps(data.reps);
      });

      // Listen for voice instructions from server
      socket.off('voice_instruction').on('voice_instruction', async ({ type }) => {
        switch (type) {
          case 'start_countdown':
            speak("Sit position detected. Starting countdown");
            await performCountdown();
            socket.emit('countdown_finished');
            break;

          case 'sit_lost':
            speak("Position lost, enter the sitting position again");
            break;

          case 'start_test':
            // No speech for now;
            break;

          case 'final_countdown':
            // Reuse the same 5→1 countdown
            await performCountdown();
            break;

          case 'test_complete':
            speak("Test complete. The results are available now.");
            break;

          default:
            break;
        }
      });
    }

    // Cleanup on unmount or if isRunning changes
    return () => {
      isMounted = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      socket.off('processed_frame');
      socket.off('voice_instruction');
    };
  }, [sessionEnded, initialInstructionGiven, isRunning]);

  // === Handlers for Start & Cancel ===
  const handleStart = () => {
    setSessionEnded(false);
    setInitialInstructionGiven(false);
    setProcessedFrame(null);
    setReps(0);
    setIsRunning(true);
  };

  const handleCancel = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    socket.off('processed_frame');
    socket.off('voice_instruction');
    setIsRunning(false);
    setInitialInstructionGiven(false);
    setProcessedFrame(null);
    setReps(0);
  };

  // === UI ===
  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <h2>Live Processing</h2>
      {!isRunning ? (
        <>
          <p>
            1. Allow the Frailty Indicator Analysis Tool to access your webcam. <br/><br/>
            2. Get in the proper position for performing the sit-stand test. Ensure that you are not too close to the camera,
            and that your whole body is within frame.<br/><br/>
            3. Begin performing the test. The 30-second timer will start counting down automatically.<br/><br/>
          </p>
          <button onClick={handleStart}>Start Test</button>
        </>
      ) : (
        <>
          <p><strong>Reps:</strong> {reps}</p>
          <button onClick={handleCancel}>Cancel Test</button>
        </>
      )}

      {/* Hidden raw video & canvas used for capturing frames */}
      <video
        ref={videoRef}
        width="960"
        height="720"
        style={{ display: 'none' }}
      />
      <canvas
        ref={canvasRef}
        width="960"
        height="720"
        style={{ display: 'none' }}
      />

      {/* Display processed frames from the server */}
      {processedFrame && (
        <img
          src={processedFrame}
          alt="Processed Frame"
          style={{ width: '960px', height: '720px', border: '2px solid #333' }}
        />
      )}

      <br />
      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button>Back to Main</button>
        </Link>
      </div>
      <br />
      <img src={scores} alt="Below Average Scores Based on Age Group" />
    </div>
  );
};

export default LiveProcessingPage;
