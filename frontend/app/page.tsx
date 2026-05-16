'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Play, CheckCircle, ArrowRight, Video, Layers, Users, Star } from 'lucide-react';

export default function Home() {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-[#020202] text-white selection:bg-purple-500/30 overflow-x-hidden font-sans">
      {/* Background Glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-pink-900/10 blur-[120px] rounded-full pointer-events-none" />

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-black/20 backdrop-blur-2xl px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3 group cursor-pointer">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20 group-hover:scale-110 transition-transform">
              <Zap size={20} fill="white" className="text-white" />
            </div>
            <span className="font-bold text-2xl tracking-tighter bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">ViralClips AI</span>
          </div>
          
          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="#showcase" className="hover:text-white transition-colors">Showcase</a>
          </div>

          <div className="flex items-center space-x-4">
            <button className="hidden sm:block text-sm font-semibold text-gray-400 hover:text-white transition-all">Sign In</button>
            <Link href="/dashboard" className="px-6 py-2.5 bg-white text-black rounded-full font-bold hover:bg-gray-200 transition-all shadow-lg shadow-white/5 flex items-center space-x-2">
              <span>Try for Free</span>
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-40 pb-20 px-6">
        {/* Hero Section */}
        <motion.section 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-5xl mx-auto text-center space-y-10 mb-32"
        >
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs font-bold text-purple-400 tracking-widest uppercase">
            <Sparkles size={14} />
            <span>AI-Powered Virality at Scale</span>
          </div>
          
          <h1 className="text-6xl md:text-9xl font-black tracking-tighter leading-[0.9] lg:text-[150px]">
             CLIP. VIRAL. <br />
             <span className="bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent italic pr-4">REPEAT.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Stop wasting hours editing. Our AI automatically transforms long-form videos into high-retention, vertical shorts that dominate TikTok, Reels, and Shorts.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6">
            <Link href="/dashboard" className="w-full sm:w-auto px-10 py-5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl font-bold text-xl hover:scale-105 transition-all shadow-xl shadow-purple-500/30 group">
              Start Building Now
              <motion.span className="inline-block ml-2 group-hover:translate-x-1 transition-transform">?</motion.span>
            </Link>
            <button className="w-full sm:w-auto px-10 py-5 bg-white/5 border border-white/10 rounded-2xl font-bold text-xl hover:bg-white/10 transition-all flex items-center justify-center space-x-2">
              <Play size={20} />
              <span>Watch Demo</span>
            </button>
          </div>
        </motion.section>

        {/* Visual Showcase */}
        <motion.section 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-6xl mx-auto mb-40 relative group"
        >
           <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent z-10 rounded-3xl" />
           <div className="rounded-3xl border border-white/10 overflow-hidden shadow-2xl shadow-purple-500/10 bg-[#0A0A0A]">
              <div className="aspect-[16/9] w-full relative">
                 <div className="absolute inset-0 flex items-center justify-center">
                    <Video size={80} className="text-white/20 animate-pulse" />
                 </div>
                 {/* This would be the viralclips_ai_hero image */}
                 <div className="absolute bottom-10 left-10 z-20 space-y-2">
                    <div className="px-3 py-1 bg-purple-600 rounded-lg text-xs font-bold uppercase tracking-widest">Processing...</div>
                    <h2 className="text-3xl font-black">AI Face Tracking in 4K</h2>
                 </div>
              </div>
           </div>
        </motion.section>

        {/* Features Grid */}
        <section id="features" className="max-w-7xl mx-auto mb-40">
           <div className="text-center mb-20 space-y-4">
              <h2 className="text-4xl md:text-6xl font-black tracking-tight">The Creator Tool of the Future.</h2>
              <p className="text-gray-500 text-lg">Everything you need to automate your social media empire.</p>
           </div>

           <motion.div 
             variants={container}
             initial="hidden"
             whileInView="show"
             viewport={{ once: true }}
             className="grid grid-cols-1 md:grid-cols-3 gap-6"
           >
             {[
               { 
                 icon: Sparkles, 
                 title: 'AI Clip Detection', 
                 desc: 'Our Gemini-powered engine identifies the most emotional and high-impact moments in your footage.',
                 color: 'from-purple-500 to-blue-500'
               },
               { 
                 icon: Layers, 
                 title: 'Dynamic Captions', 
                 desc: 'High-impact, karaoke-style subtitles that increase viewer retention by up to 80%.',
                 color: 'from-pink-500 to-orange-500'
               },
               { 
                 icon: Users, 
                 title: 'Face Tracking', 
                 desc: 'Automatically keeps the speaker in a perfect 9:16 vertical crop, even when they move.',
                 color: 'from-cyan-500 to-emerald-500'
               }
             ].map((feature, i) => (
               <motion.div 
                 key={i} 
                 variants={item}
                 className="group p-10 rounded-[40px] bg-white/[0.03] border border-white/10 hover:bg-white/[0.06] hover:border-white/20 transition-all duration-500 relative overflow-hidden"
               >
                 <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 blur-3xl transition-opacity`} />
                 <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-8 shadow-lg`}>
                    <feature.icon size={28} className="text-white" />
                 </div>
                 <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
                 <p className="text-gray-400 leading-relaxed text-lg">{feature.desc}</p>
               </motion.div>
             ))}
           </motion.div>
        </section>

        {/* Social Proof */}
        <section className="max-w-5xl mx-auto text-center py-20 border-t border-white/5">
           <p className="text-sm font-bold text-gray-500 tracking-[0.2em] uppercase mb-12">Trusted by 10,000+ Content Creators</p>
           <div className="flex flex-wrap justify-center items-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all">
              <span className="text-3xl font-black tracking-tighter">FORBES</span>
              <span className="text-3xl font-black tracking-tighter">WIRED</span>
              <span className="text-3xl font-black tracking-tighter">THE VERGE</span>
              <span className="text-3xl font-black tracking-tighter">TECHCRUNCH</span>
           </div>
        </section>
      </main>

      <footer className="border-t border-white/5 py-20 px-6 bg-black">
         <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-12">
            <div className="col-span-2 space-y-6">
               <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                    <Zap size={16} fill="white" />
                  </div>
                  <span className="font-bold text-xl">ViralClips AI</span>
               </div>
               <p className="text-gray-500 max-w-sm leading-relaxed">
                  The #1 AI platform for automated short-form video production. Build your audience while you sleep.
               </p>
            </div>
            <div className="space-y-4">
               <h4 className="font-bold">Product</h4>
               <ul className="text-gray-500 space-y-2 text-sm">
                  <li>Features</li>
                  <li>Pricing</li>
                  <li>API</li>
               </ul>
            </div>
            <div className="space-y-4">
               <h4 className="font-bold">Legal</h4>
               <ul className="text-gray-500 space-y-2 text-sm">
                  <li>Privacy</li>
                  <li>Terms</li>
                  <li>Cookies</li>
               </ul>
            </div>
         </div>
         <div className="max-w-7xl mx-auto mt-20 pt-10 border-t border-white/5 text-center text-gray-600 text-xs">
            © 2026 ViralClips AI. All rights reserved.
         </div>
      </footer>
    </div>
  );
}
