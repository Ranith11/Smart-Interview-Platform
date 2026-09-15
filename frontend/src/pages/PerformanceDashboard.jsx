import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, Brain, Target, TrendingUp, Lightbulb, Award, AlertCircle, Loader2, ChevronRight } from 'lucide-react';
import api from '../services/api';

export default function PerformanceDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { loadPerformance(); }, []);

  const loadPerformance = async () => {
    try {
      const res = await api.get('/users/performance');
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  };

  const getScoreTextColor = (score) => {
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-amber-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };
  
  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 size={36} className="animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="card text-center p-8 border-red-200 bg-red-50 shadow-sm">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-900 mb-2">Error</h2>
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!data?.has_data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Performance Dashboard</h1>
          <p className="text-slate-500 mt-1 text-base">Track your progress across interviews</p>
        </div>
        <div className="card border-slate-200 border-dashed text-center p-12 bg-slate-50">
          <BarChart3 size={64} className="text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-700 mb-2">No Evaluated Interviews Yet</h3>
          <p className="text-slate-500 mb-8 max-w-md mx-auto">
            Complete an adaptive interview to see your performance analytics, skill breakdowns, and personalized AI recommendations.
          </p>
          <Link to="/setup" className="btn btn-primary shadow-sm px-6">Start an Interview</Link>
        </div>
      </div>
    );
  }

  const { overall_average, skill_performance, bloom_progression, strengths, weak_areas, recommendations, recent_interviews } = data;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Performance Dashboard</h1>
        <p className="text-slate-500 mt-1 text-base">Aggregated performance across all evaluated interviews</p>
      </div>

      {/* Overall Score */}
      <div className="card p-6 flex flex-col md:flex-row items-center gap-8 shadow-sm">
        <div className="text-center min-w-[140px] px-6 py-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className={`text-5xl font-extrabold tracking-tight ${getScoreTextColor(overall_average)}`}>
            {Math.round(overall_average)}<span className="text-2xl">%</span>
          </div>
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-2">Overall Average</div>
        </div>
        <div className="flex-1 w-full grid grid-cols-3 gap-4">
          <div className="bg-white border border-slate-100 p-4 rounded-xl shadow-sm text-center">
            <div className="text-2xl font-bold text-slate-800">{recent_interviews.length}</div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Interviews</div>
          </div>
          <div className="bg-emerald-50 border border-emerald-100 p-4 rounded-xl shadow-sm text-center">
            <div className="text-2xl font-bold text-emerald-600">{strengths.length}</div>
            <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mt-1">Strong Skills</div>
          </div>
          <div className="bg-red-50 border border-red-100 p-4 rounded-xl shadow-sm text-center">
            <div className="text-2xl font-bold text-red-600">{weak_areas.length}</div>
            <div className="text-xs font-semibold text-red-700 uppercase tracking-wider mt-1">Weak Areas</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skill Performance */}
        <div className="card p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
            <Target size={20} className="text-indigo-600" /> Skill Performance Matrix
          </h2>
          {Object.keys(skill_performance).length > 0 ? (
            <div className="space-y-5">
              {Object.entries(skill_performance)
                .sort(([, a], [, b]) => b.average_score - a.average_score)
                .map(([skill, perf]) => (
                  <div key={skill}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-sm font-semibold text-slate-700">{skill}</span>
                      <span className={`text-sm font-bold ${getScoreTextColor(perf.average_score)}`}>
                        {Math.round(perf.average_score)}%
                      </span>
                    </div>
                    <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-1000 ${getScoreBgColor(perf.average_score)}`}
                        style={{ width: `${Math.min(100, perf.average_score)}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-slate-500 text-sm">No skill data yet</p>
          )}
        </div>

        {/* Strengths & Weaknesses */}
        <div className="card p-6 shadow-sm flex flex-col">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
            <Award size={20} className="text-emerald-500" /> Strengths & Focus Areas
          </h2>
          <div className="flex-1 space-y-6">
            {strengths.length > 0 && (
              <div>
                <div className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-3">Strong Competencies</div>
                <div className="flex flex-wrap gap-2">
                  {strengths.map(s => (
                    <span key={s} className="badge bg-emerald-100 text-emerald-800 px-3 py-1.5 shadow-sm border border-emerald-200">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {weak_areas.length > 0 && (
              <div>
                <div className="text-xs font-bold text-red-500 uppercase tracking-wider mb-3">Needs Improvement</div>
                <div className="flex flex-wrap gap-2">
                  {weak_areas.map(s => (
                    <span key={s} className="badge bg-red-100 text-red-800 px-3 py-1.5 shadow-sm border border-red-200">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {strengths.length === 0 && weak_areas.length === 0 && (
              <div className="h-full flex items-center justify-center p-6 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
                <p className="text-slate-500 text-sm font-medium text-center">Complete more interviews to generate accurate strengths and weaknesses.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="card p-6 shadow-sm border-t-4 border-t-amber-400">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-5">
            <Lightbulb size={20} className="text-amber-500" /> AI Growth Plan
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec, i) => (
              <div key={i} className={`p-4 rounded-xl border-l-4 shadow-sm ${
                rec.priority === 'high' ? 'bg-red-50 border-red-500' : 
                rec.priority === 'medium' ? 'bg-amber-50 border-amber-500' : 'bg-emerald-50 border-emerald-500'
              }`}>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">{rec.skill}</div>
                <p className="text-sm text-slate-700 leading-relaxed font-medium">{rec.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Interviews */}
      {recent_interviews.length > 0 && (
        <div className="card p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-5">
            <TrendingUp size={20} className="text-indigo-600" /> Recent Interview History
          </h2>
          <div className="space-y-3">
            {recent_interviews.map((interview) => (
              <Link key={interview.id} to={`/results/${interview.id}`} className="group flex items-center justify-between p-4 rounded-xl bg-slate-50 hover:bg-white border border-transparent hover:border-slate-200 hover:shadow-sm transition-all no-underline">
                <div>
                  <div className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {interview.date ? new Date(interview.date).toLocaleDateString() : 'N/A'}
                  </div>
                  <div className="text-sm text-slate-500 mt-1 capitalize">
                    {interview.difficulty} • {interview.question_count > 0 ? `${interview.question_count} questions` : 'Open-Ended'}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className={`text-lg font-extrabold ${getScoreTextColor(interview.average_score)}`}>
                      {Math.round(interview.average_score)}%
                    </span>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Score</div>
                  </div>
                  <ChevronRight size={20} className="text-slate-400 group-hover:text-indigo-600 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
