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
  const [notesMode, setNotesMode] = useState("");

  // Video + transcript
  const [watchedSeconds, setWatchedSeconds] = useState(0);
  const [transcriptText, setTranscriptText] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);

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
        setWatchedSeconds(
          Math.floor(playerRef.current.getCurrentTime())
        );

        if (autoScroll && transcriptRef.current) {
          transcriptRef.current.scrollBy({ top: 20, behavior: "smooth" });
        }
      }, 1200);
    } else {
      clearInterval(timerRef.current);
    }
  };

  // ================= LOAD LECTURE =================
  const loadLecture = async () => {
    if (!selectedLecture) return;

    setQuiz([]);
    setNotes("");
    setAnswers({});
    setCurrent(0);
    setSubmitted(false);
    setWatchedSeconds(0);
    setTranscriptText("");

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

      fetch(`http://127.0.0.1:8000/api/transcript/${data.video_id}/`)
        .then(r => r.json())
        .then(d => setTranscriptText(d.full_text || ""));
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
    }
  };

  // ================= NOTES =================
  const generateNotes = async (mode) => {
    if (!videoId) return;

    setLoadingNotes(true);
    setNotes("");
    setNotesMode(mode);

    const res = await fetch(
      "http://127.0.0.1:8000/api/generate-notes/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          watched_seconds: watchedSeconds,
          mode: mode, // watched | full
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
                {transcriptText
                  ? transcriptText.split(". ").map((l, i) => (
                      <p key={i} className={i % 3 === 0 ? "active-line" : ""}>
                        {l}.
                      </p>
                    ))
                  : <p>Transcript will appear here...</p>}
              </div>
            </div>
          </div>

          {/* QUIZ + NOTES */}
          <div className="quiz-card">

            <h2>AI Quiz</h2>

            <button className="btn btn-secondary" onClick={generateQuiz}>
              Generate Smart Quiz
            </button>

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

            {/* NOTES VIEW */}
            {loadingNotes && <p>🧠 Generating notes...</p>}

            {notes && (
              <div className="notes-box">
                <ReactMarkdown>{notes}</ReactMarkdown>
              </div>
            )}

            {/* QUIZ VIEW */}
            {quiz.length > 0 && (
              <>
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
                  <button className="btn btn-primary" onClick={submitAnswer}>
                    Submit Answer
                  </button>
                )}

                {submitted && (
                  <div className="result">
                    {answers[current] === quiz[current].correct_index
                      ? "✅ Correct"
                      : "❌ Wrong"}
                    <div className="ans">
                      {quiz[current].explanation}
                    </div>
                  </div>
                )}

                {submitted && current < quiz.length - 1 && (
                  <button className="btn btn-primary" onClick={nextQuestion}>
                    Next Question
                  </button>
                )}
              </>
            )}

          </div>
        </div>
      </div>
    </>
  );
}

export default App;
