import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { BarChart3, Brain, Target, CheckCircle, ArrowLeft, Lightbulb, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../services/api';

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedQ, setExpandedQ] = useState(null);

  useEffect(() => { loadResults(); }, [id]);

  const loadResults = async () => {
    try {
      const res = await api.get(`/interviews/${id}/results`);
      setResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load results');
    } finally {
      setLoading(false);
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
    const labels = { remember: 'Remember', understand: 'Understand', apply: 'Apply', analyze: 'Analyze', evaluate: 'Evaluate', create: 'Create' };
    return labels[level] || level || '';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 size={36} className="animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="card text-center p-8 border-red-200 bg-red-50 shadow-sm">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-900 mb-2">Error Loading Results</h2>
          <p className="text-red-700 mb-6">{error}</p>
          <button className="btn bg-red-600 text-white hover:bg-red-700 shadow-sm" onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
        </div>
      </div>
    );
  }

  const { session, overall_average_score, skill_performance, bloom_progression, questions, recommendations } = results;
  const hasEvaluations = questions.some(q => q.evaluation);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-4">
        <div>
          <button onClick={() => navigate('/history')} className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-900 mb-2 bg-transparent border-none cursor-pointer transition-colors p-0">
            <ArrowLeft size={16} /> Back to History
          </button>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Interview Results</h1>
          <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-slate-500">
            <span className="font-medium text-slate-700 capitalize">{session.difficulty}</span>
            <span className="text-slate-300">•</span>
            <span>{questions.length} questions answered</span>
            <span className="text-slate-300">•</span>
            <span className="capitalize">{session.completion_reason ? session.completion_reason.replace(/_/g, ' ') : 'Manual Completion'}</span>
          </div>
        </div>
        {hasEvaluations && (
          <div className="text-left md:text-center p-4 bg-white border border-slate-200 rounded-xl shadow-sm min-w-[140px]">
            <div className={`text-4xl font-extrabold tracking-tight ${getScoreTextColor(overall_average_score)}`}>
              {Math.round(overall_average_score)}<span className="text-xl">%</span>
            </div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-1">Overall Score</div>
          </div>
        )}
      </div>

      {!hasEvaluations && (
        <div className="card p-6 text-center text-slate-500 bg-slate-50">
          This interview does not have evaluation data. It may be a legacy session.
        </div>
      )}

      {/* Skill Performance */}
      {hasEvaluations && Object.keys(skill_performance).length > 0 && (
        <div className="card p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
            <Target size={20} className="text-indigo-600" /> {session.mode === 'syllabus' ? 'Topic Performance' : 'Skill Performance'}
          </h2>
          <div className="space-y-4">
            {Object.entries(skill_performance).map(([skill, data]) => (
              <div key={skill}>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-sm font-semibold text-slate-700">{skill}</span>
                  <span className={`text-sm font-bold ${getScoreTextColor(data.average_score)}`}>
                    {Math.round(data.average_score)}% <span className="text-slate-400 font-medium text-xs ml-1">({data.questions}Q)</span>
                  </span>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-1000 ${
                      data.average_score >= 80 ? 'bg-emerald-500' :
                      data.average_score >= 60 ? 'bg-amber-500' :
                      data.average_score >= 40 ? 'bg-orange-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(100, data.average_score)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="card p-6 shadow-sm border-t-4 border-t-amber-400">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-5">
            <Lightbulb size={20} className="text-amber-500" /> AI Recommendations
          </h2>
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <div key={i} className={`p-4 rounded-lg border-l-4 ${
                rec.priority === 'high' ? 'bg-red-50 border-red-500' : 
                rec.priority === 'medium' ? 'bg-amber-50 border-amber-500' : 'bg-emerald-50 border-emerald-500'
              }`}>
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                  {rec.skill}
                </div>
                <div className="text-sm text-slate-700 leading-relaxed font-medium">
                  {rec.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bloom Progression */}
      {bloom_progression.length > 0 && (
        <div className="card p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-5">
            <Brain size={20} className="text-purple-600" /> Bloom's Taxonomy Progression
          </h2>
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {bloom_progression.map((bp, i) => (
              <div key={i} className="flex flex-col items-center p-3 rounded-lg bg-slate-50 border border-slate-200 min-w-[70px] flex-shrink-0">
                <span className="text-xs font-semibold text-slate-400 mb-1">Q{bp.question_number}</span>
                <span className="text-sm font-bold text-indigo-700">
                  {getBloomLabel(bp.bloom_level)}
                </span>
                <span className="text-[10px] font-bold text-slate-400 mt-1 uppercase tracking-widest">Lvl {bp.bloom_order}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question-by-Question Review */}
      <div className="card shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50">
          <h2 className="text-lg font-bold text-slate-900">
            Question Review ({questions.length})
          </h2>
        </div>
        <div className="divide-y divide-slate-100">
          {questions.map((q) => {
            const isExpanded = expandedQ === q.id;
            const ev = q.evaluation;
            return (
              <div key={q.id} className="bg-white">
                {/* Summary row */}
                <div 
                  className={`p-4 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors ${isExpanded ? 'bg-indigo-50/30' : ''}`}
                  onClick={() => setExpandedQ(isExpanded ? null : q.id)}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0 pr-4">
                    <span className="text-sm font-bold text-slate-400 whitespace-nowrap w-8">
                      Q{q.question_number}
                    </span>
                    <span className="badge bg-slate-100 text-slate-700 border border-slate-200 font-semibold truncate max-w-[120px] sm:max-w-none">{q.skill}</span>
                    {q.bloom_level && (
                      <span className="badge bg-purple-50 text-purple-700 border border-purple-100 hidden sm:inline-flex items-center gap-1">
                        <Brain size={12} />
                        {getBloomLabel(q.bloom_level)}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    {ev && (
                      <span className={`text-base font-bold ${getScoreTextColor(ev.overall_score)}`}>
                        {ev.overall_score}%
                      </span>
                    )}
                    {!ev && q.answer_text && (
                      <span className="text-xs text-slate-400 font-medium">No eval</span>
                    )}
                    {isExpanded ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                  </div>
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="p-5 border-t border-slate-100 bg-white">
                    <div className="mb-5">
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Question</div>
                      <p className="text-base text-slate-900 leading-relaxed font-medium">{q.question_text}</p>
                    </div>
                    {q.answer_text && (
                      <div className="mb-6">
                        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Your Answer</div>
                        <div className="text-sm leading-relaxed text-slate-700 bg-slate-50 border border-slate-100 p-4 rounded-lg whitespace-pre-wrap">
                          {q.answer_text}
                        </div>
                      </div>
                    )}
                    {ev && (
                      <div className="bg-indigo-50/30 border border-indigo-100 rounded-xl p-5">
                        <div className="text-xs font-bold text-indigo-800 uppercase tracking-wider mb-4 flex items-center gap-2">
                          <BarChart3 size={14} /> Evaluation Breakdown
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5">
                          {[
                            { l: 'Technical', v: ev.technical_score },
                            { l: 'Complete', v: ev.completeness_score },
                            { l: 'Relevant', v: ev.relevance_score },
                            { l: 'Similarity', v: ev.semantic_similarity_score },
                            { l: 'Concepts', v: ev.concept_coverage_score },
                          ].map(s => (
                            <div key={s.l} className="bg-white border border-indigo-50 rounded-lg p-2 text-center shadow-sm">
                              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{s.l}</div>
                              <div className={`text-base font-bold ${getScoreTextColor(s.v)}`}>{s.v}</div>
                            </div>
                          ))}
                        </div>
                        {ev.feedback && (
                          <div className="text-sm text-slate-700 leading-relaxed border-t border-indigo-100 pt-4">
                            <span className="font-semibold text-slate-900 mr-2">Feedback:</span>
                            {ev.feedback}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 justify-center pt-4 pb-8">
        <Link to="/dashboard" className="btn btn-secondary shadow-sm">Dashboard</Link>
        <Link to="/setup" className="btn btn-primary shadow-md">New Interview</Link>
        <Link to="/performance" className="btn btn-secondary shadow-sm">Performance Profile</Link>
      </div>
    </div>
  );
}
