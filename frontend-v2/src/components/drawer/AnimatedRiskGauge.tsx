import React from 'react';
import { motion } from 'framer-motion';

interface AnimatedRiskGaugeProps {
  score: number;
  tier: string;
}

export const AnimatedRiskGauge: React.FC<AnimatedRiskGaugeProps> = ({ score, tier }) => {
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const isCritical = score >= 85;
  const isHigh = score >= 61 && score < 85;
  const isMedium = score >= 31 && score < 61;

  const strokeColor = isCritical
    ? '#ef4444'
    : isHigh
    ? '#f97316'
    : isMedium
    ? '#f59e0b'
    : '#64748b';

  const tierLabel = isCritical
    ? 'CRITICAL RISK'
    : isHigh
    ? 'HIGH RISK'
    : isMedium
    ? 'MEDIUM RISK'
    : 'LOW RISK';

  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-2xl bg-space-900/90 border border-white/[0.08] shadow-2xl relative select-none">
      <div className="relative w-36 h-36 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
          {/* Background Track Circle */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="10"
            fill="transparent"
          />

          {/* Animated Value Arc */}
          <motion.circle
            cx="60"
            cy="60"
            r={radius}
            stroke={strokeColor}
            strokeWidth="10"
            fill="transparent"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            strokeLinecap="round"
            style={{
              filter: isCritical ? 'drop-shadow(0 0 10px rgba(239, 68, 68, 0.6))' : 'drop-shadow(0 0 8px rgba(14, 165, 233, 0.4))'
            }}
          />
        </svg>

        {/* Center Display Score */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <motion.span 
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-3xl font-extrabold font-mono text-white tracking-tight"
          >
            {(score ?? 0).toFixed(0)}
          </motion.span>
          <span className="text-[10px] font-mono text-slate-400 uppercase">SCORE / 100</span>
        </div>
      </div>

      <div className="mt-2 text-center">
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold font-mono uppercase tracking-wider ${
          isCritical
            ? 'bg-red-950/80 text-red-300 border border-red-500/40'
            : isHigh
            ? 'bg-orange-950/80 text-orange-300 border border-orange-500/40'
            : isMedium
            ? 'bg-amber-950/80 text-amber-300 border border-amber-500/40'
            : 'bg-slate-900 text-slate-400 border border-slate-700'
        }`}>
          {tierLabel}
        </span>
      </div>
    </div>
  );
};
