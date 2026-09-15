import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, CheckCircle, AlertCircle, Loader2, Brain, BarChart3, Flag } from 'lucide-react';
import api from '../services/api';

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
          navigate(`/results/${id}`);
        }, 4000);
      } else if (data.next_question) {
        setTimeout(() => {
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
                {session?.mode === 'syllabus' ? 'Syllabus Mode' : 'Open-Ended Adaptive Session'}
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
            <div className={`p-1 ${getScoreColorClass(evaluation.overall_score).split(' ')[1]}`}></div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 size={20} className={getScoreTextColor(evaluation.overall_score)} />
                  Evaluation
                </h3>
                <span className={`text-3xl font-extrabold tracking-tight ${getScoreTextColor(evaluation.overall_score)}`}>
                  {evaluation.overall_score}%
                </span>
              </div>

              {/* Score breakdown */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
                {[
                  { label: 'Technical', value: evaluation.technical_score },
                  { label: 'Completeness', value: evaluation.completeness_score },
                  { label: 'Relevance', value: evaluation.relevance_score },
                  { label: 'Similarity', value: evaluation.semantic_similarity_score },
                  { label: 'Concepts', value: evaluation.concept_coverage_score },
                ].map(s => (
                  <div key={s.label} className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-center flex flex-col items-center justify-center shadow-sm">
                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">{s.label}</div>
                    <div className={`text-xl font-bold ${getScoreTextColor(s.value)}`}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Feedback */}
              {evaluation.feedback && (
                <div className="mb-6 p-4 rounded-lg bg-indigo-50/50 border border-indigo-100">
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {evaluation.feedback}
                  </p>
                </div>
              )}

              {/* Strengths / Weaknesses */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {evaluation.strengths?.length > 0 && (
                  <div>
                    <div className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      Strengths
                    </div>
                    <ul className="space-y-1.5 pl-3">
                      {evaluation.strengths.map((s, i) => (
                        <li key={i} className="text-sm text-slate-600 list-disc list-outside marker:text-emerald-400">{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {evaluation.weaknesses?.length > 0 && (
                  <div>
                    <div className="text-xs font-bold text-red-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                      Areas to Improve
                    </div>
                    <ul className="space-y-1.5 pl-3">
                      {evaluation.weaknesses.map((w, i) => (
                        <li key={i} className="text-sm text-slate-600 list-disc list-outside marker:text-red-400">{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {isComplete && (
                <div className="mt-8 p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-center shadow-sm">
                  <CheckCircle size={24} className="text-emerald-600 mx-auto mb-2" />
                  <p className="text-sm font-bold text-emerald-800">Interview complete! Redirecting to results...</p>
                </div>
              )}

              {!isComplete && (
                <div className="mt-8 text-center text-sm font-medium text-slate-400 flex items-center justify-center gap-2">
                  <Loader2 size={16} className="animate-spin" />
                  Generating your next adaptive question...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Question Card */}
        {!showEvaluation && currentQuestion && (
          <div className="flex flex-col flex-1 animate-[fadeIn_0.3s_ease-out]">
            {/* Question metadata */}
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="badge bg-slate-200 text-slate-800 font-semibold shadow-sm">{currentQuestion.skill}</span>
              <span className="badge bg-emerald-100 text-emerald-800 font-semibold shadow-sm capitalize">{currentQuestion.difficulty}</span>
              <span className="badge bg-amber-100 text-amber-800 font-semibold shadow-sm capitalize">
                {(currentQuestion.question_type || '').replace(/_/g, ' ')}
              </span>
              {currentQuestion.bloom_level && (
                <span className="badge bg-purple-100 text-purple-800 font-semibold shadow-sm flex items-center gap-1">
                  <Brain size={12} />
                  {getBloomLabel(currentQuestion.bloom_level)}
                </span>
              )}
            </div>

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
              <label className="text-sm font-bold text-slate-700 mb-2 block" htmlFor="answer-input">Your Answer</label>
              <textarea
                id="answer-input"
                className="input flex-1 resize-y min-h-[200px] md:min-h-[250px] text-base leading-relaxed bg-slate-50 focus:bg-white"
                value={answer}
                onChange={e => { setAnswer(e.target.value); setError(''); }}
                placeholder="Type your answer here..."
                disabled={submitting}
              />
              
              <div className="flex flex-col sm:flex-row justify-between items-center mt-4 gap-4">
                <span className="text-xs font-medium text-slate-400">
                  {answer.length} characters
                </span>
                <button
                  className="btn btn-primary shadow-md px-8 py-3 w-full sm:w-auto text-base"
                  onClick={handleSubmitAnswer}
                  disabled={submitting || !answer.trim()}
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
