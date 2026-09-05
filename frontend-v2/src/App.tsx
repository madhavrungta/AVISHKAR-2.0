import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { InitLoader } from './components/layout/InitLoader';
import { TopNav } from './components/layout/TopNav';
import { Sidebar } from './components/layout/Sidebar';
import { MapWorkspace } from './components/map/MapWorkspace';
import { FloatingMapControls } from './components/map/FloatingMapControls';
import { ReconLegend } from './components/map/ReconLegend';
import { EventDetailDrawer } from './components/drawer/EventDetailDrawer';
import { BottomAnalyticsPanel } from './components/analytics/BottomAnalyticsPanel';
import { AIInvestigationTerminal } from './components/ai/AIInvestigationTerminal';

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
  RiskSummary, 
  HealthStatus, 
  MapFilters,
  ImpactAssessmentResponse
} from './types';
import { getApiUrl } from './services/api';

export const App: React.FC = () => {
  const [initCompleted, setInitCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [evaluatingRisk, setEvaluatingRisk] = useState(false);

  // Data States
  const [observations, setObservations] = useState<ThermalObservation[]>([]);
  const [facilities, setFacilities] = useState<IndustrialFacility[]>([]);
  const [associations, setAssociations] = useState<ThermalFacilityAssociation[]>([]);
  const [classifications, setClassifications] = useState<ThermalClassification[]>([]);
  const [histories, setHistories] = useState<FacilityHistoricalBehavior[]>([]);
  const [baselines, setBaselines] = useState<FacilityNormalBaseline[]>([]);
  const [anomalies, setAnomalies] = useState<AbnormalThermalEvent[]>([]);
  const [riskScores, setRiskScores] = useState<VerificationRiskScore[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  // Impact Assessment States
  const [impactData, setImpactData] = useState<ImpactAssessmentResponse | null>(null);
  const [loadingImpact, setLoadingImpact] = useState<boolean>(false);
  const [errorImpact, setErrorImpact] = useState<string | null>(null);
  const [impactRadius, setImpactRadius] = useState<number>(5.0);

  // Selection & UI States
  const [selectedObservation, setSelectedObservation] = useState<ThermalObservation | null>(null);
  const [selectedFacility, setSelectedFacility] = useState<IndustrialFacility | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiTargetObsId, setAiTargetObsId] = useState<number | null>(null);

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

  // Fetch all endpoints from existing FastAPI backend
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      const [
        resObs,
        resFac,
        resAssoc,
        resClass,
        resHist,
        resBase,
        resAnom,
        resRisk,
        resAnalytics,
        resRiskSum,
        resHealth
      ] = await Promise.all([
        fetch(getApiUrl('/api/thermal-observations?limit=1000')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/industrial-facilities?limit=500')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/associations')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/classification')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/history')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/baselines')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/anomalies')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/risk')).then(r => r.ok ? r.json() : []),
        fetch(getApiUrl('/api/analytics/summary')).then(r => r.ok ? r.json() : null),
        fetch(getApiUrl('/api/risk/summary')).then(r => r.ok ? r.json() : null),
        fetch(getApiUrl('/api/health')).then(r => r.ok ? r.json() : null)
      ]);

      setObservations(resObs);
      setFacilities(resFac);
      setAssociations(resAssoc);
      setClassifications(resClass);
      setHistories(resHist);
      setBaselines(resBase);
      setAnomalies(resAnom);
      setRiskScores(resRisk);
      setAnalytics(resAnalytics);
      setRiskSummary(resRiskSum);
      setHealth(resHealth);
    } catch (err) {
      console.error('Error fetching satellite intelligence data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Fetch Impact Assessment whenever selectedObservation or impactRadius changes with AbortController race-condition protection
  const fetchImpactAssessment = useCallback(() => {
    if (!selectedObservation) {
      setImpactData(null);
      setErrorImpact(null);
      setLoadingImpact(false);
      return;
    }

    const controller = new AbortController();
    setLoadingImpact(true);
    setErrorImpact(null);

    fetch(getApiUrl(`/api/impact/${selectedObservation.id}?assessment_radius_km=${impactRadius}`), {
      signal: controller.signal
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then((data: ImpactAssessmentResponse) => {
        setImpactData(data);
        setLoadingImpact(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Impact assessment fetch error:', err);
          setErrorImpact('Impact Assessment API Unavailable');
          setLoadingImpact(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [selectedObservation?.id, impactRadius]);

  useEffect(() => {
    const cleanup = fetchImpactAssessment();
    return () => {
      if (cleanup) cleanup();
    };
  }, [fetchImpactAssessment]);

  // Execute Phase 7 Risk Scoring Endpoint
  const handleRunRiskEvaluation = async () => {
    setEvaluatingRisk(true);
    try {
      const res = await fetch(getApiUrl('/api/risk/evaluate'), { method: 'POST' });
      if (res.ok) {
        await fetchAllData();
      }
    } catch (err) {
      console.error('Error executing risk evaluation:', err);
    } finally {
      setEvaluatingRisk(false);
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

  return (
    <div className="h-screen w-screen flex flex-col bg-[#060913] text-slate-100 overflow-hidden font-sans">
      {/* 1. Initial Launch Sequence */}
      <AnimatePresence>
        {!initCompleted && (
          <InitLoader onComplete={() => setInitCompleted(true)} />
        )}
      </AnimatePresence>

      {/* 2. Top Navigation Bar */}
      <TopNav
        health={health}
        riskSummary={riskSummary}
        onOpenAI={() => {
          setAiTargetObsId(selectedObservation?.id || (observations[0]?.id ?? null));
          setAiModalOpen(true);
        }}
        onRefresh={fetchAllData}
        onRunRiskEvaluation={handleRunRiskEvaluation}
        loading={loading}
        evaluatingRisk={evaluatingRisk}
      />

      {/* 3. Main Workspace Body */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar */}
        <Sidebar
          observations={observations}
          facilities={facilities}
          anomalies={anomalies}
          riskScores={riskScores}
          associations={associations}
          histories={histories}
          baselines={baselines}
          riskSummary={riskSummary}
          analytics={analytics}
          health={health}
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
          onIngestComplete={fetchAllData}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Primary Map Workspace */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative">
          {/* Floating Map Filter Bar */}
          <div className="absolute top-4 left-4 z-20 pointer-events-auto">
            <FloatingMapControls
              filters={filters}
              onChangeFilters={setFilters}
              onResetFilters={resetFilters}
            />
          </div>

          {/* Leaflet Map Canvas */}
          <div className="flex-1 relative min-h-0 overflow-hidden">
            <MapWorkspace
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
              impactData={impactData}
              impactRadius={impactRadius}
              onSelectObservation={(obs) => {
                setSelectedObservation(obs);
                setSelectedFacility(null);
              }}
              onSelectFacility={(fac) => {
                setSelectedFacility(fac);
                setSelectedObservation(null);
              }}
            />

            {/* Bottom-Left Recon Legend Overlay */}
            <div className="absolute bottom-4 left-4 z-20 pointer-events-auto">
              <ReconLegend />
            </div>
          </div>

          {/* Collapsible Bottom Baseline & Timeline Panel */}
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

          {/* Right Investigation Event Drawer */}
          <AnimatePresence>
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
                impactData={impactData}
                loadingImpact={loadingImpact}
                errorImpact={errorImpact}
                impactRadius={impactRadius}
                onChangeImpactRadius={(radius) => setImpactRadius(radius)}
                onRetryImpact={fetchImpactAssessment}
                onClose={() => {
                  setSelectedObservation(null);
                  setSelectedFacility(null);
                }}
                onOpenAIWithContext={(obsId) => {
                  setAiTargetObsId(obsId);
                  setAiModalOpen(true);
                }}
              />
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* 4. AI Cyber-Intelligence Terminal Modal */}
      <AnimatePresence>
        {aiModalOpen && (
          <AIInvestigationTerminal
            isOpen={aiModalOpen}
            onClose={() => setAiModalOpen(false)}
            selectedObservationId={aiTargetObsId}
            observations={observations}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default App;
