import { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {

  const [lectures, setLectures] = useState({});
  const [selectedLecture, setSelectedLecture] = useState("");

  const [videoId, setVideoId] = useState("");

  const [quiz, setQuiz] = useState([]);

  // 🔥 NEW STATES FOR ONE-BY-ONE
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState({});

  const [loadingTranscript, setLoadingTranscript] = useState(false);
  const [loadingQuiz, setLoadingQuiz] = useState(false);

  const [watchedSeconds, setWatchedSeconds] = useState(0);
  const [showAnswers, setShowAnswers] = useState(false);

  const [transcriptText, setTranscriptText] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);

  const playerRef = useRef(null);
  const timerRef = useRef(null);
  const transcriptRef = useRef(null);


  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/lectures/")
      .then(res => res.json())
      .then(setLectures);
  }, []);


  useEffect(() => {
    if (window.YT) return;

    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.body.appendChild(tag);
  }, []);


  const initPlayer = (id) => {
    if (playerRef.current) {
      playerRef.current.destroy();
    }

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

          const box = transcriptRef.current;

          box.scrollTo({
            top: box.scrollTop + 20,
            behavior: "smooth"
          });

        }

      }, 1200);

    } else {
      clearInterval(timerRef.current);
    }
  };


  const loadLecture = async () => {

    if (!selectedLecture) return;

    setQuiz([]);
    setAnswers({});
    setCurrent(0);
    setShowAnswers(false);
    setWatchedSeconds(0);
    setTranscriptText("");

    setLoadingTranscript(true);

    const res = await fetch(
      "http://127.0.0.1:8000/api/submit-video/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lecture_id: selectedLecture
        }),
      }
    );

    const data = await res.json();

    setLoadingTranscript(false);

    if (data.video_id) {

      setVideoId(data.video_id);
      initPlayer(data.video_id);

      fetch(
        `http://127.0.0.1:8000/api/transcript/${data.video_id}/`
      )
        .then(r => r.json())
        .then(d => {
          setTranscriptText(d.full_text || "");
        })
        .catch(() =>
          setTranscriptText("Transcript will appear after processing...")
        );
    }
  };


  const generateQuiz = async () => {

    if (!videoId) return;

    setLoadingQuiz(true);
    setQuiz([]);
    setAnswers({});
    setCurrent(0);
    setShowAnswers(false);

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

    if (data.status === "success" && Array.isArray(data.quiz)) {
      setQuiz(data.quiz);
    }

    setLoadingQuiz(false);
  };


  // =========== QUIZ NAVIGATION ============

  const selectOption = (idx) => {
    setAnswers({
      ...answers,
      [current]: idx
    });
  };

  const next = () => {
    if (current < quiz.length - 1)
      setCurrent(current + 1);
  };

  const prev = () => {
    if (current > 0)
      setCurrent(current - 1);
  };

  // ========================================



  return (

    <>
      <div className="header">
        <div className="header-inner">
          <h1 className="title">Adaptive Learning Path</h1>
          <p className="subtitle">
            Learn smarter with attention-aware quizzes
          </p>
        </div>
      </div>


      <div className="app-container">

        <div className="controls">

          <select onChange={(e) => setSelectedLecture(e.target.value)}>
            <option value="">Select Lecture</option>

            {Object.entries(lectures).map(([id, data]) => (
              <option key={id} value={id}>
                {data.title}
              </option>
            ))}
          </select>

          <button className="btn btn-primary" onClick={loadLecture}>
            Load Lecture
          </button>

        </div>


        <div className="main-grid">

          <div className="video-card">

            <div className="player-wrapper">
              <div id="yt-player"></div>
            </div>

            <p className="watch-time">
              ⏱ Watched: {watchedSeconds}s
            </p>


            {/* TRANSCRIPT */}
            <div className="transcript-box">

              <div className="transcript-header">
                <b>Video Transcript</b>

                <label>
                  <input
                    type="checkbox"
                    checked={autoScroll}
                    onChange={() =>
                      setAutoScroll(!autoScroll)
                    }
                  /> Auto Scroll
                </label>
              </div>

              <div
                className="transcript-content"
                ref={transcriptRef}
              >

                {transcriptText ? (

                  transcriptText.split(". ").map((line, i) => (

                    <p
                      key={i}
                      className={i % 3 === 0 ? "active-line" : ""}
                    >
                      {line}.
                    </p>

                  ))

                ) : (
                  <p>Transcript will appear here...</p>
                )}

              </div>

            </div>

          </div>



          {/* ========== QUIZ ONE BY ONE ========== */}

          <div className="quiz-card">

            <h2>AI Quiz</h2>

            <button
              className="btn btn-secondary"
              onClick={generateQuiz}
            >
              Generate Smart Quiz
            </button>

            <p className="small">
              Used duration: {watchedSeconds}s
            </p>



            {quiz.length > 0 && (

              <>
                <div className="progress">
                  Question {current + 1} / {quiz.length}
                </div>


                <div className="quiz-item">

                  <b>
                    {current + 1}. {quiz[current].question}
                  </b>

                  <div className="options">

                    {quiz[current].options.map((opt, idx) => (

                      <label key={idx} className="opt">

                        <input
                          type="radio"
                          name="opt"
                          checked={answers[current] === idx}
                          onChange={() => selectOption(idx)}
                        />

                        {opt}

                      </label>

                    ))}

                  </div>



                  {showAnswers && (

                    <div className="result">

                      {answers[current] ===
                        quiz[current].correct_index
                        ? "✅ Correct"
                        : "❌ Wrong"
                      }

                      <div className="ans">
                        Correct: {
                          quiz[current].options[
                            quiz[current].correct_index
                          ]
                        }
                      </div>

                    </div>

                  )}

                </div>



                <div className="nav">

                  <button
                    className="btn"
                    onClick={prev}
                    disabled={current === 0}
                  >
                    Previous
                  </button>



                  {current < quiz.length - 1 ? (

                    <button
                      className="btn btn-primary"
                      onClick={next}
                    >
                      Next
                    </button>

                  ) : (

                    <button
                      className="btn btn-primary"
                      onClick={() => setShowAnswers(true)}
                    >
                      Finish
                    </button>

                  )}

                </div>

              </>

            )}

          </div>

        </div>
      </div>
    </>
  );
}

export default App;
