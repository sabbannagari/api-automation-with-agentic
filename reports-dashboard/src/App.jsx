import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import TestTypeDetail from './pages/TestTypeDetail';
import ReportViewer from './pages/ReportViewer';
import './App.css';

function Header() {
  return (
    <nav className="bg-gradient-to-r from-slate-700 to-slate-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition">
          <span className="text-3xl">📊</span>
          <div>
            <h1 className="text-2xl font-bold">Test Reports Dashboard</h1>
            <p className="text-slate-300 text-sm">Automated API Testing Framework</p>
          </div>
        </Link>
      </div>
    </nav>
  );
}

function AppContent() {
  const location = useLocation();
  const isReportViewerRoute = location.pathname.startsWith('/report/');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Show header for all routes except report viewer */}
      {!isReportViewerRoute && <Header />}

      {/* Routes */}
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/test-type/:testType" element={<TestTypeDetail />} />
        <Route path="/report/:testType/:reportId" element={<ReportViewer />} />
      </Routes>

      {/* Footer - hide on report viewer */}
      {!isReportViewerRoute && (
        <footer className="bg-gray-800 text-white py-6 mt-12">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p className="text-gray-300">Test Reports Dashboard - Automated API Testing Framework</p>
            <p className="text-gray-400 text-sm mt-2">Generated with ❤️ by Claude Code</p>
          </div>
        </footer>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
