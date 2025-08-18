import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getAttemptQuestions, submitQuiz, abandonQuiz } from '../api';

export default function QuizPlay() {
  const [items, setItems] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [current, setCurrent] = React.useState(0);
  const [timeLeft, setTimeLeft] = React.useState(300); // 300 seconds = 5 minutes
  const [error, setError] = React.useState(null);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const attemptId = params.get('attempt_id');
  const finishedRef = React.useRef(false);

  // Load the questions for this attempt
  React.useEffect(() => {
    if (!attemptId) {
      navigate('/');
      return;
    }
    async function loadQuestions() {
      try {
        const res = await getAttemptQuestions(attemptId);
        setItems(res.items);
        // Initialize answers array (null for each question)
        setAnswers(new Array(res.items.length).fill(null));
      } catch (e) {
        setError(e.message);
      }
    }
    loadQuestions();
  }, [attemptId, navigate]);

  // Start countdown timer
  React.useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((t) => t - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Auto-submit when time runs out
  React.useEffect(() => {
    if (timeLeft <= 0 && !finishedRef.current) {
      finishQuiz();
    }
  }, [timeLeft]);

  // Finalize the quiz: submit answers and navigate to results
  async function finishQuiz() {
    if (finishedRef.current) return;
    finishedRef.current = true;
    try {
      const result = await submitQuiz(
        attemptId,
        // Map answers state to API payload (use -1 for unanswered)
        answers.map((ans, i) => ({ id: items[i].id, answer: ans ?? -1 }))
      );
      // Go to results page with IQ score and percentile in query params
      navigate(
        `/result?iq=${result.iq}&percentile=${result.percentile}` +
          (result.share_url
            ? `&share_url=${encodeURIComponent(result.share_url)}`
            : '')
      );
    } catch (e) {
      setError(e.message);
    }
  }

  // Select an answer for the current question (but do not auto-advance)
  const selectAnswer = (optionIndex) => {
    const updatedAnswers = [...answers];
    updatedAnswers[current] = optionIndex;
    setAnswers(updatedAnswers);
  };

  // Navigation handlers
  const prevQuestion = () => {
    if (current > 0) setCurrent(current - 1);
  };
  const nextQuestion = () => {
    if (current < items.length - 1) {
      setCurrent(current + 1);
    } else {
      // Last question -> finish quiz
      finishQuiz();
    }
  };

  // If user navigates away without finishing, mark attempt abandoned
  React.useEffect(() => {
    return () => {
      if (!finishedRef.current && attemptId) {
        abandonQuiz(attemptId); // best-effort flag as abandoned
      }
    };
  }, [attemptId]);

  if (error) {
    return <div className="p-4 text-center text-red-600">{error}</div>;
  }
  if (!items.length) {
    return <div className="p-4 text-center">Loading...</div>;
  }

  const q = items[current];
  const total = items.length;
  const questionNum = current + 1;
  // Format remaining time as M:SS
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const timeDisplay = `${minutes}:${seconds.toString().padStart(2, '0')}`;

  return (
    <div className="max-w-xl mx-auto p-4 space-y-4">
      {/* Header: question progress and timer */}
      <div className="flex items-center justify-between">
        <div className="font-medium">
          Question {questionNum} / {total}
        </div>
        <div className={`font-medium ${timeLeft < 60 ? 'text-red-600' : ''}`}>
          Time: {timeDisplay}
        </div>
      </div>
      {/* Progress bar */}
      <div className="progress-track">
        <div
          className="progress-bar"
          style={{ width: `${(questionNum / total) * 100}%` }}
        />
      </div>
      {/* Question text (and image if present) */}
      <div className="text-lg font-semibold">{q.question}</div>
      {q.image && (
        <img
          src={q.image}
          alt="Question"
          className="mx-auto mb-4 max-h-60 w-full object-contain"
        />
      )}
      {/* Answer options */}
      <div>
        {q.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => selectAnswer(i)}
            className={`block w-full text-left px-4 py-3 rounded-lg mb-2 ${
              answers[current] === i
                ? 'border-2 border-blue-500'
                : 'border border-gray-300'
            } bg-white hover:bg-gray-50`}
          >
            {/* Option image, if any */}
            {q.option_images && q.option_images[i] && (
              <img
                src={q.option_images[i]}
                alt=""
                className="max-h-40 w-full object-contain mb-2"
              />
            )}
            <span>{opt}</span>
          </button>
        ))}
      </div>
      {/* Navigation buttons: Previous, Next/Finish, Exit */}
      <div className="flex justify-between mt-4">
        <button
          type="button"
          onClick={prevQuestion}
          disabled={current === 0}
          className="btn-outline px-4 py-2"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={nextQuestion}
          className="btn-primary px-4 py-2"
        >
          {current < total - 1 ? 'Next' : 'Finish'}
        </button>
        <button
          type="button"
          onClick={finishQuiz}
          className="btn-outline px-4 py-2"
        >
          Exit
        </button>
      </div>
    </div>
  );
}

