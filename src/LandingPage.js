import React from 'react';
import { Link } from 'react-router-dom';
import './App.css';

export default function LandingPage() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Frailty Indicator Analysis Tool</h1>
        <p>Welcome! This tool helps assess frailty by analyzing a sit-stand test.</p>
      </header>
      <section className="App-demo-video">
        <h2>How to Perform the Test</h2>
        <iframe
          width="700"
          height="350"
          src="https://www.youtube.com/embed/PzCTwkJVhWg"
          title="Demo Video"
          frameBorder="0"
          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </section>
      <section className="App-navigation">
        <h2>Get Started!</h2>
        <div className="nav-buttons">
          <Link to="/upload">
            <button>Upload a Video</button>
          </Link>
          <Link to="/record">
            <button>Record a Video</button>
          </Link>
          <Link to="/liveProcessing">
            <button>Live Processing</button>
          </Link>
          <Link to="/history">
            <button>View Previous Results</button>
          </Link>
        </div>
      </section>
    </div>
  );
}
