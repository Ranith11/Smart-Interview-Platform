import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, CheckCircle, AlertCircle, Loader2, Brain, BarChart3, Flag, Mic } from 'lucide-react';
import api from '../services/api';
import useSpeechToText from '../hooks/useSpeechToText';

export default function Interview() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Session state
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState('');

  const handleTranscriptComplete = (text) => {
    if (!text.trim()) return;
    setAnswer(prev => {
      const separator = prev.trim() ? ' ' : '';
      return prev + separator + text.trim();
    });
  };

  const {
    status: speechStatus,
    interimTexts,
    error: speechError,
    startRecording,
    stopRecording,
    reset: resetSpeech
  } = useSpeechToText(handleTranscriptComplete);

  const isRecording = speechStatus === 'recording';
  const isTranscribing = speechStatus === 'transcribing';
  const isSpeechActive = isRecording || isTranscribing;

  // Adaptive state
  const [evaluation, setEvaluation] = useState(null);
  const [showEvaluation, setShowEvaluation] = useState(false);
  const [questionsAnswered, setQuestionsAnswered] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    loadSession();
  }, [id]);

  const loadSession = async () => {
    try {
      const res = await api.get(`/interviews/${id}`);
      const data = res.data;
      setSession(data);

      if (data.status === 'completed') {
        navigate(`/results/${id}`);
        return;
      }

      // Find the latest unanswered question
      const questions = data.questions || [];
      const unanswered = questions.find(q => !q.answer_text);
      if (unanswered) {
        setCurrentQuestion(unanswered);
        setQuestionsAnswered(questions.filter(q => q.answer_text).length);
      } else if (questions.length > 0) {
        // All answered — maybe we need to finish?
        setCurrentQuestion(questions[questions.length - 1]);
        setQuestionsAnswered(questions.length);
      }
    } catch (err) {
      setError('Failed to load interview session');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!currentQuestion || submitting) return;
    if (!answer.trim()) {
      setError('Please write an answer before submitting.');
      return;
    }

    setSubmitting(true);
    setError('');
    setEvaluation(null);

    try {
      const res = await api.post(
        `/interviews/${id}/questions/${currentQuestion.id}/answer`,
        { answer_text: answer }
      );

      const data = res.data;

      if (data.evaluation) {
        setEvaluation(data.evaluation);
        setShowEvaluation(true);
        setQuestionsAnswered(data.questions_answered || questionsAnswered + 1);
      }

      if (data.is_complete) {
        setIsComplete(true);
        setTimeout(() => {
          resetSpeech();
          navigate(`/results/${id}`);
        }, 4000);
      } else if (data.next_question) {
        setTimeout(() => {
          resetSpeech(); // Ensure microphone stops and pending requests are invalidated
          setCurrentQuestion(data.next_question);
          setAnswer('');
          setShowEvaluation(false);
          setEvaluation(null);
        }, 3000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinishInterview = async () => {
    if (!confirm('Are you sure you want to finish the interview now?')) return;
    setFinishing(true);
    try {
      await api.post(`/interviews/${id}/complete`);
      navigate(`/results/${id}`);
    } catch (err) {
      setError('Failed to finish interview');
      setFinishing(false);
    }
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score >= 60) return 'text-amber-600 bg-amber-50 border-amber-200';
    if (score >= 40) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };
  
  const getScoreTextColor = (score) => {
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-amber-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getBloomLabel = (level) => {
    const labels = {
      remember: 'Remember', understand: 'Understand', apply: 'Apply',
      analyze: 'Analyze', evaluate: 'Evaluate', create: 'Create'
    };
    return labels[level] || level || '';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-center">
          <Loader2 size={48} className="animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Loading your interview...</p>
        </div>
      </div>
    );
  }

  if (error && !currentQuestion) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-4">
        <div className="card max-w-md w-full text-center p-8">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-900 mb-2">Error</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <button className="btn btn-primary w-full shadow-sm" onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
        </div>
      </div>
    );
  }

  const currentQNum = currentQuestion?.question_number || 1;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Bar */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-16 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-bold text-lg text-slate-900 tracking-tight">Smart<span className="text-indigo-600">Interview</span></span>
              <span className="badge bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-sm hidden sm:inline-flex">
                {session?.mode === 'syllabus' 
                  ? 'Syllabus Mode' 
                  : session?.mode === 'job_specific'
                    ? 'Job-Specific Interview'
                    : 'General Technical Session'}
              </span>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-sm font-semibold text-slate-500 bg-slate-100 px-3 py-1 rounded-md">
                Question {currentQNum}
              </div>
              <button 
                onClick={handleFinishInterview} 
                disabled={finishing || submitting}
                className="btn bg-white border border-slate-300 text-slate-700 hover:bg-red-50 hover:text-red-700 hover:border-red-200 transition-colors py-1.5 shadow-sm"
              >
                {finishing ? <Loader2 size={16} className="animate-spin mr-1.5" /> : <Flag size={16} className="mr-1.5" />}
                Finish Interview
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 w-full max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 flex flex-col">
        
        {/* Evaluation Overlay */}
        {showEvaluation && evaluation && (
          <div className="card mb-8 overflow-hidden animate-[fadeIn_0.4s_ease-out]">
            <div className="p-6">
              {isComplete && (
                <div className="py-8 p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-center shadow-sm">
                  <CheckCircle size={32} className="text-emerald-600 mx-auto mb-3" />
                  <p className="text-base font-bold text-emerald-800">Interview complete! Redirecting to results...</p>
                </div>
              )}

              {!isComplete && (
                <div className="py-12 text-center text-base font-medium text-slate-500 flex flex-col items-center justify-center gap-4">
                  <Loader2 size={32} className="animate-spin text-indigo-500" />
                  Submitting answer & generating your next question...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Question Card */}
        {!showEvaluation && currentQuestion && (
          <div className="flex flex-col flex-1 animate-[fadeIn_0.3s_ease-out]">
            {/* Question Metadata */}
            {session?.mode !== 'syllabus' && currentQuestion && (
              <div className="flex items-center gap-3 mb-3">
                {currentQuestion.skill && (
                  <span className="px-3 py-1.5 text-xs font-bold uppercase tracking-widest bg-slate-100 text-slate-700 rounded-md shadow-sm border border-slate-200">
                    {currentQuestion.skill}
                  </span>
                )}
                {currentQuestion.difficulty && (
                  <span className={`px-3 py-1.5 text-xs font-bold uppercase tracking-widest rounded-md shadow-sm border ${
                    currentQuestion.difficulty === 'hard' ? 'bg-red-50 text-red-700 border-red-200' :
                    currentQuestion.difficulty === 'medium' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    'bg-emerald-50 text-emerald-700 border-emerald-200'
                  }`}>
                    {currentQuestion.difficulty}
                  </span>
                )}
                {currentQuestion.bloom_level && (
                  <span className="px-3 py-1.5 text-xs font-bold uppercase tracking-widest bg-indigo-50 text-indigo-700 rounded-md shadow-sm border border-indigo-200">
                    {getBloomLabel(currentQuestion.bloom_level)}
                  </span>
                )}
              </div>
            )}

            {/* Question */}
            <div className="card p-6 md:p-8 mb-6 shadow-sm border-t-4 border-t-indigo-600">
              <div className="text-xs font-bold text-slate-400 mb-3 tracking-wider">
                QUESTION {currentQNum}
              </div>
              <p className="text-lg md:text-xl font-medium text-slate-900 leading-relaxed">
                {currentQuestion.question_text}
              </p>
            </div>

            {/* Answer */}
            <div className="card p-4 md:p-6 shadow-sm flex-1 flex flex-col mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-bold text-slate-700 block" htmlFor="answer-input">Your Answer</label>
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={submitting || isTranscribing}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    isRecording 
                      ? 'bg-red-100 text-red-700 border border-red-200 hover:bg-red-200' 
                      : isTranscribing
                      ? 'bg-amber-100 text-amber-700 border border-amber-200 cursor-wait'
                      : 'bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isRecording ? (
                    <>
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                      </span>
                      Stop Speaking
                    </>
                  ) : isTranscribing ? (
                    <>
                      <Loader2 size={16} className="animate-spin text-amber-600" />
                      <span className="text-amber-700">Transcribing...</span>
                    </>
                  ) : (
                    <>
                      <Mic size={16} />
                      Start Speaking
                    </>
                  )}
                </button>
              </div>
              {/* Render active interim texts in chronological order */}
              {(() => {
                const activeInterims = Array.from(interimTexts.entries())
                  .sort((a, b) => a[0] - b[0])
                  .map(entry => entry[1])
                  .filter(text => text.trim().length > 0)
                  .join(' ');
                
                const isReceivingInterim = activeInterims.length > 0;
                // If answer is non-empty and activeInterims is non-empty, insert a space
                const displayedValue = activeInterims 
                  ? answer + (answer.trim() ? " " : "") + activeInterims 
                  : answer;

                return (
                  <textarea
                    id="answer-input"
                    className={`input flex-1 resize-y min-h-[200px] md:min-h-[250px] text-base leading-relaxed ${isSpeechActive ? 'bg-slate-100 border-indigo-200 ring-1 ring-indigo-200' : 'bg-slate-50 focus:bg-white'}`}
                    value={displayedValue}
                    onChange={e => { setAnswer(e.target.value); setError(''); }}
                    placeholder="Type your answer here or click Start Speaking..."
                    disabled={submitting}
                    // Only lock the textarea if words are actively flashing on screen. 
                    // This allows manual typing during natural pauses without stopping the mic!
                    readOnly={isReceivingInterim}
                  />
                );
              })()}
              
              <div className="flex flex-col sm:flex-row justify-between items-center mt-4 gap-4">
                <span className="text-xs font-medium text-slate-400">
                  {answer.length} characters
                </span>
                <button
                  className="btn btn-primary shadow-md px-8 py-3 w-full sm:w-auto text-base"
                  onClick={handleSubmitAnswer}
                  disabled={submitting || isSpeechActive || !answer.trim()}
                >
                  {submitting ? (
                    <>
                      <Loader2 size={20} className="animate-spin mr-2" />
                      Evaluating...
                    </>
                  ) : (
                    <>
                      Submit Answer
                      <Send size={18} className="ml-2" />
                    </>
                  )}
                </button>
              </div>
              
              {error && (
                <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm font-medium flex items-center gap-2">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}
              {speechError && (
                <div className="mt-4 p-3 rounded-lg bg-orange-50 border border-orange-200 text-orange-700 text-sm font-medium flex items-center gap-2">
                  <AlertCircle size={16} />
                  {speechError}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
