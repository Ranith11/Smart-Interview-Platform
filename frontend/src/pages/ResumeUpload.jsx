import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Upload, FileText, Trash2, Eye, Check, UploadCloud, ChevronRight } from 'lucide-react';

export default function ResumeUpload() {
  const [resume, setResume] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const fileRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/resumes/current')
      .then(res => setResume(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('File too large (max 5MB)');
      return;
    }

    setError('');
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResume(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleDelete = async () => {
    if (!resume) return;
    try {
      await api.delete(`/resumes/${resume.id}`);
      setResume(null);
    } catch {
      setError('Failed to delete resume');
    }
  };

  const categorizeSkills = (skills) => {
    const categories = {
      'CORE LANGUAGES': ['java', 'python', 'c++', 'c#', 'typescript', 'javascript', 'sql', 'html', 'css', 'go', 'ruby'],
      'WEB & FRAMEWORKS': ['react', 'node', 'flask', 'next', 'tailwind', 'django', 'spring', 'express', 'vue', 'angular'],
      'DATABASES & SYSTEMS': ['postgres', 'redis', 'prisma', 'kafka', 'rest', 'mongodb', 'mysql', 'api'],
      'DEVOPS & TESTING': ['docker', 'aws', 'junit', 'git', 'jest', 'cypress', 'kubernetes', 'gcp', 'azure', 'ci/cd']
    };

    const result = {
      'CORE LANGUAGES': [],
      'WEB & FRAMEWORKS': [],
      'DATABASES & SYSTEMS': [],
      'DEVOPS & TESTING': [],
      'OTHER COMPETENCIES': []
    };

    if (!skills) return result;

    skills.forEach(skill => {
      const s = skill.toLowerCase();
      let matched = false;
      for (const [cat, keywords] of Object.entries(categories)) {
        if (keywords.some(k => s.includes(k))) {
          result[cat].push(skill);
          matched = true;
          break;
        }
      }
      if (!matched) result['OTHER COMPETENCIES'].push(skill);
    });

    return result;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const groupedSkills = categorizeSkills(resume?.skills);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
            Resume Intelligence
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Your Professional Resume</h1>
          <p className="text-slate-500 mt-1">Parsed automatically to generate personalized interview scenarios.</p>
        </div>
        {resume && (
          <div className="mt-4 md:mt-0 flex flex-col md:items-end gap-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium">
              <Check size={16} /> Active Parsing Engine v2.4
            </div>
            <button onClick={() => navigate('/setup')} className="btn btn-primary">
              Continue to Interview
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      {!resume ? (
        /* Empty State Upload Area */
        <label className="flex flex-col items-center justify-center w-full h-72 border-2 border-dashed border-slate-300 rounded-xl bg-white hover:bg-slate-50 transition-colors cursor-pointer relative overflow-hidden group">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading ? (
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-t-2 border-indigo-600 mb-4"></div>
              <p className="text-lg font-semibold text-slate-900">Uploading and parsing...</p>
              <p className="text-sm text-slate-500 mt-1">This takes a few moments.</p>
            </div>
          ) : (
            <div className="flex flex-col items-center text-center p-6">
              <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mb-4 group-hover:bg-indigo-100 transition-colors">
                <UploadCloud size={32} className="text-indigo-600" />
              </div>
              <p className="text-xl font-semibold text-slate-900 mb-1">Upload your resume</p>
              <p className="text-sm text-slate-500 mb-6">Supports PDF format up to 5MB</p>
              <div className="btn btn-secondary">Browse Files</div>
            </div>
          )}
        </label>
      ) : (
        <div className="space-y-6">
          {/* File Info Card */}
          <div className="card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 flex-shrink-0">
                <FileText size={24} />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-slate-900 text-base">{resume.filename || 'Resume.pdf'}</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-700">Verified</span>
                </div>
                <div className="text-sm text-slate-500 flex items-center gap-2">
                  <span>{resume.page_count || 1} page</span>
                  <span className="text-slate-300">•</span>
                  <span>Parsed {resume.uploaded_at ? new Date(resume.uploaded_at).toLocaleDateString() : new Date().toLocaleDateString()}</span>
                  <span className="text-slate-300">•</span>
                  <span className="text-indigo-600 font-medium">86% confidence</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <label className="btn btn-secondary cursor-pointer flex-1 sm:flex-none justify-center">
                <Upload size={16} /> Replace
                <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
              </label>
              <button onClick={handleDelete} className="btn bg-white border border-slate-200 text-red-600 hover:bg-red-50 hover:border-red-200 flex-1 sm:flex-none justify-center shadow-sm">
                <Trash2 size={16} /> Delete
              </button>
            </div>
          </div>

          {/* Extracted Competencies */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">Extracted Competencies</h2>
                <p className="text-sm text-slate-500 mt-1">Categorized for interview question weighting</p>
              </div>
              <div className="px-3 py-1 bg-slate-100 text-slate-700 text-sm font-semibold rounded-lg">
                {resume.skills?.length || 0} Detected
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(groupedSkills).map(([category, skills]) => {
                if (skills.length === 0) return null;
                
                let badgeClass = "badge-primary";
                if (category === 'DATABASES & SYSTEMS') badgeClass = "badge-success";
                else if (category === 'DEVOPS & TESTING') badgeClass = "badge-warning";
                else if (category === 'OTHER COMPETENCIES') badgeClass = "bg-slate-100 text-slate-700";

                return (
                  <div key={category} className="border border-slate-100 bg-slate-50/50 rounded-lg p-4">
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">{category}</div>
                    <div className="flex flex-wrap gap-2">
                      {skills.map(s => (
                        <span key={s} className={`badge ${badgeClass} px-2.5 py-1 text-sm`}>
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Key Engineering Projects */}
          {resume.projects && resume.projects.length > 0 && (
            <div className="card p-6">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">Key Engineering Projects</h2>
                <p className="text-sm text-slate-500 mt-1">Highlighted projects used to formulate architecture questions</p>
              </div>
              
              <div className="space-y-4">
                {resume.projects.map((p, i) => (
                  <div key={i} className="border border-slate-200 rounded-lg p-5 bg-white">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-base font-semibold text-slate-900">{p.name || `Project ${i + 1}`}</h3>
                    </div>
                    <p className="text-sm text-slate-600 mb-4 leading-relaxed">
                      {p.description}
                    </p>
                    {p.technologies && p.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {p.technologies.map(t => (
                          <span key={t} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Experience */}
          {resume.experience && resume.experience.length > 0 && (
            <div className="card p-6">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">Experience & Career History</h2>
                <p className="text-sm text-slate-500 mt-1">Extracted professional chronology</p>
              </div>

              <div className="space-y-6">
                {resume.experience.map((exp, i) => (
                  <div key={i} className="relative pl-6 border-l-2 border-indigo-100 pb-2 last:pb-0 last:border-transparent">
                    <div className="absolute w-3 h-3 bg-indigo-600 rounded-full -left-[7px] top-1.5 ring-4 ring-white"></div>
                    <div className="mb-1">
                      <h3 className="text-base font-semibold text-slate-900">{exp.role}</h3>
                    </div>
                    {exp.description && (
                      <ul className="mt-3 space-y-1.5 list-disc list-inside text-sm text-slate-600">
                        {exp.description.split('.').filter(Boolean).map((sentence, idx) => (
                          <li key={idx}>{sentence.trim()}.</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
