import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {
  const [lectures, setLectures] = useState({});
  const [selectedLecture, setSelectedLecture] = useState("");
  const [videoId, setVideoId] = useState("");

  // Quiz
  const [quiz, setQuiz] = useState([]);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  // Notes
  const [notes, setNotes] = useState("");
  const [loadingNotes, setLoadingNotes] = useState(false);

  // Video + transcript
  const [watchedSeconds, setWatchedSeconds] = useState(0);
  const [transcriptTimeline, setTranscriptTimeline] = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);

  // Chatbot
  const [userQuestion, setUserQuestion] = useState("");
  const [botAnswer, setBotAnswer] = useState("");
  const [botLoading, setBotLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  // Quiz window
  const [quizOpen, setQuizOpen] = useState(false);
  const [quizMaximized, setQuizMaximized] = useState(false);
  const [quizPosition, setQuizPosition] = useState({ x: 24, y: 24 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const quizRef = useRef(null);
  const playerRef = useRef(null);
  const timerRef = useRef(null);
  const transcriptRef = useRef(null);

  // ================= LOAD LECTURES =================
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/lectures/")
      .then(res => res.json())
      .then(setLectures);
  }, []);

  // ================= YOUTUBE API =================
  useEffect(() => {
    if (window.YT) return;
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.body.appendChild(tag);
  }, []);

  const initPlayer = (id) => {
    if (playerRef.current) playerRef.current.destroy();
    playerRef.current = new window.YT.Player("yt-player", {
      videoId: id,
      events: { onStateChange },
    });
  };

  const onStateChange = (event) => {
    if (event.data === window.YT.PlayerState.PLAYING) {
      clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        const currentTime = playerRef.current.getCurrentTime();
        setWatchedSeconds(Math.floor(currentTime));

        // Auto-scroll to active line
        if (autoScroll && transcriptRef.current && transcriptTimeline.length > 0) {
          const activeIndex = transcriptTimeline.findIndex(
            (seg) => currentTime >= seg.start && currentTime < seg.end
          );
          
          if (activeIndex >= 0) {
            const activeElement = transcriptRef.current.querySelector(
              `[data-segment-index="${activeIndex}"]`
            );
            if (activeElement) {
              activeElement.scrollIntoView({ 
                behavior: "smooth", 
                block: "center" 
              });
            }
          }
        }
      }, 300); // Update every 300ms for smooth highlighting
    } else {
      clearInterval(timerRef.current);
    }
  };

  // ================= LOAD LECTURE =================
  const loadLecture = async () => {
    if (!selectedLecture) return;

    // Reset everything
    setQuiz([]);
    setNotes("");
    setBotAnswer("");
    setUserQuestion("");
    setAnswers({});
    setCurrent(0);
    setSubmitted(false);
    setWatchedSeconds(0);
    setTranscriptTimeline([]);

    const res = await fetch(
      "http://127.0.0.1:8000/api/submit-video/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lecture_id: selectedLecture }),
      }
    );

    const data = await res.json();

    if (data.video_id) {
      setVideoId(data.video_id);
      initPlayer(data.video_id);

      // Load transcript with timeline
      fetch(`http://127.0.0.1:8000/api/transcript/${data.video_id}/`)
        .then(r => r.json())
        .then(d => {
          console.log("Transcript data:", d); // Debug
          if (d.timeline && d.timeline.length > 0) {
            setTranscriptTimeline(d.timeline);
          } else if (d.full_text) {
            // Fallback: create fake timeline from full text
            const sentences = d.full_text.split('. ');
            const fakeTimeline = sentences.map((text, i) => ({
              start: i * 5,
              end: (i + 1) * 5,
              text: text + '.'
            }));
            setTranscriptTimeline(fakeTimeline);
          }
        });
    }
  };

  // ================= QUIZ =================
  const generateQuiz = async () => {
    if (!videoId) return;

    setQuiz([]);
    setAnswers({});
    setCurrent(0);
    setSubmitted(false);

    const res = await fetch(
      "http://127.0.0.1:8000/api/generate-quiz/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          watched_seconds: watchedSeconds,
        }),
      }
    );

    const data = await res.json();
    if (data.status === "success") {
      setQuiz(data.quiz);
      setQuizOpen(true);
    }
  };

  // ================= NOTES =================
  const generateNotes = async (mode) => {
    if (!videoId) return;

    setLoadingNotes(true);
    setNotes("");

    const res = await fetch(
      "http://127.0.0.1:8000/api/generate-notes/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          watched_seconds: watchedSeconds,
          mode: mode,
        }),
      }
    );

    const data = await res.json();

    if (data.status === "success") {
      setNotes(data.notes);
    } else {
      setNotes("❌ Failed to generate notes");
    }

    setLoadingNotes(false);
  };

  // ================= CHATBOT =================
  const askBot = async () => {
    if (!userQuestion || !videoId) return;

    setBotLoading(true);
    setBotAnswer("");

    const res = await fetch("http://127.0.0.1:8000/api/chatbot/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_id: videoId,
        question: userQuestion,
      }),
    });

    const data = await res.json();
    setBotAnswer(data.answer || "❌ No response");
    setBotLoading(false);
  };

  // ================= QUIZ LOGIC =================
  const selectOption = (idx) => {
    if (submitted) return;
    setAnswers(prev => ({ ...prev, [current]: idx }));
  };

  const submitAnswer = () => {
    if (answers[current] === undefined) return;
    setSubmitted(true);
  };

  const nextQuestion = () => {
    setSubmitted(false);
    setCurrent(prev => prev + 1);
  };

  // ================= QUIZ WINDOW DRAG =================
  const handleMouseDown = (e) => {
    if (e.target.closest('.quiz-close') || e.target.closest('.quiz-maximize')) return;
    setIsDragging(true);
    const rect = quizRef.current.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDragging && !quizMaximized) {
        const newX = e.clientX - dragOffset.x;
        const newY = window.innerHeight - e.clientY - (quizRef.current?.offsetHeight || 600) + dragOffset.y;
        
        setQuizPosition({
          x: Math.max(0, Math.min(newX, window.innerWidth - (quizRef.current?.offsetWidth || 450))),
          y: Math.max(0, Math.min(newY, window.innerHeight - (quizRef.current?.offsetHeight || 600)))
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset, quizMaximized]);

  // Helper to format time
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Helper to seek video
  const seekToTime = (seconds) => {
    if (playerRef.current && playerRef.current.seekTo) {
      playerRef.current.seekTo(seconds, true);
      playerRef.current.playVideo();
    }
  };

  // ================= UI =================
  return (
    <>
      <div className="header">
        <div className="header-inner">
          <h1 className="title">Adaptive Learning Path</h1>
          <p className="subtitle">Learn smarter with attention-aware quizzes</p>
        </div>
      </div>

      <div className="app-container">

        {/* Controls */}
        <div className="controls">
          <select onChange={(e) => setSelectedLecture(e.target.value)}>
            <option value="">Select Lecture</option>
            {Object.entries(lectures).map(([id, d]) => (
              <option key={id} value={id}>{d.title}</option>
            ))}
          </select>

          <button className="btn btn-primary" onClick={loadLecture}>
            Load Lecture
          </button>

          <button 
            className="btn btn-primary" 
            onClick={generateQuiz}
            disabled={!videoId}
          >
            📝 Generate Quiz
          </button>
        </div>

        <div className="main-grid">

          {/* VIDEO + TRANSCRIPT */}
          <div className="video-card">
            <div className="player-wrapper">
              <div id="yt-player"></div>
            </div>

            <p className="watch-time">⏱ Watched: {watchedSeconds}s</p>

            <div className="transcript-box">
              <div className="transcript-header">
                <b>Video Transcript</b>
                <label>
                  <input
                    type="checkbox"
                    checked={autoScroll}
                    onChange={() => setAutoScroll(!autoScroll)}
                  /> Auto Scroll
                </label>
              </div>

              <div className="transcript-content" ref={transcriptRef}>
                {transcriptTimeline.length > 0 ? (
                  transcriptTimeline.map((seg, index) => {
                    const isActive = 
                      watchedSeconds >= seg.start && 
                      watchedSeconds < seg.end;
                    
                    return (
                      <div
                        key={index}
                        data-segment-index={index}
                        className={`transcript-line ${isActive ? 'active' : ''}`}
                        onClick={() => seekToTime(seg.start)}
                      >
                        <span className="transcript-timestamp">
                          {formatTime(seg.start)}
                        </span>
                        <span className="transcript-text">
                          {seg.text}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <p className="transcript-placeholder">
                    Transcript will appear here after loading a lecture...
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* NOTES */}
          <div className="quiz-card">

            <h2>Lecture Notes</h2>

            <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
              <button
                className="btn btn-secondary"
                onClick={() => generateNotes("watched")}
              >
                Generate Notes (Watched)
              </button>

              <button
                className="btn btn-secondary"
                onClick={() => generateNotes("full")}
              >
                Generate Full Notes
              </button>
            </div>

            {loadingNotes && <p>🧠 Generating notes...</p>}

            {notes && (
              <div className="notes-box">
                <ReactMarkdown>{notes}</ReactMarkdown>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* FLOATING QUIZ */}
      {quiz.length > 0 && !quizOpen && (
        <button className="quiz-toggle" onClick={() => setQuizOpen(true)}>
          📝 Quiz ({quiz.length})
        </button>
      )}

      {quizOpen && quiz.length > 0 && (
        <div 
          ref={quizRef}
          className={`floating-quiz ${quizMaximized ? 'maximized' : ''}`}
          style={!quizMaximized ? {
            left: `${quizPosition.x}px`,
            bottom: `${quizPosition.y}px`
          } : {}}
        >
          <div className="quiz-header" onMouseDown={handleMouseDown}>
            <h3>📝 Smart Quiz</h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                className="quiz-maximize" 
                onClick={() => setQuizMaximized(!quizMaximized)}
                title={quizMaximized ? "Restore" : "Maximize"}
              >
                {quizMaximized ? '❐' : '□'}
              </button>
              <button className="quiz-close" onClick={() => setQuizOpen(false)}>
                ✕
              </button>
            </div>
          </div>

          <div className="quiz-body">
            <div className="progress">
              Question {current + 1} / {quiz.length}
            </div>

            <div className="question-text">
              {quiz[current].question}
            </div>

            <div className="options">
              {quiz[current].options.map((opt, idx) => {
                let cls = "opt";
                if (answers[current] === idx) cls += " selected";
                if (submitted) {
                  if (idx === quiz[current].correct_index)
                    cls += " correct";
                  else if (answers[current] === idx)
                    cls += " incorrect";
                }

                return (
                  <div
                    key={idx}
                    className={cls}
                    onClick={() => selectOption(idx)}
                  >
                    {opt}
                  </div>
                );
              })}
            </div>

            {!submitted && (
              <button 
                className="btn btn-primary" 
                onClick={submitAnswer}
                disabled={answers[current] === undefined}
              >
                Submit Answer
              </button>
            )}

            {submitted && (
              <div className="result">
                {answers[current] === quiz[current].correct_index
                  ? "✅ Correct!"
                  : "❌ Wrong"}
                <div className="ans">
                  {quiz[current].explanation}
                </div>
              </div>
            )}

            {submitted && current < quiz.length - 1 && (
              <button className="btn btn-primary" onClick={nextQuestion}>
                Next Question →
              </button>
            )}

            {submitted && current === quiz.length - 1 && (
              <div className="quiz-complete">
                <h4>🎉 Quiz Complete!</h4>
                <p>You've answered all {quiz.length} questions.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* FLOATING CHATBOT */}
      {!chatOpen && (
        <button className="chat-toggle" onClick={() => setChatOpen(true)}>
          🤖 AI Tutor
        </button>
      )}

      {chatOpen && (
        <div className="floating-chat">
          <div className="chat-header">
            <h3>🤖 AI Tutor</h3>
            <button className="chat-close" onClick={() => setChatOpen(false)}>
              ✕
            </button>
          </div>

          <div className="chat-body">
            {botAnswer && (
              <div className="bot-message">
                <ReactMarkdown>{botAnswer}</ReactMarkdown>
              </div>
            )}
            {botLoading && <p className="thinking">🧠 Thinking...</p>}
          </div>

          <div className="chat-input-wrapper">
            <input
              value={userQuestion}
              onChange={(e) => setUserQuestion(e.target.value)}
              placeholder="Ask about this lecture..."
              className="chat-input"
              onKeyPress={(e) => e.key === "Enter" && askBot()}
            />
            <button 
              onClick={askBot} 
              className="chat-send" 
              disabled={!userQuestion || !videoId}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default App;