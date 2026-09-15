import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { User, Mail, Calendar, FileText, CheckCircle2, HelpCircle, Edit3, Save, X, Activity } from 'lucide-react';

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/users/profile')
      .then(res => {
        setProfile(res.data);
        setName(res.data.user.name);
      })
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await api.put('/users/profile', { name: name.trim() });
      setProfile(prev => ({ ...prev, user: { ...prev.user, name: name.trim() } }));
      setEditing(false);
    } catch {
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const u = profile?.user;
  const stats = profile?.stats;
  const resume = profile?.resume;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Account Profile</h1>
        <p className="text-slate-500 mt-1 text-base">Manage your personal information and preferences.</p>
      </div>

      {/* User Info */}
      <div className="card p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
          <div className="flex items-start gap-6">
            <div className="w-20 h-20 rounded-full bg-indigo-50 border-4 border-white shadow-md flex items-center justify-center flex-shrink-0 text-indigo-600">
              <User size={36} />
            </div>
            <div className="pt-2">
              {editing ? (
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
                  <input 
                    className="input py-1.5 px-3 max-w-xs font-semibold text-lg" 
                    value={name} 
                    onChange={e => setName(e.target.value)} 
                    autoFocus 
                  />
                  <div className="flex items-center gap-2">
                    <button onClick={handleSave} className="btn btn-primary py-1.5 px-3 shadow-sm text-sm" disabled={saving}>
                      {saving ? 'Saving...' : <><Save size={16} className="mr-1.5" /> Save</>}
                    </button>
                    <button onClick={() => { setEditing(false); setName(u.name); }} className="btn bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 py-1.5 px-3 text-sm">
                      <X size={16} className="mr-1.5" /> Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-2xl font-bold text-slate-900 mb-1">{u?.name}</div>
              )}
              
              <div className="flex flex-col gap-2 mt-3">
                <div className="flex items-center text-sm text-slate-600">
                  <Mail size={16} className="mr-2 text-slate-400" />
                  {u?.email}
                </div>
                
                {u?.created_at && (
                  <div className="flex items-center text-sm text-slate-600">
                    <Calendar size={16} className="mr-2 text-slate-400" />
                    Joined {new Date(u.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {!editing && (
            <button onClick={() => setEditing(true)} className="btn bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-sm text-sm px-4 py-2 mt-2 sm:mt-0">
              <Edit3 size={16} className="mr-2 text-slate-400" /> Edit Profile
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Stats */}
        <div className="card p-6 shadow-sm h-full flex flex-col">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
            <Activity size={20} className="text-indigo-600" /> Activity Overview
          </h2>
          <div className="grid grid-cols-2 gap-4 flex-1">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center text-center">
              <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-3">
                <FileText size={20} />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats?.total_interviews || 0}</div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Interviews</div>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center text-center">
              <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-3">
                <CheckCircle2 size={20} />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats?.completed_interviews || 0}</div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Completed</div>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center text-center">
              <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-3">
                <HelpCircle size={20} />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats?.total_questions || 0}</div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Questions</div>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center text-center">
              <div className="w-10 h-10 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-3">
                <Edit3 size={20} />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stats?.total_answered || 0}</div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Answered</div>
            </div>
          </div>
        </div>

        {/* Resume */}
        <div className="card p-6 shadow-sm h-full flex flex-col">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-6">
            <FileText size={20} className="text-indigo-600" /> Active Resume
          </h2>
          
          {resume ? (
            <div className="flex-1 flex flex-col">
              <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200 mb-6">
                <FileText size={24} className="text-slate-400" />
                <span className="font-semibold text-slate-700 truncate">{resume.filename}</span>
              </div>
              
              {resume.skills && resume.skills.length > 0 && (
                <div className="flex-1">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Extracted Skills ({resume.skills.length})</div>
                  <div className="flex flex-wrap gap-2">
                    {resume.skills.map(s => (
                      <span key={s} className="px-3 py-1.5 text-sm font-medium rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-slate-50 border-2 border-dashed border-slate-200 rounded-xl">
              <FileText size={40} className="text-slate-300 mb-4" />
              <p className="text-slate-500 font-medium mb-4">You haven't uploaded a resume yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
