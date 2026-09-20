import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileText, Clock, BarChart3, LogOut, BrainCircuit, Menu, X, User, BookOpen } from 'lucide-react';
import { useState } from 'react';

const mainMenuItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/setup', label: 'Start Interview', icon: BookOpen },
  { to: '/history', label: 'Interviews', icon: Clock },
  { to: '/resume', label: 'Resume & Skills', icon: FileText },
  { to: '/performance', label: 'Analytics', icon: BarChart3 },
  { to: '/profile', label: 'Profile', icon: User },
];

export default function Sidebar() {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!isAuthenticated) return null;

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white border-r border-slate-200 w-64">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100">
        <Link to="/dashboard" className="flex items-center gap-2 text-indigo-600 font-bold text-xl tracking-tight no-underline">
          <BrainCircuit size={28} className="text-indigo-600" />
          <span className="text-slate-900">Smart<span className="text-indigo-600">Interview</span></span>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto py-6 flex flex-col gap-8">
        {/* Main Menu */}
        <div className="px-4">
          <h3 className="px-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Main Menu</h3>
          <div className="space-y-1">
            {mainMenuItems.map(({ to, label, icon: Icon }) => {
              const isActive = to.includes('?') 
                ? location.pathname + location.search === to
                : (location.pathname.startsWith(to) && to !== '/dashboard') || (to === '/dashboard' && location.pathname === '/dashboard');
              return (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors no-underline ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <Icon size={18} className={isActive ? 'text-indigo-600' : 'text-slate-400'} />
                  {label}
                  {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-600"></div>}
                </Link>
              );
            })}
          </div>
        </div>


      </div>

      {/* User Profile Footer */}
      <div className="p-4 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="truncate">
              <div className="text-sm font-bold text-slate-900 truncate">{user?.name}</div>
              <div className="text-xs font-medium text-slate-500 truncate">{user?.email}</div>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors cursor-pointer bg-transparent border-none flex-shrink-0"
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Header / Hamburger */}
      <div className="md:hidden flex items-center justify-between bg-white border-b border-slate-200 px-4 h-16">
        <Link to="/dashboard" className="flex items-center gap-2 text-indigo-600 font-bold text-xl tracking-tight no-underline">
          <BrainCircuit size={24} className="text-indigo-600" />
          <span className="text-slate-900">Smart<span className="text-indigo-600">Interview</span></span>
        </Link>
        <button 
          onClick={() => setMobileOpen(true)}
          className="p-2 text-slate-500 hover:bg-slate-100 rounded-md bg-transparent border-none"
        >
          <Menu size={24} />
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-slate-900/50" onClick={() => setMobileOpen(false)}></div>
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
            <div className="absolute top-0 right-0 -mr-12 pt-4">
              <button
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white bg-transparent border-none cursor-pointer"
                onClick={() => setMobileOpen(false)}
              >
                <X size={24} className="text-white" />
              </button>
            </div>
            <SidebarContent />
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <div className="hidden md:flex flex-col h-screen sticky top-0">
        <SidebarContent />
      </div>
    </>
  );
}
