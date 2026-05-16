'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, Youtube, Play, TrendingUp, Sparkles, Layout, 
  Settings, LogOut, Search, Plus, MoreVertical, Clock, CheckCircle2,
  Loader2, AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api, Project } from '../../lib/api';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [url, setUrl] = useState('');
  const [activeTab, setActiveTab] = useState('projects');
  const [isProcessing, setIsProcessing] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) return;
    
    const loadProjects = async () => {
      try {
        const data = await api.getProjects();
        setProjects(data);
      } catch (err) {
        console.error('Failed to load projects:', err);
      }
    };

    loadProjects();

    // Poll for updates every 5 seconds if any project is not completed
    const interval = setInterval(() => {
      const hasPending = projects.some(p => p.status !== 'completed' && p.status !== 'failed');
      if (hasPending) {
        loadProjects();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [user, projects]);

  const handleImport = async () => {
    if (!url) return;
    setIsProcessing(true);
    setError('');
    
    try {
      const response = await api.processVideo(url);
      
      // Add a temporary "Processing" project to the list
      const newProject: Project = {
        id: response.project_id,
        title: 'New YouTube Clip',
        status: response.status,
        progress_percent: 0,
      };
      setProjects([newProject, ...projects]);
      setUrl('');
    } catch (err: any) {
      console.error('Import failed:', err);
      setError(err.message || 'Failed to start processing');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!user) return null; // AuthContext handles redirect

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-purple-500/30">
      {/* Background Decor */}
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-purple-600/5 blur-[120px] pointer-events-none" />

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-72 border-r border-white/5 bg-black/40 backdrop-blur-3xl z-50 p-8 flex flex-col">
        <div className="flex items-center space-x-3 mb-16 px-2">
          <div className="w-9 h-9 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Sparkles size={18} fill="white" className="text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight">ViralClips AI</span>
        </div>

        <nav className="flex-1 space-y-2">
          <div className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-6 px-4">Workspace</div>
          {[
            { id: 'projects', icon: Layout, label: 'My Projects' },
            { id: 'templates', icon: Sparkles, label: 'AI Templates' },
            { id: 'analytics', icon: TrendingUp, label: 'Analytics' },
          ].map((item) => (
            <button 
              key={item.id} 
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-2xl transition-all duration-300 group ${activeTab === item.id ? 'bg-white/10 text-white shadow-xl shadow-black/50' : 'text-gray-500 hover:text-white hover:bg-white/5'}`}
            >
              <item.icon size={20} className={activeTab === item.id ? 'text-purple-400' : 'group-hover:text-purple-400'} />
              <span className="font-semibold text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto space-y-2 pt-8 border-t border-white/5">
          <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-gray-500 hover:text-white hover:bg-white/5 transition-all">
            <Settings size={20} />
            <span className="font-semibold text-sm">Settings</span>
          </button>
          <button 
            onClick={logout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-red-500/50 hover:text-red-400 hover:bg-red-500/5 transition-all"
          >
            <LogOut size={20} />
            <span className="font-semibold text-sm">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="pl-72 min-h-screen">
        <header className="sticky top-0 z-40 bg-black/20 backdrop-blur-xl border-b border-white/5 px-12 py-6 flex justify-between items-center">
           <div className="flex items-center space-x-4 bg-white/5 border border-white/10 rounded-2xl px-4 py-2 w-96 group focus-within:border-purple-500/50 transition-all">
              <Search size={18} className="text-gray-500 group-focus-within:text-purple-400" />
              <input type="text" placeholder="Search projects..." className="bg-transparent border-none outline-none text-sm w-full text-white" />
           </div>

           <div className="flex items-center space-x-6">
              <div className="hidden lg:flex items-center space-x-3 text-sm px-4 py-2 bg-white/5 rounded-xl border border-white/10">
                 <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                 <span className="text-gray-400">Pro Plan</span>
              </div>
              <div className="flex items-center space-x-3">
                 <div className="text-right">
                    <div className="text-xs font-bold">{user.displayName || user.email?.split('@')[0]}</div>
                    <div className="text-[10px] text-gray-500">Creator</div>
                 </div>
                 {user.photoURL ? (
                    <img src={user.photoURL} className="w-10 h-10 rounded-full border border-white/10" alt="Profile" />
                 ) : (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-xs font-bold ring-2 ring-purple-500/20">
                       {user.email?.charAt(0).toUpperCase()}
                    </div>
                 )}
              </div>
           </div>
        </header>

        <div className="p-12 max-w-7xl mx-auto">
          <div className="flex justify-between items-end mb-12">
            <div>
              <h1 className="text-4xl font-black tracking-tight mb-2">Welcome Back</h1>
              <p className="text-gray-500">Manage and create viral shorts from your content.</p>
            </div>
            <button className="flex items-center space-x-2 px-6 py-3 bg-white text-black rounded-2xl font-bold hover:bg-gray-200 transition-all active:scale-95 shadow-xl shadow-white/5">
              <Plus size={20} />
              <span>New Project</span>
            </button>
          </div>

          {/* Creation Hub */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
            <motion.div 
              whileHover={{ y: -5 }}
              className="group relative p-10 rounded-[40px] bg-gradient-to-br from-white/[0.05] to-white/[0.01] border border-white/10 hover:border-purple-500/30 transition-all overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/10 blur-[80px] opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Upload className="text-purple-400" />
                </div>
                <h3 className="text-2xl font-bold mb-2">Upload Files</h3>
                <p className="text-gray-500 mb-8 leading-relaxed">Drag and drop raw footage up to 2GB. Supports MP4, MOV, and AVI.</p>
                <div className="flex items-center space-x-2 text-purple-400 font-bold text-sm cursor-pointer hover:underline">
                  <span>Browse local files</span>
                  <ArrowRight size={16} />
                </div>
              </div>
            </motion.div>

            <motion.div 
              whileHover={{ y: -5 }}
              className="group relative p-10 rounded-[40px] bg-gradient-to-br from-white/[0.05] to-white/[0.01] border border-white/10 hover:border-red-500/30 transition-all overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/10 blur-[80px] opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="w-14 h-14 bg-red-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Youtube className="text-red-500" />
                </div>
                <h3 className="text-2xl font-bold mb-4">Import from YouTube</h3>
                <div className="flex flex-col space-y-3">
                  <div className="flex space-x-3">
                    <input 
                      type="text" 
                      placeholder="Paste link here..." 
                      className="flex-1 bg-black/50 border border-white/5 rounded-2xl px-6 py-3 focus:outline-none focus:border-red-500/50 transition-all text-sm"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                    />
                    <button 
                      onClick={handleImport}
                      disabled={isProcessing || !url}
                      className="px-8 py-3 bg-white text-black rounded-2xl font-bold text-sm hover:bg-gray-200 active:scale-95 transition-all disabled:opacity-50"
                    >
                      {isProcessing ? <Loader2 className="animate-spin" size={20} /> : 'Import'}
                    </button>
                  </div>
                  {error && (
                    <div className="flex items-center space-x-2 text-red-500 text-xs">
                      <AlertCircle size={14} />
                      <span>{error}</span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </section>

          {/* Project List */}
          <section>
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-bold flex items-center space-x-2">
                <Clock size={20} className="text-gray-500" />
                <span>Recent Activity</span>
              </h2>
              <button className="text-sm font-bold text-purple-400 hover:text-purple-300">View All</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
               {projects.map((project, i) => {
                 const isCompleted = project.status === 'completed';
                 const isFailed = project.status === 'failed';
                 
                 return (
                 <motion.div 
                   key={project.id || i}
                   initial={{ opacity: 0, scale: 0.9 }}
                   animate={{ opacity: 1, scale: 1 }}
                   transition={{ delay: i * 0.1 }}
                   className="group bg-white/[0.02] rounded-[32px] border border-white/5 hover:border-white/10 overflow-hidden transition-all duration-500 flex flex-col"
                 >
                   <div className={`aspect-video bg-gradient-to-br from-purple-900/40 to-black relative flex items-center justify-center`}>
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-[2px] flex items-center justify-center gap-4">
                         <button className="w-12 h-12 bg-white text-black rounded-full flex items-center justify-center hover:scale-110 transition-transform">
                            <Play fill="black" size={20} />
                         </button>
                      </div>
                      <Layout className="text-white/10 group-hover:scale-110 transition-transform duration-700" size={60} />
                   </div>
                   
                   <div className="p-8 flex-1 flex flex-col">
                      <div className="flex justify-between items-start mb-4">
                         <div>
                            <h4 className="font-bold text-lg mb-1">{project.title}</h4>
                            <div className="flex items-center space-x-2 text-xs text-gray-500">
                               <span className="flex items-center space-x-1">
                                  <Clock size={12} />
                                  <span>Recent</span>
                               </span>
                            </div>
                         </div>
                         <button className="text-gray-500 hover:text-white">
                            <MoreVertical size={20} />
                         </button>
                      </div>

                      <div className="mt-auto pt-6 border-t border-white/5">
                         {isFailed ? (
                            <div className="flex flex-col space-y-2">
                               <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-red-500/10 text-red-500 w-fit">
                                  <AlertCircle size={12} />
                                  <span>Failed</span>
                               </div>
                               <span className="text-xs text-red-400 truncate">{project.error_message}</span>
                            </div>
                         ) : isCompleted ? (
                            <div className="flex items-center justify-between">
                               <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-green-500/10 text-green-500">
                                  <CheckCircle2 size={12} />
                                  <span>Completed</span>
                               </div>
                               <button className="text-xs font-bold text-gray-400 hover:text-white transition-colors">View Clips</button>
                            </div>
                         ) : (
                            <div className="space-y-3">
                               <div className="flex items-center justify-between text-xs font-bold">
                                  <span className="text-orange-400 capitalize">{project.status}...</span>
                                  <span className="text-gray-400">{project.progress_percent}%</span>
                               </div>
                               <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                  <div 
                                     className="h-full bg-gradient-to-r from-orange-500 to-purple-500 transition-all duration-500 ease-out"
                                     style={{ width: `${project.progress_percent}%` }}
                                  />
                               </div>
                            </div>
                         )}
                      </div>
                   </div>
                 </motion.div>
               )})}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function ArrowRight({ size, className }: { size?: number, className?: string }) {
  return (
    <svg 
      width={size || 24} 
      height={size || 24} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}
