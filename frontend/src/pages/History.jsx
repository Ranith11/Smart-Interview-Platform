import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Clock, FileText, ChevronRight, CheckCircle2 } from 'lucide-react';

export default function History() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/interviews/history')
      .then(res => setSessions(res.data))
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  const getScoreTextColor = (score) => {
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-amber-500';
    if (score >= 40) return 'text-orange-500';
    return 'text-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Interview History</h1>
        <p className="text-slate-500 mt-1 text-base">Review your past interview sessions and track progress</p>
      </div>

      {sessions.length === 0 ? (
        <div className="card text-center p-12 bg-slate-50 border-dashed border-slate-200">
          <Clock size={48} className="text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-700 mb-2">No interviews yet</h3>
          <p className="text-slate-500 mb-6">Start your first interview to see it here.</p>
          <Link to="/setup" className="btn btn-primary shadow-sm">Start Interview</Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="divide-y divide-slate-100">
            {sessions.map(s => (
              <Link
                key={s.id}
                to={s.status === 'completed' ? `/results/${s.id}` : `/interview/${s.id}`}
                className="flex items-center justify-between p-5 hover:bg-slate-50 transition-colors no-underline group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center flex-shrink-0 border border-indigo-100">
                    <FileText size={22} className="text-indigo-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="font-bold text-slate-900 capitalize">{s.difficulty}</span>
                      <span className="text-slate-300">•</span>
                      <span className="text-sm font-semibold text-slate-500 capitalize">{s.question_type.replace('_', ' ')}</span>
                      {s.completion_reason && (
                        <>
                          <span className="text-slate-300">•</span>
                          <span className="badge bg-slate-100 text-slate-600 capitalize text-[10px]">{s.completion_reason.replace(/_/g, ' ')}</span>
                        </>
                      )}
                    </div>
                    <div className="text-sm font-medium text-slate-500 mb-2">
                      {new Date(s.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      <span className="mx-2">•</span>
                      {s.questions_answered} {s.question_count > 0 ? `/ ${s.question_count}` : ''} answered
                    </div>
                    {s.is_adaptive !== false && s.selected_skills && s.selected_skills.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {s.selected_skills.slice(0, 4).map(sk => (
                          <span key={sk} className="text-[11px] font-semibold px-2 py-0.5 bg-slate-100 rounded-md border border-slate-200 text-slate-600">{sk}</span>
                        ))}
                        {s.selected_skills.length > 4 && <span className="text-[11px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">+{s.selected_skills.length - 4} more</span>}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  {s.average_score != null ? (
                    <div className="text-right">
                      <div className={`text-xl font-extrabold ${getScoreTextColor(s.average_score)}`}>
                        {Math.round(s.average_score)}%
                      </div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">Score</div>
                    </div>
                  ) : (
                    <span className={`badge ${s.status === 'completed' ? 'badge-success' : s.status === 'abandoned' ? 'badge-error' : 'badge-warning'}`}>
                      {s.status === 'completed' && <CheckCircle2 size={12} className="mr-1" />}
                      {s.status === 'completed' ? 'Completed' : s.status === 'abandoned' ? 'Abandoned' : 'In Progress'}
                    </span>
                  )}
                  <ChevronRight size={20} className="text-slate-300 group-hover:text-indigo-600 transition-colors hidden sm:block" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
