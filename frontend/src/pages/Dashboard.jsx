import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  Search, Bell, Plus, Zap, FileText, CheckCircle2, 
  HelpCircle, TrendingUp, ChevronRight, BarChart3, 
  AlertCircle, Clock, Play, BrainCircuit
} from 'lucide-react';

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

  return (
    <div className="flex flex-col min-h-screen bg-[#F8FAFC]">
      {/* Top Header */}
      <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-40">
        <div className="flex-1 max-w-2xl hidden md:flex">
          {/* Search Bar omitted */}
        </div>
        <div className="flex items-center gap-6 ml-auto">
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
             </div>
             <span className="text-sm font-semibold text-slate-700">{user?.name}</span>
          </div>
        </div>
      </header>

      {/* Main Dashboard Content */}
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-10">
        
        {/* Welcome Banner */}
        <div className="bg-gradient-to-br from-[#0F172A] to-[#1E293B] rounded-3xl p-10 shadow-xl overflow-hidden relative">
          {/* Decorative background elements */}
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl"></div>
          <div className="absolute bottom-0 left-20 -mb-20 w-72 h-72 rounded-full bg-blue-500/10 blur-3xl"></div>
          
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-8">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-indigo-200 text-xs font-bold uppercase tracking-wider mb-4 backdrop-blur-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
                AI Coach Ready
              </div>
              <h1 className="text-4xl font-extrabold text-white tracking-tight mb-4">
                Welcome back, {user?.name?.split(' ')[0] || 'User'}!
              </h1>
              <p className="text-slate-300 text-lg leading-relaxed">
                Ready to level up your interview skills? Start a new session, review your past performance, or update your resume to keep your AI recommendations sharp.
              </p>
            </div>
            <div className="flex-shrink-0">
              <Link to={resume ? '/setup' : '/resume'} className="group flex items-center justify-center gap-3 bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-2xl text-base font-bold transition-all shadow-[0_0_40px_-10px_rgba(79,70,229,0.5)] hover:shadow-[0_0_60px_-15px_rgba(79,70,229,0.7)] hover:-translate-y-1 no-underline">
                <Play size={20} className="fill-white" />
                Start Interview
                <ChevronRight size={18} className="opacity-70 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </Link>
            </div>
          </div>
        </div>

        {/* 4 Stat Cards */}
        <div>
          <h2 className="text-lg font-extrabold text-slate-900 mb-6 flex items-center gap-2">
            <TrendingUp className="text-indigo-600" size={24} /> 
            Your Progress Snapshot
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md hover:border-indigo-200 transition-all group">
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:scale-110 transition-transform"><FileText size={24} /></div>
                <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest text-right">Total<br/>Interviews</h3>
              </div>
              <div className="flex items-end gap-3">
                <span className="text-4xl font-black text-slate-900">{stats?.total_interviews || 0}</span>
              </div>
            </div>
            
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md hover:border-emerald-200 transition-all group">
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 group-hover:scale-110 transition-transform"><CheckCircle2 size={24} /></div>
                <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest text-right">Completed<br/>Sessions</h3>
              </div>
              <div className="flex items-end gap-3">
                <span className="text-4xl font-black text-slate-900">{stats?.completed_interviews || 0}</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md hover:border-sky-200 transition-all group">
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-xl bg-sky-50 flex items-center justify-center text-sky-600 group-hover:scale-110 transition-transform"><HelpCircle size={24} /></div>
                <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest text-right">Questions<br/>Practiced</h3>
              </div>
              <div className="flex items-end gap-3">
                <span className="text-4xl font-black text-slate-900">{stats?.total_questions || 0}</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md hover:border-amber-200 transition-all group">
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 group-hover:scale-110 transition-transform"><Zap size={24} /></div>
                <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest text-right">Average<br/>Score</h3>
              </div>
              <div className="flex items-end gap-3">
                <span className="text-4xl font-black text-slate-900">{stats?.average_score != null ? Math.round(stats.average_score) : 0}<span className="text-2xl text-slate-400 ml-1">%</span></span>
              </div>
            </div>
          </div>
        </div>

        {/* Portals to features */}
        <div>
          <h2 className="text-lg font-extrabold text-slate-900 mb-6 flex items-center gap-2">
            <BrainCircuit className="text-indigo-600" size={24} /> 
            Explore Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Analytics Portal */}
            <Link to="/performance" className="group relative bg-white rounded-3xl p-8 border border-slate-200 shadow-sm hover:shadow-xl hover:border-indigo-300 transition-all no-underline overflow-hidden flex flex-col h-full">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110">
                <BarChart3 size={120} />
              </div>
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-6 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <BarChart3 size={28} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Performance Analytics</h3>
              <p className="text-slate-500 font-medium leading-relaxed mb-8 flex-1">
                Dive deep into your performance metrics. Discover your strongest skills and AI-recommended growth areas.
              </p>
              <div className="flex items-center text-indigo-600 font-bold text-sm">
                View Full Analytics <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Resume Portal */}
            <Link to="/resume" className="group relative bg-white rounded-3xl p-8 border border-slate-200 shadow-sm hover:shadow-xl hover:border-emerald-300 transition-all no-underline overflow-hidden flex flex-col h-full">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110">
                <FileText size={120} />
              </div>
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600 mb-6 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                <FileText size={28} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Resume Intelligence</h3>
              <p className="text-slate-500 font-medium leading-relaxed mb-8 flex-1">
                Manage your uploaded resumes. Let our AI extract your competencies to generate highly personalized questions.
              </p>
              <div className="flex items-center text-emerald-600 font-bold text-sm">
                Manage Resume <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* History Portal */}
            <Link to="/history" className="group relative bg-white rounded-3xl p-8 border border-slate-200 shadow-sm hover:shadow-xl hover:border-amber-300 transition-all no-underline overflow-hidden flex flex-col h-full">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity transform group-hover:scale-110">
                <Clock size={120} />
              </div>
              <div className="w-14 h-14 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-600 mb-6 group-hover:bg-amber-600 group-hover:text-white transition-colors">
                <Clock size={28} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Interview History</h3>
              <p className="text-slate-500 font-medium leading-relaxed mb-8 flex-1">
                Review past interview sessions, analyze individual question feedback, and track your improvement over time.
              </p>
              <div className="flex items-center text-amber-600 font-bold text-sm">
                View History <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

          </div>
        </div>

      </main>
    </div>
  );
}
