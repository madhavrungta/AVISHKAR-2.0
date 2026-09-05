import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Satellite, Radio, Globe2, ShieldCheck, Zap } from 'lucide-react';

interface InitLoaderProps {
  onComplete: () => void;
}

export const InitLoader: React.FC<InitLoaderProps> = ({ onComplete }) => {
  const [step, setStep] = useState(0);

  const steps = [
    { label: 'Connecting to Earth Observation Network', icon: Satellite },
    { label: 'Synchronizing VIIRS / MODIS Telemetry', icon: Radio },
    { label: 'Loading Geospatial Facility Baselines', icon: Globe2 },
    { label: 'Initializing Intelligence Workspace', icon: ShieldCheck }
  ];

  useEffect(() => {
    const timer1 = setTimeout(() => setStep(1), 300);
    const timer2 = setTimeout(() => setStep(2), 650);
    const timer3 = setTimeout(() => setStep(3), 950);
    const timerComplete = setTimeout(() => onComplete(), 1300);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timerComplete);
    };
  }, [onComplete]);

  const CurrentIcon = steps[step].icon;

  return (
    <motion.div 
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.02 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed inset-0 z-[9999] bg-[#060913] flex flex-col items-center justify-center text-slate-100 select-none overflow-hidden"
    >
      {/* Background Radial Atmosphere Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(14,165,233,0.12)_0%,rgba(6,9,19,0.98)_70%)] pointer-events-none" />
      
      {/* Central Brand Badge */}
      <motion.div 
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative z-10 flex flex-col items-center gap-6"
      >
        <div className="relative">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center shadow-glow-cyan">
            <CurrentIcon className="w-10 h-10 text-cyan-400 animate-pulse" />
          </div>
          {/* Animated Orbital Ring */}
          <div className="absolute -inset-2.5 rounded-3xl border border-cyan-500/20 animate-spin" style={{ animationDuration: '8s' }} />
        </div>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 text-xs font-semibold tracking-wider uppercase mb-2 font-mono">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>NTRO · SIH 26162</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white font-display">
            AVISHKAR <span className="text-cyan-400">2.0</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">Satellite Intelligence & Geospatial Surveillance</p>
        </div>

        {/* Step Progress Bar & Label */}
        <div className="w-72 sm:w-80 flex flex-col gap-2 mt-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="text-cyan-300 font-medium">{steps[step].label}</span>
            <span>{Math.round(((step + 1) / steps.length) * 100)}%</span>
          </div>
          <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden border border-slate-800">
            <motion.div 
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: `${((step + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            />
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
