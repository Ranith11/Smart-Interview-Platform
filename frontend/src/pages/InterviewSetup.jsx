import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Play, Settings, AlertCircle, ArrowRight, UploadCloud, FileText, X, CheckSquare, Square, Loader2, BookOpen } from 'lucide-react';

export default function InterviewSetup() {
  const [resume, setResume] = useState(null);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  // Syllabus Mode state
  const [mode, setMode] = useState('normal');
  const [uploadedFiles, setUploadedFiles] = useState([]);       // File objects staged for upload
  const [processing, setProcessing] = useState(false);          // Upload/processing in progress
  const [processingStatus, setProcessingStatus] = useState(''); // Status message during processing
  const [processedData, setProcessedData] = useState(null);     // { syllabus_id, subject, topics }
  const [selectedTopics, setSelectedTopics] = useState([]);

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/resumes/current')
      .then(res => {
        if (res?.data) {
          setResume(res.data);
          setSelectedSkills(res.data.skills || []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toggleSkill = (skill) => {
    setSelectedSkills(prev =>
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    );
  };

  const toggleTopic = (topic) => {
    setSelectedTopics(prev =>
      prev.includes(topic) ? prev.filter(t => t !== topic) : [...prev, topic]
    );
  };

  const handleFileSelect = (e) => {
    const newFiles = Array.from(e.target.files || []);
    const allowed = ['.pdf', '.txt', '.docx'];
    const valid = newFiles.filter(f => {
      const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
      return allowed.includes(ext);
    });
    if (valid.length !== newFiles.length) {
      setError('Only PDF, TXT, and DOCX files are supported.');
    } else {
      setError('');
    }
    setUploadedFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...valid.filter(f => !names.has(f.name))];
    });
    e.target.value = '';
  };

  const removeFile = (name) => {
    setUploadedFiles(prev => prev.filter(f => f.name !== name));
    if (uploadedFiles.length === 1) {
      setProcessedData(null);
      setSelectedTopics([]);
    }
  };

  const handleProcessMaterial = async () => {
    if (uploadedFiles.length === 0) {
      setError('Please upload at least one file first.');
      return;
    }
    setError('');
    setProcessing(true);
    setProcessedData(null);
    setSelectedTopics([]);

    const steps = [
      'Extracting content...',
      'Creating knowledge base...',
      'Detecting topics...',
      'Ready'
    ];
    let step = 0;
    setProcessingStatus(steps[step]);
    const stepTimer = setInterval(() => {
      step = Math.min(step + 1, steps.length - 1);
      setProcessingStatus(steps[step]);
    }, 4000);

    try {
      const formData = new FormData();
      uploadedFiles.forEach(f => formData.append('files', f));

      const res = await api.post('/interviews/upload-syllabus', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      clearInterval(stepTimer);
      setProcessingStatus('Ready');
      setProcessedData(res.data);
      setSelectedTopics(res.data.topics || []);
    } catch (err) {
      clearInterval(stepTimer);
      setError(err.response?.data?.detail || 'Failed to process material. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const handleStart = async () => {
    if (mode === 'normal') {
      if (!resume) { setError('Please upload a resume first'); return; }
      if (selectedSkills.length === 0) { setError('Select at least one skill'); return; }
    } else {
      if (!processedData) { setError('Please upload and process your syllabus material first.'); return; }
      if (selectedTopics.length === 0) { setError('Select at least one topic to be interviewed on.'); return; }
    }

    setError('');
    setStarting(true);
    try {
      const payload = {
        resume_id: resume ? resume.id : 0,
        difficulty: null,
        question_type: null,
        question_count: null,
        selected_skills: mode === 'normal' ? selectedSkills : [],
        mode,
        syllabus_id: mode === 'syllabus' ? processedData.syllabus_id : null,
        selected_topics: mode === 'syllabus' ? selectedTopics : null,
      };
      const res = await api.post('/interviews/start', payload);
      navigate(`/interview/${res.data.session_id || res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start interview');
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!resume && mode === 'normal') {
    return (
      <div className="max-w-md mx-auto mt-16 px-4">
        <div className="card text-center p-8 border-amber-200 bg-amber-50 shadow-sm">
          <AlertCircle size={48} className="text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-amber-900 mb-2">No Resume Uploaded</h2>
          <p className="text-amber-700 mb-6">Upload your resume so we can personalise the questions for Normal Mode.</p>
          <button onClick={() => navigate('/resume')} className="btn bg-amber-600 text-white hover:bg-amber-700 w-full shadow-sm">Upload Resume</button>
        </div>
      </div>
    );
  }

  const canStart = mode === 'normal'
    ? selectedSkills.length > 0
    : (processedData && selectedTopics.length > 0);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <Settings className="text-indigo-600" size={28} />
          Interview Setup
        </h1>
        <p className="text-slate-500 mt-2 text-base">
          Choose Normal Adaptive Mode for an open-ended interview based on your resume, or Syllabus Mode for a structured interview on any uploaded reference material.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      <div className="mb-8 flex space-x-4 border-b border-slate-200">
        <button
          className={`pb-4 px-2 text-sm font-medium border-b-2 transition-colors ${mode === 'normal' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
          onClick={() => { setMode('normal'); setError(''); }}
        >
          Normal (Adaptive) Mode
        </button>
        <button
          className={`pb-4 px-2 text-sm font-medium border-b-2 transition-colors ${mode === 'syllabus' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
          onClick={() => { setMode('syllabus'); setError(''); }}
        >
          Syllabus Mode
        </button>
      </div>

      <div className="space-y-6">
        {mode === 'normal' ? (
          /* Normal Mode Setup */
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Target Skills</h2>
                <p className="text-sm text-slate-500 mt-0.5">{selectedSkills.length} of {resume?.skills?.length || 0} selected</p>
              </div>
              <button
                className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 bg-transparent border-none cursor-pointer px-2 py-1 hover:bg-indigo-50 rounded transition-colors"
                onClick={() => setSelectedSkills(selectedSkills.length === resume?.skills?.length ? [] : [...(resume?.skills || [])])}
              >
                {selectedSkills.length === resume?.skills?.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="flex flex-wrap gap-2.5">
              {(resume?.skills || []).map(s => {
                const isSelected = selectedSkills.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() => toggleSkill(s)}
                    className={`px-4 py-2 text-sm font-medium rounded-full cursor-pointer transition-all border ${
                      isSelected
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-slate-50'
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Syllabus Mode Setup */
          <div className="space-y-4">
            {/* Upload Panel */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100">
                <BookOpen size={20} className="text-indigo-600 shrink-0" />
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Upload Syllabus / Reference Material</h2>
                  <p className="text-sm text-slate-500 mt-0.5">PDF, TXT, or DOCX files · Up to 20 MB each · Multiple files supported</p>
                </div>
              </div>

              {/* Drop area / file button */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl py-8 px-4 text-slate-500 hover:border-indigo-400 hover:bg-indigo-50 hover:text-indigo-600 transition-all cursor-pointer"
              >
                <UploadCloud size={32} />
                <span className="font-medium text-sm">Click to select files</span>
                <span className="text-xs">PDF, TXT, DOCX</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.docx"
                multiple
                className="hidden"
                onChange={handleFileSelect}
              />

              {/* Staged files list */}
              {uploadedFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Selected files</p>
                  {uploadedFiles.map(f => (
                    <div key={f.name} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200">
                      <FileText size={16} className="text-indigo-500 shrink-0" />
                      <span className="text-sm text-slate-700 flex-1 truncate">{f.name}</span>
                      <span className="text-xs text-slate-400">{(f.size / 1024).toFixed(0)} KB</span>
                      <button
                        type="button"
                        onClick={() => removeFile(f.name)}
                        className="text-slate-400 hover:text-red-500 transition-colors"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Process button */}
              {uploadedFiles.length > 0 && !processedData && (
                <button
                  type="button"
                  onClick={handleProcessMaterial}
                  disabled={processing}
                  className="mt-4 w-full btn btn-primary py-2.5 text-sm flex items-center justify-center gap-2"
                >
                  {processing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      {processingStatus}
                    </>
                  ) : (
                    <>
                      <UploadCloud size={16} />
                      Process Material
                    </>
                  )}
                </button>
              )}

              {processedData && (
                <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
                  Ready
                  <button
                    type="button"
                    onClick={() => { setProcessedData(null); setSelectedTopics([]); }}
                    className="ml-auto text-emerald-500 hover:text-emerald-700"
                    title="Reset and re-upload"
                  >
                    <X size={14} />
                  </button>
                </div>
              )}
            </div>


          </div>
        )}



        {/* Start Button */}
        <div className="pt-2">
          <button
            id="start-interview-btn"
            onClick={handleStart}
            disabled={starting || !canStart}
            className="btn btn-primary w-full py-3.5 text-base shadow-md group relative overflow-hidden"
          >
            {starting ? (
              <>
                <Loader2 size={18} className="animate-spin mr-2" />
                {mode === 'syllabus' ? 'Starting Syllabus Interview...' : 'Initializing Adaptive Engine...'}
              </>
            ) : (
              <>
                <Play size={20} className="mr-2" />
                <span className="font-semibold">Start {mode === 'syllabus' ? 'Syllabus Interview' : 'Open-Ended Interview'}</span>
                <ArrowRight size={18} className="absolute right-6 opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all duration-300" />
              </>
            )}
          </button>

          <p className="text-center text-sm text-slate-500 mt-4 flex items-center justify-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            {mode === 'syllabus'
              ? 'Questions will follow your selected topics sequentially, grounded in uploaded material.'
              : 'The interview continues until you choose to finish.'}
          </p>
        </div>
      </div>
    </div>
  );
}
