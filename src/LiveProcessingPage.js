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

    const [processedFrame, setProcessedFrame] = useState(null);
    const [reps, setReps] = useState(0);
    const [sessionEnded, setSessionEnded] = useState(false);

    useEffect(() => {
        let isMounted = true;

        const initCamera = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                if (!isMounted) return;

                streamRef.current = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.play();
                }

                socket.on('play_sound', (data) => {
                    playSound(data.sound);
                });

                const canvas = canvasRef.current;
                const ctx = canvas.getContext('2d');

                const sendFrame = () => {
                    if (
                        !videoRef.current ||
                        videoRef.current.readyState !== 4 ||
                        sessionEnded
                    ) return;

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

        initCamera();

        // Close the connection and remove the video frame
        socket.off('processed_frame').on('processed_frame', (data) => {
            if (data.image === null) {
                setSessionEnded(true);
                setProcessedFrame(null);
                return;
            }
            setProcessedFrame(`data:image/jpeg;base64,${data.image}`);
            setReps(data.reps);
        });

        return () => {
            isMounted = false;
            if (intervalRef.current) clearInterval(intervalRef.current);
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, [sessionEnded]);

    const playSound = (sound) => {
        const audio = new Audio(`${sound}.mp3`);
        audio.play();
    };

    return (
        <div style={{ textAlign: 'center', marginTop: '60px' }}>
            <h2>Live Processing</h2>
            <p>
                1. Allow the Frailty Indicator Analysis Tool to access your webcam. <br/><br/>
                2. Get in the proper position for performing the sit-stand test. Ensure that you are not too close to the camera,
                and that your whole body is within frame.<br/><br/>
                3. Begin performing the test. The 30-second timer will start counting down automatically.<br/><br/>
            </p>
            <br/>
            <p><strong>Reps:</strong> {reps}</p>

            <video ref={videoRef} width="960" height="720" style={{ display: 'none' }} />
            <canvas ref={canvasRef} width="960" height="720" style={{ display: 'none' }} />

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
