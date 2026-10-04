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
          <Route path="/settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
};

