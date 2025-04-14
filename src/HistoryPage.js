import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function HistoryPage() {
  const [videoList, setVideoList] = useState([]);

  useEffect(() => {
    async function fetchVideos() {
      try {
        // This endpoint returns only original (non-processed) videos.
        const response = await fetch('http://127.0.0.1:5000/videos');
        const data = await response.json();
        setVideoList(data);
      } catch (error) {
        console.error('Error fetching videos:', error);
      }
    }
    fetchVideos();
  }, []);

  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <h2>Previous Results</h2>
      {videoList.length === 0 && <p>No uploaded videos found.</p>}

      <ul style={{ listStyle: 'none', padding: 0 }}>
        {videoList.map((originalFilename) => {
          // Build the processed filename by inserting "_processed" before file extension
          const dotIndex = originalFilename.lastIndexOf('.');
          let baseName = originalFilename;
          let ext = '';
          if (dotIndex !== -1) {
            baseName = originalFilename.substring(0, dotIndex);
            ext = originalFilename.substring(dotIndex);
          }
          // e.g. "myvideo_processed.mp4"
          const processedFilename = `${baseName}_processed${ext}`;

          return (
            <li key={originalFilename} style={{ marginBottom: '40px' }}>
              {/* Original video */}
              <p>Original: {originalFilename}</p>
              <video
                src={`http://127.0.0.1:5000/uploads/${originalFilename}`}
                width="400"
                controls
                style={{ marginRight: '20px' }}
              />

              {/* Processed (analyzed) video */}
              <p>Analyzed: {processedFilename}</p>
              <video
                src={`http://127.0.0.1:5000/uploads/${processedFilename}`}
                width="400"
                controls
                // If the processed file 404s, hide the <video> to avoid a broken player.
                onError={(e) => {
                  console.warn('Processed file not found:', processedFilename);
                  e.currentTarget.style.display = 'none';
                }}
              />
            </li>
          );
        })}
      </ul>

      <div style={{ marginTop: '30px' }}>
        <Link to="/">
          <button>Back to Main</button>
        </Link>
      </div>
    </div>
  );
}
