import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, Target, Lightbulb, Award, AlertCircle, Loader2, 
  Trophy, ClipboardList, TrendingUp, Calendar, BookOpen, CheckCircle2, FileText, ArrowRight, Settings, Briefcase
} from 'lucide-react';
import api from '../services/api';

export default function PerformanceDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modeFilter, setModeFilter] = useState('normal');

  useEffect(() => { loadPerformance(); }, [modeFilter]);

  const loadPerformance = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/users/performance?mode=${modeFilter}`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#059669'; // emerald-600
    if (score >= 60) return '#d97706'; // amber-600
    if (score >= 40) return '#ea580c'; // orange-600
    return '#dc2626'; // red-600
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

  const getModeLabel = (mode) => {
    if (mode === 'job_specific') return 'Job-Specific';
    if (mode === 'syllabus') return 'Syllabus-Based';
    return 'General Technical';
  };

  if (loading && !data) {
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

  const renderHeader = () => (
    <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Performance Analytics</h1>
        <p className="text-slate-500 mt-1 text-sm">Track your interview performance, identify trends, and get personalized recommendations.</p>
      </div>
      {/* Mode Filter Dropdown */}
      <div className="relative self-start sm:self-auto">
        <select
          value={modeFilter}
          onChange={(e) => setModeFilter(e.target.value)}
          className="appearance-none bg-white border border-slate-200 text-slate-700 font-medium text-sm rounded-lg pl-4 pr-10 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 shadow-sm cursor-pointer hover:border-slate-300 transition-colors"
        >
          <option value="normal">General Technical</option>
          <option value="job_specific">Job-Specific</option>
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
          <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      </div>
    </div>
  );

  if (!data?.has_data || !data.recent_interviews || data.recent_interviews.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6 bg-slate-50/50 min-h-screen">
        {renderHeader()}
        <div className="card border-slate-200 border-dashed text-center p-12 bg-slate-50/80">
          <BarChart3 size={64} className="text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-700 mb-2">
            No Completed {modeFilter !== 'all' ? getModeLabel(modeFilter) : ''} Interviews
          </h3>
          <p className="text-slate-500 mb-8 max-w-md mx-auto">
            Complete an interview in this mode to see your performance analytics, skill breakdowns, and personalized AI recommendations.
          </p>
          <Link to="/setup" className="btn btn-primary shadow-sm px-6">Start an Interview</Link>
        </div>
      </div>
    );
  }

  const { overall_average, skill_performance, bloom_performance, strengths, weak_areas, recommendations, recent_interviews } = data;
  const latestInterview = recent_interviews[0];

  // Colors for Bloom Taxonomy bars
  const bloomColors = {
    'Remember': 'bg-blue-500',
    'Understand': 'bg-emerald-400',
    'Apply': 'bg-amber-400',
    'Analyze': 'bg-red-400',
    'Evaluate': 'bg-purple-400',
    'Create': 'bg-pink-400'
  };
  const bloomLevels = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'];

  // Calculate SVG line chart points
  // recent_interviews has latest at index 0. We want Latest on the LEFT (index 0 is left).
  const svgWidth = Math.max(recent_interviews.length * 120, 800);
  const svgHeight = 220;
  const paddingX = 60;
  const paddingYTop = 40;
  const paddingYBottom = 40;
  const chartHeight = svgHeight - paddingYTop - paddingYBottom;
  
  const getX = (index) => {
    if (recent_interviews.length === 1) return svgWidth / 2;
    return paddingX + (index * ((svgWidth - 2 * paddingX) / (recent_interviews.length - 1)));
  };
  
  const getY = (score) => {
    return paddingYTop + chartHeight - ((score / 100) * chartHeight);
  };

  const points = recent_interviews.map((int, i) => `${getX(i)},${getY(int.average_score)}`).join(' ');

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6 bg-slate-50/50 min-h-screen">
      {renderHeader()}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5 shadow-sm flex items-center gap-4 bg-white border border-slate-100">
          <div className="w-12 h-12 rounded-full bg-amber-50 flex items-center justify-center shrink-0">
            <Trophy className="text-amber-500" size={24} />
          </div>
          <div>
            <div className="text-sm font-medium text-slate-500">Average Overall Score</div>
            <div className="text-3xl font-extrabold text-slate-900 tracking-tight mt-1">{Math.round(overall_average)}%</div>
            <div className="text-xs text-slate-400 mt-1">Across {recent_interviews.length} interviews</div>
          </div>
        </div>
        
        <div className="card p-5 shadow-sm flex items-center gap-4 bg-white border border-slate-100">
          <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
            <ClipboardList className="text-blue-500" size={24} />
          </div>
          <div>
            <div className="text-sm font-medium text-slate-500">Total Interviews</div>
            <div className="text-3xl font-extrabold text-slate-900 tracking-tight mt-1">{recent_interviews.length}</div>
            <div className="text-xs text-slate-400 mt-1">Completed successfully</div>
          </div>
        </div>

        <div className="card p-5 shadow-sm flex items-center gap-4 bg-white border border-slate-100">
          <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center shrink-0">
            <CheckCircle2 className="text-emerald-500" size={24} />
          </div>
          <div>
            <div className="text-sm font-medium text-slate-500">Strong Skills</div>
            <div className="text-3xl font-extrabold text-slate-900 tracking-tight mt-1">{strengths.length}</div>
            <div className="text-xs text-slate-400 mt-1">Performing well</div>
          </div>
        </div>

        <div className="card p-5 shadow-sm flex items-center gap-4 bg-white border border-slate-100">
          <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center shrink-0">
            <TrendingUp className="text-purple-500" size={24} />
          </div>
          <div>
            <div className="text-sm font-medium text-slate-500">Areas to Improve</div>
            <div className="text-3xl font-extrabold text-slate-900 tracking-tight mt-1">{weak_areas.length}</div>
            <div className="text-xs text-slate-400 mt-1">Need more practice</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main Graph */}
        <div className="xl:col-span-2 card p-6 shadow-sm bg-white border border-slate-100">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-slate-900">Interview Performance Progress</h2>
            <p className="text-sm text-slate-500">Your overall score across all completed interviews.</p>
          </div>
          <div className="w-full overflow-x-auto custom-scrollbar border border-slate-100 rounded-lg bg-slate-50 relative">
            {loading && <div className="absolute inset-0 bg-white/50 backdrop-blur-[2px] flex items-center justify-center z-10 rounded-lg"><Loader2 className="animate-spin text-indigo-500" /></div>}
            <svg width={svgWidth} height={svgHeight} className="min-w-full">
              {/* Grid Lines */}
              {[0, 20, 40, 60, 80, 100].map(val => (
                <g key={val}>
                  <text x={30} y={getY(val) + 4} className="text-[10px] fill-slate-400 text-end" textAnchor="end">{val}</text>
                  <line x1={40} y1={getY(val)} x2={svgWidth} y2={getY(val)} stroke="#e2e8f0" strokeDasharray="4 4" />
                </g>
              ))}
              
              {/* Y Axis Label */}
              <text x={12} y={svgHeight / 2} transform={`rotate(-90 12,${svgHeight/2})`} className="text-[11px] fill-slate-400 font-medium text-center" textAnchor="middle">Score (%)</text>
              
              {/* Data Line */}
              {recent_interviews.length > 1 && (
                <polyline
                  points={points}
                  fill="none"
                  stroke="#3b82f6" // blue-500
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
              
              {/* Data Points and X Axis Labels */}
              {recent_interviews.map((int, i) => {
                const x = getX(i);
                const y = getY(int.average_score);
                // The label shows standard chronological ordering but in reverse, or just Interview N
                // To keep it simple: if there are N interviews, and index 0 is latest, its chronological number is N-i
                const interviewNumber = recent_interviews.length - i;
                return (
                  <g key={int.id}>
                    <circle cx={x} cy={y} r="5" fill="#3b82f6" stroke="#ffffff" strokeWidth="2" />
                    <text x={x} y={y - 12} className="text-xs font-bold fill-slate-700" textAnchor="middle">{Math.round(int.average_score)}%</text>
                    <text x={x} y={svgHeight - 15} className="text-[10px] fill-slate-500 font-medium" textAnchor="middle">Interview {interviewNumber}</text>
                    {i === 0 && (
                       <text x={x} y={svgHeight - 4} className="text-[9px] fill-slate-400" textAnchor="middle">(Latest)</text>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Skill-wise Performance */}
        <div className="card p-6 shadow-sm bg-white border border-slate-100 xl:col-span-1">
          <div className="mb-6">
            <h2 className="text-lg font-bold text-slate-900">Skill-wise Performance</h2>
            <p className="text-sm text-slate-500">Your average scores in each skill area.</p>
          </div>
          {Object.keys(skill_performance).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(skill_performance)
                .sort(([, a], [, b]) => b.average_score - a.average_score)
                .map(([skill, perf], idx) => {
                  const colors = ['bg-blue-500', 'bg-emerald-400', 'bg-amber-400', 'bg-red-400', 'bg-purple-400', 'bg-pink-400', 'bg-indigo-400'];
                  const bgColor = colors[idx % colors.length];
                  return (
                    <div key={skill} className="flex items-center gap-4">
                      <div className="w-1/3 truncate text-sm font-semibold text-slate-700" title={skill}>{skill}</div>
                      <div className="flex-1 h-3.5 bg-slate-100 rounded-full overflow-hidden relative">
                        <div 
                          className={`h-full rounded-full transition-all duration-1000 ${bgColor}`}
                          style={{ width: `${Math.min(100, perf.average_score)}%` }}
                        />
                      </div>
                      <div className="w-8 text-right text-sm font-bold text-slate-700">
                        {Math.round(perf.average_score)}%
                      </div>
                    </div>
                  );
                })}
              <div className="flex justify-between text-[10px] font-medium text-slate-400 mt-2 pl-[33%] pr-8">
                <span>0</span>
                <span>20</span>
                <span>40</span>
                <span>60</span>
                <span>80</span>
                <span>100</span>
              </div>
              <div className="text-center text-[10px] font-medium text-slate-400 w-full pl-[33%] pr-8">Average Score (%)</div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm">No skill data available.</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Bloom's Taxonomy */}
        {modeFilter !== 'syllabus' && (
          <div className="card p-6 shadow-sm bg-white border border-slate-100 xl:col-span-1 flex flex-col">
          <div className="mb-6 flex justify-between items-start gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Bloom's Taxonomy</h2>
              <p className="text-sm text-slate-500">Your performance across cognitive levels.</p>
            </div>
            {modeFilter === 'syllabus' && (
              <span className="badge bg-amber-50 text-amber-700 border-amber-200">Syllabus Mode Excluded</span>
            )}
          </div>
          {bloom_performance && Object.keys(bloom_performance).length > 0 ? (
            <div className="flex-1 flex items-end justify-between min-h-[220px] pb-10 pt-4 relative pl-12">
              {/* Y-axis labels */}
              <div className="absolute left-3 top-0 bottom-10 flex flex-col justify-between text-[10px] text-slate-400 font-medium items-end w-6">
                <span>100</span>
                <span>80</span>
                <span>60</span>
                <span>40</span>
                <span>20</span>
                <span>0</span>
              </div>
              <div className="absolute left-11 top-0 bottom-10 border-l border-slate-200"></div>
              <div className="absolute -left-3 top-24 -rotate-90 text-[10px] font-medium text-slate-400 whitespace-nowrap">Score (%)</div>
              
              <div className="flex justify-between items-end w-full h-full gap-1 pr-2">
                {bloomLevels.map(level => {
                  const isZero = bloom_performance[level] === undefined;
                  const score = isZero ? 0 : bloom_performance[level];
                  
                  return (
                    <div key={level} className="flex flex-col items-center justify-end h-full flex-1 group">
                      <span className={`text-[9px] font-bold mb-1 ${isZero ? 'text-slate-300' : 'text-slate-700'}`}>
                        {Math.round(score)}%
                      </span>
                      <div 
                        className={`w-full max-w-[32px] rounded-t-sm transition-all duration-1000 ${isZero ? 'bg-slate-100' : bloomColors[level]}`} 
                        style={{ height: `${Math.max(score, 1)}%`, minHeight: '2px' }}
                      ></div>
                      <div className="mt-2 w-full flex justify-center text-center">
                        <span className={`text-[9px] font-medium tracking-tight leading-tight ${isZero ? 'text-slate-300' : 'text-slate-600'}`}>
                          {level}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="absolute bottom-0 w-full text-center text-[10px] font-medium text-slate-400 ml-2">Cognitive Level</div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm mt-4">
              {modeFilter === 'syllabus' ? "Syllabus mode uses a linear structure, not Bloom's taxonomy." : "No Bloom data available yet."}
            </p>
          )}
        </div>
        )}

        {/* Strengths and Weaknesses */}
        <div className={`card p-6 shadow-sm bg-white border border-slate-100 ${modeFilter === 'syllabus' ? 'xl:col-span-3' : 'xl:col-span-2'}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-4">
                <CheckCircle2 size={20} className="text-emerald-500" /> Your Strengths
              </h2>
              {strengths.length > 0 ? (
                <ul className="space-y-3">
                  {strengths.map(s => (
                    <li key={s} className="flex items-start gap-2 text-sm text-slate-700">
                      <CheckCircle2 size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                      <span>Excellent performance in <span className="font-semibold">{s}</span></span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500 italic">Complete more interviews to identify strong areas.</p>
              )}
            </div>
            
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-4">
                <AlertCircle size={20} className="text-red-500" /> Areas for Improvement
              </h2>
              {weak_areas.length > 0 ? (
                <ul className="space-y-3">
                  {weak_areas.map(w => (
                    <li key={w} className="flex items-start gap-2 text-sm text-slate-700">
                      <AlertCircle size={16} className="text-red-400 mt-0.5 shrink-0" />
                      <span>Needs review in <span className="font-semibold">{w}</span> concepts</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500 italic">No significant weak areas identified yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      {recommendations.length > 0 && (
        <div className="card p-6 shadow-sm bg-white border border-slate-100">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-5">
            <Lightbulb size={20} className="text-purple-500" /> AI Recommendations
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
            {recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                <FileText size={18} className="text-purple-400 mt-0.5 shrink-0" />
                <p className="text-sm text-slate-700 leading-relaxed">{rec.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Latest Interview Summary */}
      {latestInterview && (
        <div className="card p-6 shadow-sm bg-white border border-slate-100 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Calendar size={20} className="text-blue-500" />
              <div>
                <h2 className="text-lg font-bold text-slate-900">Latest Interview Summary</h2>
                <p className="text-xs text-slate-500">Your most recent interview performance.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full font-semibold">
              {latestInterview.mode === 'job_specific' && <Briefcase size={16} />}
              {latestInterview.mode === 'syllabus' && <BookOpen size={16} />}
              {latestInterview.mode === 'normal' && <Settings size={16} />}
              {getModeLabel(latestInterview.mode)}
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-slate-50 p-4 rounded-xl border border-slate-100">
            {/* Info Col */}
            <div>
              <div className="text-sm font-bold text-slate-900 mb-1">Interview {recent_interviews.length}</div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">
                  {latestInterview.date ? new Date(latestInterview.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Unknown Date'}
                </span>
              </div>
            </div>
            
            {/* Score Col */}
            <div>
              <div className="text-xs font-medium text-slate-500 mb-1">Overall Score</div>
              <div className="text-2xl font-extrabold text-slate-900 leading-none">
                {Math.round(latestInterview.average_score)}%
              </div>
            </div>
            
            {/* Topics Col */}
            <div className="max-w-[150px]">
              <div className="text-xs font-medium text-slate-500 mb-1">Topics / Skills</div>
              <div className="text-sm font-semibold text-slate-800 truncate" title={latestInterview.skills?.join(', ')}>
                {latestInterview.skills?.join(', ') || 'General'}
              </div>
            </div>
            
            {/* Questions Col */}
            <div>
              <div className="text-xs font-medium text-slate-500 mb-1">Questions</div>
              <div className="text-lg font-bold text-slate-800 leading-none">
                {latestInterview.question_count}
              </div>
            </div>
            
            {/* Strengths */}
            <div>
              <div className="flex items-center gap-1 text-xs font-bold text-emerald-600 mb-1">
                <CheckCircle2 size={12} /> Strong Areas
              </div>
              <ul className="text-[11px] text-slate-600 space-y-0.5">
                {latestInterview.strong_areas?.length > 0 
                  ? latestInterview.strong_areas.slice(0,2).map(s => <li key={s} className="truncate w-32" title={s}>• {s}</li>) 
                  : <li>• None identified</li>}
              </ul>
            </div>
            
            {/* Focus */}
            <div>
              <div className="flex items-center gap-1 text-xs font-bold text-red-500 mb-1">
                <AlertCircle size={12} /> Focus Next
              </div>
              <ul className="text-[11px] text-slate-600 space-y-0.5">
                {latestInterview.focus_next?.length > 0 
                  ? latestInterview.focus_next.slice(0,2).map(s => <li key={s} className="truncate w-32" title={s}>• {s}</li>) 
                  : <li>• Review fundamentals</li>}
              </ul>
            </div>
            
            {/* Action */}
            <div className="shrink-0 pt-2 md:pt-0">
              <Link to={`/results/${latestInterview.id}`} className="btn btn-primary text-xs px-4 py-2 shadow-sm rounded-md whitespace-nowrap">
                View Detailed Results &rarr;
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
