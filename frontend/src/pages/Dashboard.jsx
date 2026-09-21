import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Search, Bell, Plus, Zap, FileText, CheckCircle2, HelpCircle, TrendingUp, ChevronRight, BarChart3, AlertCircle, Clock } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, historyRes] = await Promise.all([
          api.get('/users/stats'),
          api.get('/interviews/history'),
        ]);
        setStats(statsRes.data);
        setHistory(historyRes.data.slice(0, 5));

        try {
          const resumeRes = await api.get('/resumes/current');
          setResume(resumeRes.data);
        } catch { /* no resume yet */ }
      } catch (err) {
        console.error('Failed to load dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const getPerformanceStage = (score) => {
    if (!score) return { title: "Getting Started", desc: "Complete your first interview to establish a baseline.", polish: "Needs Polish" };
    if (score >= 80) return { title: "Advanced Stage", desc: "Consistently scoring high. Ready for complex system design.", polish: "Excellent" };
    if (score >= 60) return { title: "Intermediate Stage", desc: "Solid foundation, with room to grow in problem efficiency.", polish: "On Track" };
    return { title: "Foundation Stage", desc: "Building core competencies. Focus on foundational concepts.", polish: "Needs Polish" };
  };

  const perfStage = getPerformanceStage(stats?.average_score);

  return (
    <div className="flex flex-col min-h-screen bg-[#F8FAFC]">
      {/* Top Header */}
      <header className="h-16 bg-white/50 backdrop-blur-sm border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-40">
        <div className="flex-1 max-w-2xl hidden md:flex">
          {/* Functional Search Bar Omitted as requested by user to avoid placeholders */}
          <div className="relative w-full max-w-md hidden">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input type="text" placeholder="Search anything (questions, topics, skills)..." className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all" />
          </div>
        </div>
        <div className="flex items-center gap-6 ml-auto">
          <Link to={resume ? '/setup' : '/resume'} className="flex items-center gap-2 bg-[#0F172A] hover:bg-slate-800 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors no-underline shadow-sm">
            <Plus size={16} />
            Start New Interview
          </Link>
        </div>
      </header>

      {/* Main Dashboard Content */}
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-8">
        
        {/* Welcome Banner */}
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div className="max-w-2xl">
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
                Welcome back, <span className="text-indigo-600">{user?.name?.split(' ')[0] || 'User'}</span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold uppercase tracking-wider ml-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                  AI Coach Ready
                </span>
              </h1>
              <p className="text-slate-500 mt-3 text-base leading-relaxed">
                Ready for your next mock interview session? We generate personalized questions based on your resume and recent scoring trends.
              </p>
              <div className="flex items-center gap-4 mt-6 text-sm text-slate-500 font-medium">
                <span className="flex items-center gap-1.5"><Zap size={16} className="text-amber-500" /> Quick prep: ~15 mins</span>
                <span className="text-slate-300">•</span>
                <span>Focus area: {resume?.skills?.[0] || 'Core Concepts'} & Architecture</span>
              </div>
            </div>
            <div className="flex-shrink-0">
              <Link to={resume ? '/setup' : '/resume'} className="flex items-center justify-center gap-2 bg-[#0F172A] hover:bg-slate-800 text-white px-6 py-3 rounded-xl text-sm font-semibold transition-colors no-underline shadow-md">
                <Plus size={18} />
                Start New Interview
              </Link>
            </div>
          </div>
        </div>

        {/* 4 Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-indigo-200 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Interviews</h3>
              <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-600"><FileText size={16} /></div>
            </div>
            <div className="flex items-end gap-3">
              <span className="text-3xl font-extrabold text-slate-900">{stats?.total_interviews || 0}</span>
              {stats?.total_interviews > 0 && (
                <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md mb-1.5">+{stats.total_interviews} total</span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium mt-2">Adaptive interview sessions</p>
          </div>
          
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-emerald-200 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Completed Sessions</h3>
              <div className="w-8 h-8 rounded-md bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600"><CheckCircle2 size={16} /></div>
            </div>
            <div className="flex items-end gap-3">
              <span className="text-3xl font-extrabold text-slate-900">{stats?.completed_interviews || 0}</span>
              {stats?.total_interviews > 0 && (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md mb-1.5">
                  {Math.round((stats.completed_interviews / stats.total_interviews) * 100)}% finished
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium mt-2">{stats?.total_interviews - stats?.completed_interviews || 0} abandoned sessions</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-sky-200 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Questions Practiced</h3>
              <div className="w-8 h-8 rounded-md bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600"><HelpCircle size={16} /></div>
            </div>
            <div className="flex items-end gap-3">
              <span className="text-3xl font-extrabold text-slate-900">{stats?.total_questions || 0}</span>
              {stats?.total_questions > 0 && (
                <span className="text-xs font-semibold text-sky-700 bg-sky-100 px-2 py-0.5 rounded-md mb-1.5">AI Evaluated</span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium mt-2">Across all interview sessions</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-indigo-200 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Answered In Depth</h3>
              <div className="w-8 h-8 rounded-md bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600"><TrendingUp size={16} /></div>
            </div>
            <div className="flex items-end gap-3">
              <span className="text-3xl font-extrabold text-slate-900">{stats?.total_answered || 0}</span>
              {stats?.total_questions > 0 && (
                <span className="text-xs font-semibold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-md mb-1.5">
                  {Math.round((stats.total_answered / stats.total_questions) * 100)}% response
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium mt-2">Questions successfully completed</p>
          </div>
        </div>

        {/* 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* Overall Performance Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-amber-50 text-amber-600 flex items-center justify-center"><BarChart3 size={18} /></div>
                  <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">Overall Performance</h2>
                </div>
                <span className="text-xs font-bold px-2 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-md">{perfStage.polish}</span>
              </div>
              
              <div className="p-6 flex flex-col">
                <div className="bg-slate-50 rounded-xl p-5 border border-slate-100 flex items-start gap-5 mb-8">
                  <div className="text-center">
                    <div className="text-3xl font-extrabold text-slate-900">{stats?.average_score != null ? Math.round(stats.average_score) : 0}<span className="text-xl">%</span></div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Score</div>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 mb-1">{perfStage.title}</h4>
                    <p className="text-xs text-slate-500 leading-relaxed font-medium">{perfStage.desc}</p>
                  </div>
                </div>

                <div className="space-y-5">
                  <div>
                    <div className="flex justify-between text-xs font-bold text-slate-700 mb-2">
                      <span>Overall Mastery</span>
                      <span>{stats?.average_score != null ? Math.round(stats.average_score) : 0}%</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full transition-all duration-1000" style={{ width: `${stats?.average_score || 0}%` }}></div>
                    </div>
                  </div>
                </div>

                <div className="pt-6">
                  <div className="bg-indigo-50/50 border border-indigo-100 rounded-xl p-4 flex gap-3">
                    <AlertCircle size={18} className="text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h5 className="text-xs font-bold text-slate-900 mb-1">Recommended AI Target:</h5>
                      <p className="text-xs text-slate-600 font-medium leading-relaxed">
                        Re-attempt an interview focusing on {resume?.skills?.[0] || 'core technical'} concepts to push your average score past 60%.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Resume Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-slate-50 text-slate-500 flex items-center justify-center border border-slate-200"><FileText size={18} /></div>
                  <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">Your Resume</h2>
                </div>
                <Link to="/resume" className="text-xs font-bold text-slate-500 hover:text-indigo-600 transition-colors no-underline">Manage</Link>
              </div>
              
              <div className="p-6">
                {!resume ? (
                  <div className="text-center py-4">
                    <p className="text-sm text-slate-500 mb-4 font-medium">No resume uploaded yet.</p>
                    <Link to="/resume" className="btn btn-secondary shadow-sm text-xs w-full no-underline">Upload Resume</Link>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
                      <div className="flex items-center gap-3">
                        <div className="px-2 py-1 bg-red-50 text-red-600 border border-red-200 rounded-md text-[10px] font-extrabold uppercase">PDF</div>
                        <div>
                          <div className="text-sm font-bold text-slate-900 truncate max-w-[150px]">{resume.filename || 'resume.pdf'}</div>
                          <div className="text-[10px] font-medium text-slate-400 mt-0.5">Updated {new Date(resume.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                      <div className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-bold flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                        {resume.skills?.length || 0} skills
                      </div>
                    </div>
                    
                    <div className="mb-4 text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">Identified Competencies</div>
                    <div className="flex flex-wrap gap-2 mb-6">
                      {(resume.skills || []).slice(0, 8).map(s => (
                        <span key={s} className="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 text-xs font-semibold rounded-md shadow-sm">
                          {s}
                        </span>
                      ))}
                      {(resume.skills || []).length > 8 && (
                        <span className="px-3 py-1.5 bg-slate-50 border border-slate-200 text-slate-500 text-xs font-semibold rounded-md flex items-center gap-1">
                          +{ (resume.skills || []).length - 8 } more
                        </span>
                      )}
                    </div>
                    
                    <Link to="/resume" className="flex items-center justify-center gap-2 w-full py-3 bg-white border border-dashed border-slate-300 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 hover:text-indigo-600 hover:border-indigo-300 transition-all no-underline">
                      <Plus size={16} />
                      Upload new revision
                    </Link>
                  </>
                )}
              </div>
            </div>
            
          </div>

          {/* Right Column */}
          <div className="lg:col-span-7 space-y-6">
            
            {/* Recent Sessions Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-slate-50 text-slate-500 flex items-center justify-center border border-slate-200"><Clock size={18} /></div>
                  <div>
                    <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">Recent Interview Sessions</h2>
                    <p className="text-xs text-slate-500 font-medium mt-0.5">Historical performance breakdown</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex bg-slate-100 p-1 rounded-lg">
                    <button className="px-3 py-1 bg-white shadow-sm text-slate-900 text-xs font-bold rounded-md">All</button>
                    <button className="px-3 py-1 text-slate-500 hover:text-slate-700 text-xs font-bold rounded-md transition-colors border-none bg-transparent cursor-pointer">Technical</button>
                  </div>
                  {history.length > 0 && (
                    <Link to="/history" className="text-xs font-bold text-indigo-600 flex items-center gap-1 hover:text-indigo-800 ml-2 no-underline">
                      View all <ChevronRight size={14} />
                    </Link>
                  )}
                </div>
              </div>

              <div className="flex-1">
                {history.length === 0 ? (
                  <div className="p-12 flex flex-col items-center text-center">
                    <div className="w-16 h-16 bg-slate-50 border border-slate-100 text-slate-300 rounded-full flex items-center justify-center mb-4">
                      <Clock size={24} />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 mb-1">No sessions yet</h4>
                    <p className="text-xs text-slate-500 font-medium max-w-xs">Complete your first interview to see performance analytics here.</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {history.map((h, i) => (
                      <div key={h.id} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6 hover:bg-slate-50 transition-colors">
                        <div className="flex items-start gap-4">
                          <div className="w-8 h-8 rounded-md bg-indigo-50 text-indigo-600 text-xs font-bold flex items-center justify-center flex-shrink-0 border border-indigo-100">
                            #{history.length - i}
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-slate-900 mb-2">{h.selected_skills?.[0] || 'Technical'} Practice</h4>
                            <div className="flex flex-wrap items-center gap-2 mb-3">
                              <span className="px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-extrabold uppercase rounded-md">{h.difficulty}</span>
                              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-extrabold uppercase rounded-md">Mixed Topics</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
                              <Clock size={12} /> {new Date(h.started_at).toLocaleDateString()}
                              <span>•</span>
                              <span>{h.questions_answered} answered</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-6 sm:pl-4 sm:border-l border-slate-100">
                          <div className="text-center min-w-[60px]">
                            {h.average_score != null ? (
                              <>
                                <div className={`text-xl font-black ${h.average_score >= 70 ? 'text-emerald-600' : h.average_score >= 50 ? 'text-amber-500' : 'text-red-500'}`}>
                                  {Math.round(h.average_score)}%
                                </div>
                                <div className="text-[10px] font-extrabold text-slate-400 uppercase mt-0.5">Score</div>
                              </>
                            ) : (
                              <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-extrabold uppercase rounded-full whitespace-nowrap">
                                In Progress
                              </span>
                            )}
                          </div>
                          
                          <Link to={h.status === 'completed' ? `/results/${h.id}` : `/interview/${h.id}`} className="px-4 py-2 bg-white border border-slate-200 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-50 transition-colors shadow-sm no-underline flex items-center gap-2">
                            Feedback <ChevronRight size={14} className="text-slate-400" />
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
