import React from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, FileText, Target, Sparkles, ArrowRight, Brain, Zap, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-xl tracking-tight">
            <BrainCircuit size={28} />
            <span className="text-slate-900">Smart<span className="text-indigo-600">Interview</span></span>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary shadow-sm text-sm px-5 py-2 no-underline">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors no-underline">
                  Log in
                </Link>
                <Link to="/register" className="btn btn-primary shadow-sm text-sm px-5 py-2 no-underline">
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden pt-16 pb-32 lg:pt-32 lg:pb-40">
        {/* Background Gradients */}
        <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80" aria-hidden="true">
          <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" style={{ clipPath: "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)" }}></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-sm font-semibold mb-8 animate-[fadeIn_0.5s_ease-out]">
            <Sparkles size={16} className="text-indigo-500" />
            AI-Powered Open-Ended Adaptive Engine
          </div>
          <h1 className="text-5xl lg:text-7xl font-extrabold text-slate-900 tracking-tight leading-tight mb-6 animate-[fadeIn_0.7s_ease-out]">
            Nail Your Next Interview<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              Tailored to Your Resume
            </span>
          </h1>
          <p className="mt-6 text-lg lg:text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed animate-[fadeIn_0.9s_ease-out]">
            Upload your resume and experience an open-ended, adaptive technical interview. Our AI dynamically scales Bloom's Taxonomy and difficulty based on your real-time performance.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-[fadeIn_1.1s_ease-out]">
            <Link to={isAuthenticated ? '/setup' : '/register'} className="btn btn-primary shadow-lg shadow-indigo-500/30 text-lg px-8 py-3.5 rounded-xl group no-underline">
              Start Practice Session
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link to={isAuthenticated ? '/dashboard' : '/login'} className="btn bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 text-lg px-8 py-3.5 rounded-xl shadow-sm no-underline">
              {isAuthenticated ? 'Go to Dashboard' : 'Log in to Account'}
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">The Open-Ended Adaptive Flow</h2>
            <p className="mt-4 text-lg text-slate-500 max-w-2xl mx-auto">No timers. No fixed questions. Just you and an AI that adapts perfectly to your skill level until you're ready to finish.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
            {[
              { icon: FileText, title: 'Upload & Parse', desc: 'We extract your core skills, frameworks, and projects instantly to build your candidate profile.', color: 'text-blue-600', bg: 'bg-blue-50' },
              { icon: Brain, title: 'Adaptive Progression', desc: 'Questions scale from basic recall (Remember) to complex system design (Create) based strictly on your answers.', color: 'text-purple-600', bg: 'bg-purple-50' },
              { icon: Zap, title: 'Instant Evaluation', desc: 'Every answer gets scored across 5 dimensions, providing immediate actionable feedback to improve on the spot.', color: 'text-emerald-600', bg: 'bg-emerald-50' },
            ].map(({ icon: Icon, title, desc, color, bg }) => (
              <div key={title} className="flex flex-col items-center text-center p-6 rounded-2xl hover:bg-slate-50 border border-transparent hover:border-slate-100 transition-colors">
                <div className={`w-16 h-16 rounded-2xl ${bg} ${color} flex items-center justify-center mb-6 shadow-sm`}>
                  <Icon size={32} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">{title}</h3>
                <p className="text-slate-600 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-24 bg-slate-900 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl mb-4">Built With Production AI</h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-12">Not a simple wrapper. A fully engineered application utilizing modern retrieval augmented generation and vector search.</p>
          
          <div className="flex flex-wrap justify-center gap-4 max-w-4xl mx-auto">
            {['RAG Architecture', 'ChromaDB', 'SentenceTransformers', 'Groq Llama 3', 'FastAPI', 'React', 'Tailwind v4'].map(t => (
              <span key={t} className="px-5 py-2.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-semibold shadow-sm hover:bg-slate-700 hover:text-white transition-colors cursor-default">
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 text-indigo-600 font-bold text-lg">
            <BrainCircuit size={24} />
            <span className="text-slate-900">Smart<span className="text-indigo-600">Interview</span></span>
          </div>
          <div className="flex gap-8 text-sm font-medium text-slate-500">
            <Link to="#" className="hover:text-slate-900 transition-colors no-underline">Privacy</Link>
            <Link to="#" className="hover:text-slate-900 transition-colors no-underline">Terms</Link>
            <Link to="#" className="hover:text-slate-900 transition-colors no-underline">Contact</Link>
          </div>
          <div className="text-sm text-slate-400">
            © 2026 SmartInterview Platform.
          </div>
        </div>
      </footer>
      
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
