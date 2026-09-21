import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Play, Settings, AlertCircle, ArrowRight, Briefcase } from 'lucide-react';

export default function InterviewSetup() {
  const [resume, setResume] = useState(null);
  const [hasJD, setHasJD] = useState(false);
  const [targetSkills, setTargetSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get('/resumes/current'),
      api.get('/job-descriptions/current').catch(() => null),
      api.get('/job-descriptions/mapping').catch(() => null),
    ])
      .then(([res, jdRes, mapRes]) => {
        setResume(res.data);
        setHasJD(!!jdRes?.data);
        const skills = mapRes?.data?.interview_skills?.length > 0
          ? mapRes.data.interview_skills
          : (res.data.skills || []);
        setTargetSkills(skills);
        setSelectedSkills(skills);
      })
      .catch(() => setError('Please upload a resume first'))
      .finally(() => setLoading(false));
  }, []);

  const toggleSkill = (skill) => {
    setSelectedSkills(prev =>
      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
    );
  };

  const handleStart = async () => {
    if (!resume) { setError('Please upload a resume first'); return; }
    if (selectedSkills.length === 0) { setError('Select at least one skill'); return; }

    setError('');
    setStarting(true);
    try {
      const res = await api.post('/interviews/start', {
        resume_id: resume.id,
        difficulty: null,
        question_type: null,
        question_count: null,
        selected_skills: selectedSkills,
      });
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

  if (!resume) {
    return (
      <div className="max-w-md mx-auto mt-16 px-4">
        <div className="card text-center p-8 border-amber-200 bg-amber-50 shadow-sm">
          <AlertCircle size={48} className="text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-amber-900 mb-2">No Resume Uploaded</h2>
          <p className="text-amber-700 mb-6">You need to upload your resume before starting an interview so we can personalize the questions.</p>
          <button onClick={() => navigate('/resume')} className="btn bg-amber-600 text-white hover:bg-amber-700 w-full shadow-sm">Upload Resume</button>
        </div>
      </div>
    );
  }

  if (!hasJD) {
    return (
      <div className="max-w-md mx-auto mt-16 px-4">
        <div className="card text-center p-8 border-blue-200 bg-blue-50 shadow-sm">
          <Briefcase size={48} className="text-blue-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-blue-900 mb-2">No Job Description Uploaded</h2>
          <p className="text-blue-700 mb-6">
            The adaptive interview engine targets skills from your job description. Please upload a JD so we can focus on what matters for your role.
          </p>
          <button onClick={() => navigate('/resume')} className="btn bg-blue-600 text-white hover:bg-blue-700 w-full shadow-sm">Upload Job Description</button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <Settings className="text-indigo-600" size={28} />
          Interview Focus Areas
        </h1>
        <p className="text-slate-500 mt-2 text-base">Select the skills you want the adaptive engine to evaluate. The AI will dynamically adjust difficulty, question types, and Bloom's taxonomy levels as you answer.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Skills Selection */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Target Skills</h2>
              <p className="text-sm text-slate-500 mt-0.5">{selectedSkills.length} of {targetSkills.length} selected</p>
            </div>
            <button
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 bg-transparent border-none cursor-pointer px-2 py-1 hover:bg-indigo-50 rounded transition-colors"
              onClick={() => setSelectedSkills(selectedSkills.length === targetSkills.length ? [] : [...targetSkills])}
            >
              {selectedSkills.length === targetSkills.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>
          
          <div className="flex flex-wrap gap-2.5">
            {targetSkills.map(s => {
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

        {/* Start Button */}
        <div className="pt-4">
          <button
            onClick={handleStart}
            disabled={starting || selectedSkills.length === 0}
            className="btn btn-primary w-full py-3.5 text-base shadow-md group relative overflow-hidden"
          >
            {starting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-t-2 border-white mr-2"></div>
                Initializing Adaptive Engine...
              </>
            ) : (
              <>
                <Play size={20} className="mr-2" />
                <span className="font-semibold">Start Open-Ended Interview</span>
                <ArrowRight size={18} className="absolute right-6 opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all duration-300" />
              </>
            )}
          </button>
          
          <p className="text-center text-sm text-slate-500 mt-4 flex items-center justify-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            The interview continues until you choose to finish.
          </p>
        </div>
      </div>
    </div>
  );
}
