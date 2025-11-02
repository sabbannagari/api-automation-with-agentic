import { useParams, Link, useNavigate } from 'react-router-dom';
import { reportsApi } from '../api/reports';

function ReportViewer() {
  const { testType, reportId } = useParams();
  const navigate = useNavigate();

  const reportUrl = reportsApi.getHtmlReportUrl(testType, reportId);

  return (
    <div className="h-screen flex flex-col">
      {/* Header with navigation */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(-1)}
                className="inline-flex items-center text-white hover:text-slate-200 transition"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="font-semibold">Back</span>
              </button>
              <div className="h-6 w-px bg-white/30"></div>
              <Link to="/" className="hover:text-slate-200 transition font-semibold">
                🏠 Dashboard
              </Link>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-sm text-slate-300">Viewing Report:</span>
              <span className="bg-white/20 backdrop-blur px-3 py-1 rounded-full text-sm font-semibold uppercase">
                {testType}
              </span>
              <a
                href={reportUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center bg-white/20 hover:bg-white/30 backdrop-blur px-3 py-1 rounded-lg text-sm font-semibold transition"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Open in New Tab
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* iFrame container */}
      <div className="flex-1 bg-gray-100">
        <iframe
          src={reportUrl}
          className="w-full h-full border-0"
          title={`${testType} Test Report ${reportId}`}
        />
      </div>
    </div>
  );
}

export default ReportViewer;
