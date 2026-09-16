import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  BookOpen,
  UploadCloud,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Play,
  ArrowRight,
  Loader2,
  Sparkles,
  Layers,
  Clock,
  RotateCcw,
} from 'lucide-react';

export default function SyllabusUpload() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [processedData, setProcessedData] = useState(null);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user already has an active syllabus
    api.get('/interviews/syllabus/current')
      .then(res => {
        if (res.data?.syllabus_id) {
          setProcessedData(res.data);
          setSelectedTopics(res.data.topics || []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target?.files || e.dataTransfer?.files || []);
    if (!files.length) return;

    const allowed = ['.pdf', '.txt', '.docx'];
    const valid = files.filter(f => {
      const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
      return allowed.includes(ext);
    });

    if (valid.length !== files.length) {
      setError('Only PDF, TXT, and DOCX files are supported.');
    } else {
      setError('');
    }

    setUploadedFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...valid.filter(f => !names.has(f.name))];
    });

    if (e.target) e.target.value = '';
  };

  const removeFile = (name) => {
    setUploadedFiles(prev => prev.filter(f => f.name !== name));
    if (uploadedFiles.length <= 1) {
      setProcessedData(null);
      setSelectedTopics([]);
    }
  };

  const handleProcessMaterial = async () => {
    if (uploadedFiles.length === 0) {
      setError('Please upload at least one syllabus file first.');
      return;
    }
    setError('');
    setProcessing(true);
    setProcessedData(null);
    setSelectedTopics([]);

    const steps = [
      'Extracting document text...',
      'Inferring subject and key topics...',
      'Creating isolated vector knowledge base...',
      'Finalizing syllabus RAG...',
    ];
    let step = 0;
    setProcessingStatus(steps[step]);
    const interval = setInterval(() => {
      step = Math.min(step + 1, steps.length - 1);
      setProcessingStatus(steps[step]);
    }, 1500);

    try {
      const formData = new FormData();
      uploadedFiles.forEach(f => formData.append('files', f));

      const res = await api.post('/interviews/upload-syllabus', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      clearInterval(interval);
      setProcessingStatus('Ready');
      setProcessedData(res.data);
      setSelectedTopics(res.data.topics || []);
    } catch (err) {
      clearInterval(interval);
      setError(err.response?.data?.detail || 'Failed to process syllabus. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const toggleTopic = (topic) => {
    setSelectedTopics(prev =>
      prev.includes(topic) ? prev.filter(t => t !== topic) : [...prev, topic]
    );
  };

  const selectAllTopics = () => {
    if (processedData?.topics) {
      if (selectedTopics.length === processedData.topics.length) {
        setSelectedTopics([]);
      } else {
        setSelectedTopics([...processedData.topics]);
      }
    }
  };

  const handleStartInterview = async () => {
    if (!processedData?.syllabus_id) {
      setError('Please upload and process syllabus material first.');
      return;
    }
    if (selectedTopics.length === 0) {
      setError('Please select at least one topic for your interview.');
      return;
    }

    setError('');
    setStarting(true);
    try {
      const payload = {
        mode: 'syllabus',
        syllabus_id: processedData.syllabus_id,
        selected_topics: selectedTopics,
        resume_id: null,
      };
      const res = await api.post('/interviews/start', payload);
      navigate(`/interview/${res.data.session_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start syllabus interview');
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

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
            <BookOpen size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Syllabus & Course Interview
            </h1>
            <p className="text-slate-500 mt-1 text-sm">
              Upload your course syllabus, lecture slides, or exam reference material. Questions are strictly source-grounded in your documents.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium flex items-center gap-3">
          <AlertCircle size={18} className="shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload & Files */}
        <div className="lg:col-span-6 space-y-6">
          <div className="card p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <UploadCloud size={18} className="text-indigo-600" />
                Upload Course Material
              </h2>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
                PDF · DOCX · TXT
              </span>
            </div>

            {/* Dropzone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
              onDrop={(e) => { e.preventDefault(); e.stopPropagation(); handleFileSelect(e); }}
              className="group border-2 border-dashed border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/50 rounded-xl p-8 text-center cursor-pointer transition-all duration-200"
            >
              <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                <UploadCloud size={24} />
              </div>
              <p className="font-semibold text-slate-700 text-sm">
                Click or drag files here
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Upload university syllabus, lecture notes, or reference docs (up to 20 MB each)
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                multiple
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>

            {/* Uploaded Files List */}
            {uploadedFiles.length > 0 && (
              <div className="mt-5 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider px-1">
                  <span>Selected Files ({uploadedFiles.length})</span>
                  <span>Size</span>
                </div>
                {uploadedFiles.map((file) => (
                  <div
                    key={file.name}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/70 hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 flex-1">
                      <FileText size={16} className="text-indigo-600 shrink-0" />
                      <span className="text-sm font-medium text-slate-800 truncate">{file.name}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 ml-3">
                      <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(0)} KB</span>
                      <button
                        type="button"
                        onClick={() => removeFile(file.name)}
                        className="text-slate-400 hover:text-red-500 p-1 rounded transition-colors"
                        title="Remove file"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Process Button */}
            {uploadedFiles.length > 0 && !processedData && (
              <button
                type="button"
                onClick={handleProcessMaterial}
                disabled={processing}
                className="mt-5 w-full btn btn-primary py-3 text-sm flex items-center justify-center gap-2 rounded-xl font-semibold shadow-sm"
              >
                {processing ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>{processingStatus}</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Analyze & Extract Topics</span>
                  </>
                )}
              </button>
            )}

            {/* Processed Success Badge with Timing Metrics */}
            {processedData && (
              <div className="mt-5 p-4 rounded-xl bg-emerald-50/80 border border-emerald-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-emerald-800 font-semibold text-sm">
                    <CheckCircle2 size={18} className="text-emerald-600" />
                    <span>Document Processed Successfully</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setProcessedData(null);
                      setSelectedTopics([]);
                      setUploadedFiles([]);
                    }}
                    className="text-xs text-emerald-700 hover:text-emerald-900 font-medium flex items-center gap-1"
                    title="Reset and upload new syllabus"
                  >
                    <RotateCcw size={12} />
                    <span>Reset</span>
                  </button>
                </div>

                {/* Stage Profiling Metrics Badge */}
                {processedData.metrics && (
                  <div className="mt-2 pt-2 border-t border-emerald-200/60 flex flex-wrap items-center gap-3 text-xs text-emerald-700">
                    <span className="flex items-center gap-1">
                      <Clock size={12} /> Total: {processedData.metrics.total_elapsed_sec}s
                    </span>
                    <span>• Extract: {processedData.metrics.stages?.extraction_sec}s</span>
                    <span>• Topics: {processedData.metrics.stages?.topic_inference_sec}s</span>
                    <span>• Vector DB: {processedData.metrics.stages?.embedding_and_chroma_sec}s</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Inferred Topics & Start Session */}
        <div className="lg:col-span-6 space-y-6">
          <div className="card p-6 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between min-h-[380px]">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
                <div>
                  <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Layers size={18} className="text-indigo-600" />
                    Syllabus Topics
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {processedData
                      ? `${selectedTopics.length} of ${processedData.topics?.length || 0} topics selected`
                      : 'Topics will appear here once processed'}
                  </p>
                </div>
                {processedData?.topics?.length > 0 && (
                  <button
                    type="button"
                    onClick={selectAllTopics}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-transparent border-none cursor-pointer px-2 py-1 hover:bg-indigo-50 rounded transition-colors"
                  >
                    {selectedTopics.length === processedData.topics.length ? 'Deselect All' : 'Select All'}
                  </button>
                )}
              </div>

              {/* Subject Tag */}
              {processedData?.subject && (
                <div className="mb-4 px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-semibold uppercase">Course Subject:</span>
                  <span className="text-sm font-bold text-slate-800">{processedData.subject}</span>
                </div>
              )}

              {/* Topics Grid */}
              {processedData?.topics?.length > 0 ? (
                <div className="flex flex-wrap gap-2 pt-1 max-h-64 overflow-y-auto pr-1">
                  {processedData.topics.map((topic) => {
                    const isSelected = selectedTopics.includes(topic);
                    return (
                      <button
                        key={topic}
                        type="button"
                        onClick={() => toggleTopic(topic)}
                        className={`px-3.5 py-1.5 text-xs font-medium rounded-full cursor-pointer transition-all border ${
                          isSelected
                            ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-slate-50'
                        }`}
                      >
                        {topic}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-center text-slate-400">
                  <Layers size={36} className="text-slate-300 mb-2" />
                  <p className="text-sm font-medium text-slate-500">No topics detected yet</p>
                  <p className="text-xs text-slate-400 max-w-xs mt-1">
                    Upload your course document on the left and click &quot;Analyze &amp; Extract Topics&quot; to begin.
                  </p>
                </div>
              )}
            </div>

            {/* Start Button */}
            <div className="pt-6 border-t border-slate-100 mt-6">
              <button
                id="start-syllabus-interview-btn"
                type="button"
                onClick={handleStartInterview}
                disabled={starting || !processedData || selectedTopics.length === 0}
                className="btn btn-primary w-full py-3.5 text-sm font-bold rounded-xl shadow-md flex items-center justify-center gap-2 group transition-all duration-200"
              >
                {starting ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Preparing Adaptive Session...</span>
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    <span>Start Syllabus Interview</span>
                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>

              <div className="mt-3 flex items-center justify-center gap-1.5 text-xs text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>Source-grounded questions with adaptive difficulty progression</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
