import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Send, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Brain, 
  BarChart3, 
  Flag,
  Mic,
  Volume2,
  Square,
  Play
} from 'lucide-react';
import api from '../services/api';

// Canonical technical term mapping for live speech recognition
function normalizeLiveTerms(text) {
  if (!text) return '';
  // Strip any accidental non-Latin or Arabic/Urdu script
  text = text.replace(/[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+/g, '');

  const rules = [
    [/\b(?:see\s*plus\s*plus|c\s*plus\s*plus)\b/gi, 'C++'],
    [/\b(?:see\s*sharp|c\s*sharp)\b/gi, 'C#'],
    [/\b(?:fast\s*api)\b/gi, 'FastAPI'],
    [/\b(?:node\s*js)\b/gi, 'Node.js'],
    [/\b(?:next\s*js)\b/gi, 'Next.js'],
    [/\b(?:pie\s*thon|python)\b/gi, 'Python'],
    [/\b(?:java)\b/gi, 'Java'],
    [/\b(?:golang)\b/gi, 'Go'],
    [/\b(?:type\s*script)\b/gi, 'TypeScript'],
    [/\b(?:java\s*script)\b/gi, 'JavaScript'],
    [/\b(?:postgres|post\s*gres|postgress)\b/gi, 'PostgreSQL'],
    [/\b(?:mongo\s*db)\b/gi, 'MongoDB'],
    [/\b(?:sequel|s\s*q\s*l)\b/gi, 'SQL'],
    [/\b(?:no\s*sql)\b/gi, 'NoSQL'],
    [/\b(?:sqlite|sequel\s*lite)\b/gi, 'SQLite'],
    [/\b(?:rest\s*apis?)\b/gi, 'REST API'],
    [/\b(?:rest\s*ful)\b/gi, 'RESTful'],
    [/\b(?:j\s*w\s*t|jay\s*son\s*web\s*tokens?|json\s*web\s*tokens?)\b/gi, 'JWT'],
    [/\b(?:o\s*auth\s*2|oauth\s*2)\b/gi, 'OAuth 2.0'],
    [/\b(?:o\s*auth)\b/gi, 'OAuth'],
    [/\b(?:k\s*8\s*s|cooper\s*neties|cubernetes)\b/gi, 'Kubernetes'],
    [/\b(?:dock\s*er)\b/gi, 'Docker'],
    [/\b(?:git\s*hub)\b/gi, 'GitHub'],
    [/\b(?:ci\s*cd|c\s*i\s*c\s*d)\b/gi, 'CI/CD'],
    [/\b(?:g\s*i\s*l)\b/gi, 'GIL'],
    [/\b(?:o\s*o\s*p)\b/gi, 'OOP'],
    [/\b(?:d\s*s\s*a)\b/gi, 'DSA'],
    [/\b(?:r\s*a\s*g)\b/gi, 'RAG'],
    [/\b(?:l\s*l\s*ms?)\b/gi, 'LLM'],
    [/\b(?:a\s*c\s*i\s*d)\b/gi, 'ACID'],
    [/\b(?:v\s*tables?)\b/gi, 'vtable'],
    [/\b(?:b\s*trees?)\b/gi, 'B-tree'],
    [/\b(?:async\s*and\s*await|async\s*await)\b/gi, 'async/await'],
  ];

  for (const [pattern, replacement] of rules) {
    text = text.replace(pattern, replacement);
  }
  return text;
}

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
  const [questionsAnswered, setQuestionsAnswered] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  // Voice layer state
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [autoplayBlocked, setAutoplayBlocked] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [micPermissionDenied, setMicPermissionDenied] = useState(false);
  const [liveInterimSnippet, setLiveInterimSnippet] = useState('');

  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const baseAnswerRef = useRef('');

  useEffect(() => {
    loadSession();
    return () => {
      stopAudioPlayback();
      cleanupRecording();
    };
  }, [id]);

  // Trigger TTS whenever a new question is set
  useEffect(() => {
    if (currentQuestion) {
      const isFirst = currentQuestion.question_number === 1;
      playQuestionAudio(currentQuestion, isFirst);
    }
    return () => {
      stopAudioPlayback();
    };
  }, [currentQuestion?.id]);

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
        setCurrentQuestion(questions[questions.length - 1]);
        setQuestionsAnswered(questions.length);
      }
    } catch (err) {
      setError('Failed to load interview session');
    } finally {
      setLoading(false);
    }
  };

  // ── Voice Output (TTS) ───────────────────────────────────

  const stopAudioPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsSpeaking(false);
    setTtsLoading(false);
  };

  const playQuestionAudio = async (question, isIntro = false) => {
    if (!question || !question.question_text) return;

    stopAudioPlayback();
    setTtsLoading(true);
    setAutoplayBlocked(false);

    try {
      const res = await api.post(
        '/interviews/voice/tts',
        {
          text: question.question_text,
          question_number: question.question_number || 1,
          include_intro: isIntro,
        },
        { responseType: 'blob' }
      );

      const blobUrl = URL.createObjectURL(res.data);
      const audio = new Audio(blobUrl);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);
        setTtsLoading(false);
        setAutoplayBlocked(false);
      };

      audio.onended = () => {
        setIsSpeaking(false);
        setTtsLoading(false);
      };

      audio.onerror = () => {
        setIsSpeaking(false);
        setTtsLoading(false);
      };

      // Handle browser autoplay policy
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          setIsSpeaking(false);
          setTtsLoading(false);
          if (err.name === 'NotAllowedError') {
            setAutoplayBlocked(true);
          }
        });
      }
    } catch (err) {
      setIsSpeaking(false);
      setTtsLoading(false);
    }
  };

  // ── Voice Input (Live Speech-to-Text & Whisper Refinement) ──

  const cleanupRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (_) {}
    }
    if (mediaRecorderRef.current?.stream) {
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
    mediaRecorderRef.current = null;
  };

  const startRecording = async () => {
    stopAudioPlayback();
    setMicPermissionDenied(false);
    setError('');
    setLiveInterimSnippet('');
    baseAnswerRef.current = answer.trim();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setMicPermissionDenied(true);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });
        stream.getTracks().forEach((t) => t.stop());

        if (audioBlob.size > 500) {
          await transcribeRecordedAudio(audioBlob);
        } else {
          setIsTranscribing(false);
        }
      };

      recorder.start(250);
      setIsRecording(true);

      // Initialize browser Web Speech API for LIVE word-by-word streaming
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';

          let sessionFinal = '';

          recognition.onresult = (event) => {
            let interim = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
              const text = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                sessionFinal += ' ' + text;
              } else {
                interim += ' ' + text;
              }
            }

            const rawSpoken = (sessionFinal + ' ' + interim).trim();
            const normalizedSpoken = normalizeLiveTerms(rawSpoken);
            setLiveInterimSnippet(normalizedSpoken);

            // Stream live words directly into the textarea!
            const prefix = baseAnswerRef.current;
            const fullAnswer = prefix ? `${prefix} ${normalizedSpoken}` : normalizedSpoken;
            setAnswer(fullAnswer.trim());
          };

          recognition.onerror = (e) => {
            console.warn('SpeechRecognition warning:', e.error);
          };

          recognition.onend = () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              try { recognition.start(); } catch (_) {}
            }
          };

          recognition.start();
          recognitionRef.current = recognition;
        } catch (e) {
          console.warn('Live recognition error:', e);
        }
      }
    } catch (err) {
      setIsRecording(false);
      setMicPermissionDenied(true);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      setIsRecording(false);
      setIsTranscribing(true);
      mediaRecorderRef.current.stop();
    } else {
      setIsRecording(false);
      setIsTranscribing(false);
    }
  };

  const transcribeRecordedAudio = async (audioBlob) => {
    setIsTranscribing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'candidate_answer.webm');

      const res = await api.post('/interviews/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const rawTranscript = (res.data?.transcript || '').trim();
      const cleanTranscript = normalizeLiveTerms(rawTranscript);

      if (cleanTranscript) {
        const prefix = baseAnswerRef.current;
        const refined = prefix ? `${prefix} ${cleanTranscript}` : cleanTranscript;
        setAnswer(refined.trim());
      }
    } catch (err) {
      // If Whisper network fails, keep the live Web Speech text that was already captured!
      console.warn('Whisper STT error, preserving live speech text:', err);
    } finally {
      setIsTranscribing(false);
      setLiveInterimSnippet('');
    }
  };

  // ── Answer Submission ────────────────────────────────────

  const handleSubmitAnswer = async () => {
    if (!currentQuestion || submitting) return;
    if (!answer.trim()) {
      setError('Please write or speak an answer before submitting.');
      return;
    }

    if (isRecording) stopRecording();
    stopAudioPlayback();

    setSubmitting(true);
    setError('');

    try {
      const res = await api.post(
        `/interviews/${id}/questions/${currentQuestion.id}/answer`,
        { answer_text: answer }
      );

      const data = res.data;

      // Update question answered count internally
      setQuestionsAnswered(data.questions_answered || (questionsAnswered + 1));

      // Handle interview completion (auto-stop triggered by adaptive engine)
      if (data.is_complete) {
        setIsComplete(true);
        navigate(`/results/${id}`);
      } else if (data.next_question) {
        // Immediately proceed to the next question with zero in-interview evaluation
        setCurrentQuestion(data.next_question);
        setAnswer('');
        baseAnswerRef.current = '';
        setLiveInterimSnippet('');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinishInterview = async () => {
    if (!confirm('Are you sure you want to finish the interview now?')) return;
    stopAudioPlayback();
    if (isRecording) stopRecording();

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
                {session?.mode === 'syllabus' ? 'Syllabus & Course Session' : 'Open-Ended Adaptive Session'}
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
        
        {/* Question Card */}
        {currentQuestion && (
          <div className="flex flex-col flex-1 animate-[fadeIn_0.3s_ease-out]">
            {/* Question metadata */}
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="badge bg-slate-200 text-slate-800 font-semibold shadow-sm">
                <span className="text-slate-500 font-normal mr-1">{session?.mode === 'syllabus' ? 'Topic:' : 'Skill:'}</span>
                {currentQuestion.skill}
              </span>
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

            {/* Question Card with Subtle Voice Status */}
            <div className="card p-6 md:p-8 mb-6 shadow-sm border-t-4 border-t-indigo-600">
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-bold text-slate-400 tracking-wider">
                  QUESTION {currentQNum}
                </div>

                {/* Voice Status Controls */}
                <div className="flex items-center gap-2">
                  {ttsLoading && (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                      <Loader2 size={12} className="animate-spin text-indigo-600" />
                      Loading voice...
                    </span>
                  )}

                  {isSpeaking && (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-full animate-pulse shadow-sm">
                      <Volume2 size={13} className="text-indigo-600" />
                      Interviewer speaking
                      <button 
                        onClick={stopAudioPlayback} 
                        className="text-slate-400 hover:text-slate-700 ml-1.5 text-[11px] font-semibold underline"
                        title="Skip audio"
                      >
                        Skip
                      </button>
                    </span>
                  )}

                  {autoplayBlocked && !isSpeaking && !ttsLoading && (
                    <button
                      onClick={() => playQuestionAudio(currentQuestion, currentQuestion.question_number === 1)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-3 py-1 rounded-full transition-colors shadow-sm"
                      title="Click to hear the interviewer speak the question"
                    >
                      <Play size={12} fill="currentColor" />
                      Listen to Interviewer
                    </button>
                  )}

                  {!isSpeaking && !ttsLoading && !autoplayBlocked && (
                    <button
                      onClick={() => playQuestionAudio(currentQuestion, false)}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-indigo-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-md transition-colors shadow-sm"
                      title="Listen to question again"
                    >
                      <Volume2 size={12} />
                      Replay
                    </button>
                  )}
                </div>
              </div>

              <p className="text-lg md:text-xl font-medium text-slate-900 leading-relaxed">
                {currentQuestion.question_text}
              </p>
            </div>

            {/* Answer Card with Integrated Microphone and LIVE STT */}
            <div className="card p-4 md:p-6 shadow-sm flex-1 flex flex-col mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-bold text-slate-700 block" htmlFor="answer-input">
                  Your Answer
                </label>

                {/* Subtle Live Recording / Transcribing Indicator */}
                <div className="flex items-center gap-2">
                  {isRecording && (
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
                      Listening live... Speak technical answer (click mic to finish)
                    </span>
                  )}
                  {isTranscribing && (
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 rounded-full">
                      <Loader2 size={12} className="animate-spin" />
                      Refining technical terms...
                    </span>
                  )}
                </div>
              </div>

              <div className="relative flex-1 flex flex-col">
                <textarea
                  id="answer-input"
                  className="input flex-1 resize-y min-h-[200px] md:min-h-[250px] text-base leading-relaxed bg-slate-50 focus:bg-white pr-14"
                  value={answer}
                  onChange={e => { setAnswer(e.target.value); setError(''); }}
                  placeholder="Type your answer here, or click the microphone to speak live..."
                  disabled={submitting || isTranscribing}
                />

                {/* Clean Microphone Button inside the textarea */}
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={submitting || isTranscribing}
                  title={
                    isRecording 
                      ? "Click to finish speaking and refine technical terms" 
                      : "Click to speak your answer with live microphone"
                  }
                  className={`absolute top-3 right-3 p-2.5 rounded-full transition-all shadow-sm ${
                    isRecording
                      ? "bg-emerald-600 text-white ring-4 ring-emerald-100 hover:bg-emerald-700 animate-pulse"
                      : isTranscribing
                      ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                      : "bg-white text-slate-600 border border-slate-200 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50"
                  }`}
                >
                  {isTranscribing ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : isRecording ? (
                    <Square size={18} fill="currentColor" />
                  ) : (
                    <Mic size={18} />
                  )}
                </button>
              </div>

              {/* Real-time live snippet feedback when recording */}
              {isRecording && liveInterimSnippet && (
                <div className="mt-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded px-2.5 py-1.5 flex items-center gap-2">
                  <span className="font-semibold text-emerald-600">Live Voice:</span>
                  <span className="italic truncate">{liveInterimSnippet}</span>
                </div>
              )}

              {/* Inline Microphone Notice if permission is denied */}
              {micPermissionDenied && (
                <div className="mt-3 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between">
                  <span>Microphone access was denied or is unavailable. You can continue typing your answer normally in English.</span>
                  <button 
                    onClick={() => setMicPermissionDenied(false)} 
                    className="text-amber-700 hover:text-amber-900 font-bold ml-3"
                  >
                    Dismiss
                  </button>
                </div>
              )}
              
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
                      Submitting...
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
