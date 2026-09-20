import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { Play, Settings, AlertCircle, ArrowRight, UploadCloud, FileText, X, CheckSquare, Square, Loader2, BookOpen, Briefcase, BarChart2 } from 'lucide-react';

export default function InterviewSetup() {
  const [resume, setResume] = useState(null);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');
  
  const [searchParams, setSearchParams] = useSearchParams();
  const currentMode = searchParams.get('mode') || 'normal';

  // Mode Selection
  const setMode = (mode) => {
    setSearchParams({ mode });
    setError('');
  };

  // Job-Specific Mode state
  const [jdText, setJdText] = useState('');
  const [jdTitle, setJdTitle] = useState('');
  const [isExtractingJd, setIsExtractingJd] = useState(false);
  const jdFileInputRef = useRef(null);
  const [jdAnalysisData, setJdAnalysisData] = useState(null);
  const [analyzingJd, setAnalyzingJd] = useState(false);

  // Syllabus Mode state
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [processedData, setProcessedData] = useState(null);
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

  const handleJdFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.pdf', '.txt', '.md'].includes(ext)) {
      setError('Only PDF, TXT, and MD files are supported for Job Descriptions.');
      return;
    }
    
    setError('');
    setIsExtractingJd(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.post('/interviews/extract-jd', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setJdText(res.data.extracted_text);
      if (!jdTitle && file.name) {
        // Option to prefill title with filename without extension
        setJdTitle(file.name.slice(0, file.name.lastIndexOf('.')));
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to extract Job Description from file.');
    } finally {
      setIsExtractingJd(false);
    }
    e.target.value = '';
  };

  const handleAnalyzeJd = async () => {
    if (!resume) { setError('Please upload a resume first'); return; }
    if (!jdText.trim()) { setError('Please provide a Job Description'); return; }
    setError('');
    setAnalyzingJd(true);
    setJdAnalysisData(null);
    try {
      const payload = {
        resume_id: resume.id,
        job_description_text: jdText,
        job_description_title: jdTitle,
      };
      const res = await api.post('/interviews/analyze-jd', payload);
      setJdAnalysisData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze Job Description');
    } finally {
      setAnalyzingJd(false);
    }
  };

  const handleStart = async () => {
    if (currentMode === 'normal') {
      if (!resume) { setError('Please upload a resume first'); return; }
      if (selectedSkills.length === 0) { setError('Select at least one skill'); return; }
    } else if (currentMode === 'job_specific') {
      if (!resume) { setError('Please upload a resume first'); return; }
      if (!jdAnalysisData) { setError('Please analyze the Job Description first'); return; }
    } else if (currentMode === 'syllabus') {
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
        selected_skills: currentMode === 'normal' ? selectedSkills : [],
        mode: currentMode,
        syllabus_id: currentMode === 'syllabus' ? processedData.syllabus_id : null,
        selected_topics: currentMode === 'syllabus' ? selectedTopics : null,
        job_description_text: currentMode === 'job_specific' ? jdText : null,
        job_description_title: currentMode === 'job_specific' ? (jdTitle || jdAnalysisData?.inferred_title) : null,
        analysis_id: currentMode === 'job_specific' ? jdAnalysisData?.analysis_id : null,
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

  // Determine if we can start
  let canStart = false;
  if (currentMode === 'normal') {
    canStart = selectedSkills.length > 0;
  } else if (currentMode === 'job_specific') {
    canStart = jdAnalysisData !== null;
  } else if (currentMode === 'syllabus') {
    canStart = processedData && selectedTopics.length > 0;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-3">
          Select Interview Mode
        </h1>
        <p className="text-slate-500 text-lg max-w-2xl mx-auto">
          Choose how you want to be interviewed. Each mode uses a tailored adaptive engine.
        </p>
      </div>

      {/* Mode Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        
        {/* General Technical */}
        <button
          onClick={() => setMode('normal')}
          className={`flex flex-col items-center text-center p-6 rounded-2xl border-2 transition-all ${
            currentMode === 'normal' 
            ? 'border-indigo-600 bg-indigo-50 shadow-md transform scale-[1.02]' 
            : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'
          }`}
        >
          <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${currentMode === 'normal' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
            <Settings size={24} />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">General Technical</h3>
          <p className="text-xs text-slate-500">Adaptive open-ended interview based on your resume skills.</p>
        </button>

        {/* Job-Specific */}
        <button
          onClick={() => setMode('job_specific')}
          className={`flex flex-col items-center text-center p-6 rounded-2xl border-2 transition-all ${
            currentMode === 'job_specific' 
            ? 'border-indigo-600 bg-indigo-50 shadow-md transform scale-[1.02]' 
            : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'
          }`}
        >
          <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${currentMode === 'job_specific' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
            <Briefcase size={24} />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Job-Specific</h3>
          <p className="text-xs text-slate-500">Tailored to a specific job description to test relevant skills.</p>
        </button>

        {/* Syllabus-Based */}
        <button
          onClick={() => setMode('syllabus')}
          className={`flex flex-col items-center text-center p-6 rounded-2xl border-2 transition-all ${
            currentMode === 'syllabus' 
            ? 'border-indigo-600 bg-indigo-50 shadow-md transform scale-[1.02]' 
            : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'
          }`}
        >
          <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${currentMode === 'syllabus' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
            <BookOpen size={24} />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Syllabus-Based</h3>
          <p className="text-xs text-slate-500">Structured interview grounded in custom uploaded reference material.</p>
        </button>

        {/* Previous Performance - Hidden per user request for now
        <button
          onClick={() => setMode('previous_performance')}
          className={`flex flex-col items-center text-center p-6 rounded-2xl border-2 transition-all ${
            currentMode === 'previous_performance' 
            ? 'border-indigo-600 bg-indigo-50 shadow-md transform scale-[1.02]' 
            : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'
          }`}
        >
          <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${currentMode === 'previous_performance' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
            <BarChart2 size={24} />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Targeted Weakness</h3>
          <p className="text-xs text-slate-500">Start where you left off based on your historical performance.</p>
        </button>
        */}
      </div>

      {/* Main Configuration Area */}
      <div className="max-w-2xl mx-auto">
        
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm font-medium flex items-center gap-2">
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        {/* Missing Resume Warning for Normal & Job-Specific */}
        {!resume && (currentMode === 'normal' || currentMode === 'job_specific') && (
          <div className="card text-center p-8 border-amber-200 bg-amber-50 shadow-sm mb-6">
            <AlertCircle size={48} className="text-amber-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-amber-900 mb-2">No Resume Uploaded</h2>
            <p className="text-amber-700 mb-6">A resume is required for {currentMode === 'normal' ? 'Normal Mode' : 'Job-Specific Mode'} to personalize your interview.</p>
            <button onClick={() => navigate('/resume')} className="btn bg-amber-600 text-white hover:bg-amber-700 shadow-sm">Upload Resume</button>
          </div>
        )}

        {/* Mode specific configuration blocks */}
        
        {currentMode === 'previous_performance' && (
          <div className="card text-center p-12 border-indigo-200 bg-indigo-50 shadow-sm">
            <BarChart2 size={48} className="text-indigo-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-indigo-900 mb-2">Coming Soon</h2>
            <p className="text-indigo-700 font-medium">This mode is a further enhancement!</p>
          </div>
        )}

        {currentMode === 'normal' && resume && (
          <div className="card p-6 mb-6">
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2"><Settings size={20} className="text-indigo-600"/> Target Skills</h2>
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
        )}

        {currentMode === 'job_specific' && resume && (
          <div className="card p-6 mb-6">
            <div className="flex items-center gap-2 mb-6 pb-4 border-b border-slate-100">
              <Briefcase size={20} className="text-indigo-600"/>
              <h2 className="text-lg font-bold text-slate-900">Job Description Details</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <input
                  ref={jdFileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md"
                  className="hidden"
                  onChange={handleJdFileSelect}
                />
                
                {!jdText ? (
                  <div 
                    onClick={() => !isExtractingJd && jdFileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${isExtractingJd ? 'border-indigo-300 bg-indigo-50/50' : 'border-slate-300 hover:border-indigo-500 hover:bg-slate-50'}`}
                  >
                    <div className="flex flex-col items-center justify-center">
                      {isExtractingJd ? (
                        <>
                          <Loader2 size={32} className="text-indigo-500 animate-spin mb-3" />
                          <p className="text-sm font-semibold text-slate-700">Extracting Job Description...</p>
                        </>
                      ) : (
                        <>
                          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mb-3">
                            <UploadCloud size={24} className="text-indigo-600" />
                          </div>
                          <p className="text-base font-bold text-slate-700 mb-1">Upload Job Description</p>
                          <p className="text-sm text-slate-500 mb-4">Support for PDF, TXT, or MD files</p>
                          <button type="button" className="btn bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-sm py-1.5 pointer-events-none">
                            Browse Files
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="border border-emerald-200 bg-emerald-50 rounded-xl p-5 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 flex-shrink-0">
                        <CheckSquare size={20} />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-800">Job Description Uploaded</h4>
                        <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                           Ready for analysis. {jdTitle ? `Title: ${jdTitle}` : ''}
                        </p>
                      </div>
                    </div>
                    <button 
                      type="button" 
                      onClick={() => { setJdText(''); setJdTitle(''); setJdAnalysisData(null); }}
                      className="text-xs font-semibold text-slate-500 hover:text-red-600 transition-colors ml-4"
                    >
                      Remove
                    </button>
                  </div>
                )}
                
                <p className="text-xs text-slate-500 mt-3 flex items-center gap-1.5">
                   <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 flex-shrink-0"></span>
                   We will analyze the uploaded job description against your resume to prioritize what gets asked.
                </p>

                <div className="mt-4 flex justify-end">
                  <button
                    type="button"
                    onClick={handleAnalyzeJd}
                    disabled={analyzingJd || !jdText.trim()}
                    className="btn bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 text-sm px-6 py-2"
                  >
                    {analyzingJd ? (
                      <><Loader2 size={16} className="animate-spin mr-2 inline" /> Analyzing...</>
                    ) : (
                      'Analyze Job Description'
                    )}
                  </button>
                </div>
              </div>

              {jdAnalysisData && (
                <div className="mt-6 p-5 border-2 border-indigo-100 bg-indigo-50/50 rounded-xl animate-[fadeIn_0.3s_ease-out]">
                  <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                    <CheckSquare size={18} className="text-indigo-600" />
                    Job Match Analysis
                  </h3>
                  
                  {/* Matching Skills */}
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-emerald-800 mb-2">Matching Skills (Eligible)</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(jdAnalysisData.matching_skills).map(([skill, rel]) => (
                        <span key={skill} className="px-3 py-1 text-xs font-medium bg-emerald-100 text-emerald-800 rounded-md border border-emerald-200">
                          {skill} <span className="opacity-60 ml-1">({rel})</span>
                        </span>
                      ))}
                      {Object.keys(jdAnalysisData.matching_skills).length === 0 && (
                        <span className="text-sm text-slate-500 italic">No matching skills found in resume.</span>
                      )}
                    </div>
                  </div>

                  {/* JD-Only Skills */}
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-amber-800 mb-2">Missing from Resume (JD-Only) (Eligible)</h4>
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysisData.jd_only_skills.map(skill => (
                        <span key={skill} className="px-3 py-1 text-xs font-medium bg-amber-100 text-amber-800 rounded-md border border-amber-200">
                          {skill}
                        </span>
                      ))}
                      {jdAnalysisData.jd_only_skills.length === 0 && (
                        <span className="text-sm text-slate-500 italic">None.</span>
                      )}
                    </div>
                  </div>

                  {/* Non-Matching Resume Skills */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-500 mb-2">Unrelated Resume Skills (Excluded)</h4>
                    <div className="flex flex-wrap gap-2">
                      {jdAnalysisData.non_matching_skills.map(skill => (
                        <span key={skill} className="px-3 py-1 text-xs font-medium bg-slate-100 text-slate-400 rounded-md border border-slate-200 line-through">
                          {skill}
                        </span>
                      ))}
                      {jdAnalysisData.non_matching_skills.length === 0 && (
                        <span className="text-sm text-slate-500 italic">None.</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {currentMode === 'syllabus' && (
          <div className="space-y-4 mb-6">
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100">
                <BookOpen size={20} className="text-indigo-600 shrink-0" />
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Upload Syllabus / Reference Material</h2>
                  <p className="text-sm text-slate-500 mt-0.5">PDF, TXT, or DOCX files · Up to 20 MB each</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl py-8 px-4 text-slate-500 hover:border-indigo-400 hover:bg-indigo-50 hover:text-indigo-600 transition-all cursor-pointer"
              >
                <UploadCloud size={32} />
                <span className="font-medium text-sm">Click to select files</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.docx"
                multiple
                className="hidden"
                onChange={handleFileSelect}
              />

              {uploadedFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                  {uploadedFiles.map(f => (
                    <div key={f.name} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200">
                      <FileText size={16} className="text-indigo-500 shrink-0" />
                      <span className="text-sm text-slate-700 flex-1 truncate">{f.name}</span>
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
                  Ready to start
                  <button
                    type="button"
                    onClick={() => { setProcessedData(null); setSelectedTopics([]); }}
                    className="ml-auto text-emerald-500 hover:text-emerald-700"
                    title="Reset"
                  >
                    <X size={14} />
                  </button>
                </div>
              )}
            </div>
            
            {processedData && (
              <div className="card p-6 animate-[fadeIn_0.3s_ease-out]">
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-100">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Detected Topics</h2>
                    <p className="text-sm text-slate-500 mt-0.5">Select the topics you want to be interviewed on</p>
                  </div>
                  <button
                    className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 bg-transparent border-none cursor-pointer"
                    onClick={() => setSelectedTopics(selectedTopics.length === processedData.topics.length ? [] : [...processedData.topics])}
                  >
                    {selectedTopics.length === processedData.topics.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {processedData.topics.map(t => {
                    const isSelected = selectedTopics.includes(t);
                    return (
                      <div 
                        key={t}
                        onClick={() => toggleTopic(t)}
                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                          isSelected ? 'border-indigo-600 bg-indigo-50/50' : 'border-slate-100 hover:border-indigo-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className={`mt-0.5 ${isSelected ? 'text-indigo-600' : 'text-slate-300'}`}>
                          {isSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                        </div>
                        <span className={`text-sm font-medium leading-tight ${isSelected ? 'text-slate-900' : 'text-slate-600'}`}>
                          {t}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Start Button Area */}
        {currentMode !== 'previous_performance' && (
          <div className="pt-2">
            <button
              id="start-interview-btn"
              onClick={handleStart}
              disabled={starting || !canStart}
              className="btn btn-primary w-full py-4 text-base shadow-lg group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {starting ? (
                <>
                  <Loader2 size={20} className="animate-spin mr-2" />
                  {currentMode === 'job_specific' ? 'Analyzing Job Description...' : 'Initializing Engine...'}
                </>
              ) : (
                <>
                  <Play size={20} className="mr-2" />
                  <span className="font-semibold text-lg tracking-wide">
                    {currentMode === 'syllabus' ? 'Start Syllabus Interview' : 'Start Interview'}
                  </span>
                  <ArrowRight size={20} className="absolute right-6 opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all duration-300" />
                </>
              )}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
