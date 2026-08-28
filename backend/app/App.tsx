import React, { useState, useEffect } from 'react';
import { FirmsMap } from './components/FirmsMap';
import { StatsPanel } from './components/StatsPanel';
import { IngestionControl } from './components/IngestionControl';
import { 
  ThermalObservation, 
  IndustrialFacility, 
  ThermalFacilityAssociation,
  ThermalClassification,
  FacilityHistoricalBehavior,
  FacilityNormalBaseline,
  AbnormalThermalEvent,
  VerificationRiskScore,
  AnalyticsSummary, 
  FacilityAnalyticsSummary, 
  ClassificationSummary,
  HistorySummary,
  BaselineSummary,
  AnomalySummary,
  RiskSummary,
  HealthStatus 
} from './types';
import { AlertCircle, RefreshCw, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [observations, setObservations] = useState<ThermalObservation[]>([]);
  const [facilities, setFacilities] = useState<IndustrialFacility[]>([]);
  const [associations, setAssociations] = useState<ThermalFacilityAssociation[]>([]);
  const [classifications, setClassifications] = useState<ThermalClassification[]>([]);
  const [histories, setHistories] = useState<FacilityHistoricalBehavior[]>([]);
  const [baselines, setBaselines] = useState<FacilityNormalBaseline[]>([]);
  const [anomalies, setAnomalies] = useState<AbnormalThermalEvent[]>([]);
  const [riskScores, setRiskScores] = useState<VerificationRiskScore[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [facilityAnalytics, setFacilityAnalytics] = useState<FacilityAnalyticsSummary | null>(null);
  const [classificationSummary, setClassificationSummary] = useState<ClassificationSummary | null>(null);
  const [historySummary, setHistorySummary] = useState<HistorySummary | null>(null);
  const [baselineSummary, setBaselineSummary] = useState<BaselineSummary | null>(null);
  const [anomalySummary, setAnomalySummary] = useState<AnomalySummary | null>(null);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) setHealth(await res.json());
    } catch (e) {
      console.error('Failed to fetch health status', e);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics/summary');
      if (res.ok) setAnalytics(await res.json());
    } catch (e) {
      console.error('Failed to fetch thermal analytics', e);
    }
  };

  const fetchFacilityAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics/facilities-summary');
      if (res.ok) setFacilityAnalytics(await res.json());
    } catch (e) {
      console.error('Failed to fetch facility analytics', e);
    }
  };

  const fetchClassificationSummary = async () => {
    try {
      const res = await fetch('/api/analytics/classification-summary');
      if (res.ok) setClassificationSummary(await res.json());
    } catch (e) {
      console.error('Failed to fetch classification summary', e);
    }
  };

  const fetchHistorySummary = async () => {
    try {
      const res = await fetch('/api/analytics/historical-summary');
      if (res.ok) setHistorySummary(await res.json());
    } catch (e) {
      console.error('Failed to fetch history summary', e);
    }
  };

  const fetchBaselineSummary = async () => {
    try {
      const res = await fetch('/api/analytics/baselines-summary');
      if (res.ok) setBaselineSummary(await res.json());
    } catch (e) {
      console.error('Failed to fetch baseline summary', e);
    }
  };

  const fetchAnomalySummary = async () => {
    try {
      const res = await fetch('/api/analytics/anomalies-summary');
      if (res.ok) setAnomalySummary(await res.json());
    } catch (e) {
      console.error('Failed to fetch anomaly summary', e);
    }
  };

  const fetchRiskSummary = async () => {
    try {
      const res = await fetch('/api/analytics/risk-summary');
      if (res.ok) setRiskSummary(await res.json());
    } catch (e) {
      console.error('Failed to fetch risk summary', e);
    }
  };

  const fetchObservations = async () => {
    try {
      const res = await fetch('/api/thermal-observations?limit=1000');
      if (res.ok) setObservations(await res.json());
    } catch (e) {
      console.error('Failed to fetch thermal observations', e);
    }
  };

  const fetchFacilities = async () => {
    try {
      const res = await fetch('/api/industrial-facilities?limit=1000');
      if (res.ok) setFacilities(await res.json());
    } catch (e) {
      console.error('Failed to fetch industrial facilities', e);
    }
  };

  const fetchAssociations = async () => {
    try {
      const res = await fetch('/api/associations?limit=1000');
      if (res.ok) setAssociations(await res.json());
    } catch (e) {
      console.error('Failed to fetch facility associations', e);
    }
  };

  const fetchClassifications = async () => {
    try {
      const res = await fetch('/api/classification?limit=1000');
      if (res.ok) setClassifications(await res.json());
    } catch (e) {
      console.error('Failed to fetch classifications', e);
    }
  };

  const fetchHistories = async () => {
    try {
      const res = await fetch('/api/history?limit=1000');
      if (res.ok) setHistories(await res.json());
    } catch (e) {
      console.error('Failed to fetch facility histories', e);
    }
  };

  const fetchBaselines = async () => {
    try {
      const res = await fetch('/api/baselines?limit=1000');
      if (res.ok) setBaselines(await res.json());
    } catch (e) {
      console.error('Failed to fetch facility baselines', e);
    }
  };

  const fetchAnomalies = async () => {
    try {
      const res = await fetch('/api/anomalies?limit=1000');
      if (res.ok) setAnomalies(await res.json());
    } catch (e) {
      console.error('Failed to fetch abnormal events', e);
    }
  };

  const fetchRiskScores = async () => {
    try {
      const res = await fetch('/api/risk?limit=1000');
      if (res.ok) setRiskScores(await res.json());
    } catch (e) {
      console.error('Failed to fetch risk scores', e);
    }
  };

  const refreshAll = async () => {
    setLoading(true);
    await Promise.all([
      fetchHealth(),
      fetchAnalytics(),
      fetchFacilityAnalytics(),
      fetchClassificationSummary(),
      fetchHistorySummary(),
      fetchBaselineSummary(),
      fetchAnomalySummary(),
      fetchRiskSummary(),
      fetchObservations(),
      fetchFacilities(),
      fetchAssociations(),
      fetchClassifications(),
      fetchHistories(),
      fetchBaselines(),
      fetchAnomalies(),
      fetchRiskScores()
    ]);
    setLoading(false);
  };

  const triggerRiskJob = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/risk/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recalculate_all: true })
      });
      if (res.ok) {
        await refreshAll();
      }
    } catch (e) {
      console.error('Failed to trigger risk evaluation job', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Header */}
      <header className="h-12 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="font-extrabold text-amber-500 tracking-wider text-sm flex items-center gap-1.5">
            🔥 NTRO SIH-26162
          </span>
          <span className="text-slate-600">|</span>
          <h2 className="text-xs font-semibold text-slate-300">
            Phase 8: Multi-Modal Satellite Verification & Risk Scoring Pipeline
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={triggerRiskJob}
            className="px-2.5 py-1 text-xs rounded bg-purple-900/80 hover:bg-purple-800 border border-purple-500/40 text-purple-200 transition-colors flex items-center gap-1 font-medium shadow"
            title="Evaluate Multi-Modal Risk Scores & Optical Verification"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Run Multi-Modal Risk Evaluator</span>
          </button>

          <div className="bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] px-2.5 py-0.5 rounded-full flex items-center gap-1 font-medium">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Thermal Anomaly ≠ Confirmed Fire</span>
          </div>

          <button
            onClick={refreshAll}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Refresh All Data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Main Viewport */}
      <div className="flex flex-1 overflow-hidden relative">
        <StatsPanel 
          analytics={analytics} 
          facilityAnalytics={facilityAnalytics}
          associations={associations} 
          classificationSummary={classificationSummary}
          historySummary={historySummary}
          baselineSummary={baselineSummary}
          anomalySummary={anomalySummary}
          riskSummary={riskSummary}
          health={health} 
        />

        <div className="flex-1 flex flex-col relative overflow-hidden">
          <div className="absolute top-4 left-4 z-[999] max-w-lg w-full">
            <IngestionControl
              onIngestComplete={refreshAll}
              apiKeyConfigured={health?.firms_api_key_configured ?? false}
            />
          </div>

          <FirmsMap 
            observations={observations} 
            facilities={facilities} 
            associations={associations}
            classifications={classifications}
            histories={histories}
            baselines={baselines}
            anomalies={anomalies}
            riskScores={riskScores}
            loading={loading} 
          />
        </div>
      </div>
    </div>
  );
};

export default App;
