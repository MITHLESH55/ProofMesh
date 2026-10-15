import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../layouts/Layout';
import { Login } from '../pages/Login';
import { Register } from '../pages/Register';
import { Dashboard } from '../pages/Dashboard';
import { Repositories } from '../pages/Repositories';
import { RepositoryDetail } from '../pages/RepositoryDetail';
import { Changes } from '../pages/Changes';
import { ChangeDetail } from '../pages/ChangeDetail';
import { Settings } from '../pages/Settings';
import { DependencyGraph } from '../pages/DependencyGraph';
import { AssuranceView } from '../pages/AssuranceView';
import { RuntimeAssurance } from '../pages/RuntimeAssurance';
import { EnterpriseOverview } from '../pages/EnterpriseOverview';
import { EnterpriseGraph } from '../pages/EnterpriseGraph';
import { AgentCenter } from '../pages/AgentCenter';
import { AgentTaskDetail } from '../pages/AgentTaskDetail';
import { ApprovalCenter } from '../pages/ApprovalCenter';
import { RemediationCenter } from '../pages/RemediationCenter';
import { HistoricalEvidence } from '../pages/HistoricalEvidence';
import { ChangeProofV3View } from '../pages/ChangeProofV3View';

export const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/repositories" element={<Repositories />} />
          <Route path="/repositories/:id" element={<RepositoryDetail />} />
          <Route path="/changes" element={<Changes />} />
          <Route path="/changes/:id" element={<ChangeDetail />} />
          <Route path="/graph" element={<DependencyGraph />} />
          <Route path="/graph/:repoId" element={<DependencyGraph />} />
          <Route path="/assurance/:id" element={<AssuranceView />} />
          <Route path="/runtime" element={<RuntimeAssurance />} />
          <Route path="/enterprise" element={<EnterpriseOverview />} />
          <Route path="/enterprise/graph" element={<EnterpriseGraph />} />
          <Route path="/agents" element={<AgentCenter />} />
          <Route path="/agents/tasks" element={<AgentTaskDetail />} />
          <Route path="/agents/tasks/:taskId" element={<AgentTaskDetail />} />
          <Route path="/approvals" element={<ApprovalCenter />} />
          <Route path="/remediation" element={<RemediationCenter />} />
          <Route path="/evidence" element={<HistoricalEvidence />} />
          <Route path="/proof-v3" element={<ChangeProofV3View />} />
          <Route path="/proof-v3/:changeId" element={<ChangeProofV3View />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
};


