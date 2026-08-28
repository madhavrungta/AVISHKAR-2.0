import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { StatsPanel } from './components/StatsPanel';
import { FirmsMap } from './components/FirmsMap';
import { MapFilterBar } from './components/MapFilterBar';
import { EventDetailDrawer } from './components/EventDetailDrawer';
import { BottomAnalyticsPanel } from './components/BottomAnalyticsPanel';
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
  HealthStatus,
  MapFilters 
} from './types';

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

  // Layout UI State
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedObservation, setSelectedObservation] = useState<ThermalObservation | null>(null);
  const [selectedFacility, setSelectedFacility] = useState<IndustrialFacility | null>(null);

  // Map Filter State
  const [filters, setFilters] = useState<MapFilters>({
    satellite: 'ALL',
    minFrp: 0,
    maxFrp: 500,
    confidence: 'ALL',
    priority: 'ALL',
    facilityType: 'ALL',
    showAnomalies: true,
    showFacilities: true,
    showVectors: true,
    showEvents: true
  });

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

  const resetFilters = () => {
    setFilters({
      satellite: 'ALL',
      minFrp: 0,
      maxFrp: 500,
      confidence: 'ALL',
      priority: 'ALL',
      facilityType: 'ALL',
      showAnomalies: true,
      showFacilities: true,
      showVectors: true,
      showEvents: true
    });
  };

  useEffect(() => {
    refreshAll();
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      {/* Top Header */}
      <Header
        onRunEvaluator={triggerRiskJob}
        onRefresh={refreshAll}
        loading={loading}
        health={health}
      />

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Intelligence Sidebar */}
        <StatsPanel
          analytics={analytics}
          facilityAnalytics={facilityAnalytics}
          anomalySummary={anomalySummary}
          riskSummary={riskSummary}
          health={health}
          observations={observations}
          facilities={facilities}
          anomalies={anomalies}
          riskScores={riskScores}
          associations={associations}
          histories={histories}
          baselines={baselines}
          selectedObservation={selectedObservation}
          selectedFacility={selectedFacility}
          onSelectObservation={(obs) => {
            setSelectedObservation(obs);
            setSelectedFacility(null);
          }}
          onSelectFacility={(fac) => {
            setSelectedFacility(fac);
            setSelectedObservation(null);
          }}
          onIngestComplete={refreshAll}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Primary GIS Map Workspace */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative">
          {/* Floating Top Control Layer */}
          <div className="absolute top-3 left-3 z-[999] flex flex-col gap-2 max-w-md pointer-events-auto">
            <MapFilterBar
              filters={filters}
              onChangeFilters={setFilters}
              onResetFilters={resetFilters}
            />
          </div>

          {/* Leaflet Map Canvas */}
          <div className="flex-1 relative min-h-0">
            <FirmsMap
              observations={observations}
              facilities={facilities}
              associations={associations}
              classifications={classifications}
              histories={histories}
              baselines={baselines}
              anomalies={anomalies}
              riskScores={riskScores}
              filters={filters}
              loading={loading}
              selectedObservation={selectedObservation}
              selectedFacility={selectedFacility}
              onSelectObservation={(obs) => {
                setSelectedObservation(obs);
                setSelectedFacility(null);
              }}
              onSelectFacility={(fac) => {
                setSelectedFacility(fac);
                setSelectedObservation(null);
              }}
            />
          </div>

          {/* Collapsible Bottom Panel */}
          <BottomAnalyticsPanel
            selectedObservation={selectedObservation}
            selectedFacility={selectedFacility}
            observations={observations}
            facilities={facilities}
            associations={associations}
            classifications={classifications}
            histories={histories}
            baselines={baselines}
            anomalies={anomalies}
            riskScores={riskScores}
            onSelectObservation={(obs) => {
              setSelectedObservation(obs);
              setSelectedFacility(null);
            }}
          />

          {/* Right Intelligence Event Drawer */}
          {(selectedObservation || selectedFacility) && (
            <EventDetailDrawer
              selectedObservation={selectedObservation}
              selectedFacility={selectedFacility}
              associations={associations}
              classifications={classifications}
              histories={histories}
              baselines={baselines}
              anomalies={anomalies}
              riskScores={riskScores}
              facilities={facilities}
              onClose={() => {
                setSelectedObservation(null);
                setSelectedFacility(null);
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
