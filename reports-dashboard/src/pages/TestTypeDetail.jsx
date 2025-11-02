import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function TestTypeDetail() {
  const { testType } = useParams();
  const [reports, setReports] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const reportsPerPage = 10;

  useEffect(() => {
    loadData();
  }, [testType]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [reportsData, historyData] = await Promise.all([
        reportsApi.getReportsByType(testType, 50),
        reportsApi.getHistory(testType, 20)
      ]);
      // Sort reports by timestamp (latest first)
      const sortedReports = (reportsData.reports || []).sort((a, b) =>
        new Date(b.timestamp) - new Date(a.timestamp)
      );
      setReports(sortedReports);
      setHistory(historyData.history);
      setError(null);
      setCurrentPage(1);
    } catch (err) {
      setError('Failed to load reports');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Pagination
  const indexOfLastReport = currentPage * reportsPerPage;
  const indexOfFirstReport = indexOfLastReport - reportsPerPage;
  const currentReports = reports.slice(indexOfFirstReport, indexOfLastReport);
  const totalPages = Math.ceil(reports.length / reportsPerPage);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-sky-400 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading {testType} reports...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <p className="text-red-700">{error}</p>
          <button
            onClick={loadData}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back Button */}
      <Link
        to="/"
        className="inline-flex items-center text-slate-600 hover:text-slate-700 mb-6 font-semibold"
      >
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 uppercase">{testType}</h1>
            <p className="text-gray-500 mt-2">Test History & Analytics</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Total Reports</div>
            <div className="text-3xl font-bold text-sky-500">{reports.length}</div>
          </div>
        </div>
      </div>

      {/* Historical Trend Chart */}
      {history.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">📈 Historical Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formatted_time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="summary.passed"
                stroke="#10b981"
                strokeWidth={2}
                name="Passed"
                dot={{ fill: '#10b981' }}
              />
              <Line
                type="monotone"
                dataKey="summary.failed"
                stroke="#ef4444"
                strokeWidth={2}
                name="Failed"
                dot={{ fill: '#ef4444' }}
              />
              <Line
                type="monotone"
                dataKey="summary.total"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Total"
                dot={{ fill: '#8b5cf6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Reports Grid */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800">📊 Test Reports</h2>
          <div className="text-sm text-gray-500">
            Showing {indexOfFirstReport + 1}-{Math.min(indexOfLastReport, reports.length)} of {reports.length} reports
          </div>
        </div>

        {reports.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <p className="text-gray-500">No reports available for {testType}</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {currentReports.map((report) => (
                <div
                  key={report.id}
                  className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-4"
                >
                  <div className="mb-3">
                    <div className="text-xs text-gray-500">
                      {new Date(report.timestamp).toLocaleString()}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-gray-800">{report.summary.total}</div>
                      <div className="text-xs text-gray-500">Tests</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">{report.summary.passed}</div>
                      <div className="text-xs text-gray-500">Passed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-red-600">{report.summary.failed}</div>
                      <div className="text-xs text-gray-500">Failed</div>
                    </div>
                  </div>

                  <div className="mb-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-600">Pass Rate</span>
                      <span className="font-semibold text-sky-500">{report.summary.pass_rate}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-sky-400 h-1.5 rounded-full transition-all"
                        style={{ width: report.summary.pass_rate }}
                      ></div>
                    </div>
                  </div>

                  <Link
                    to={`/report/${testType}/${report.id}`}
                    className="block w-full bg-sky-400 text-white py-2 px-3 rounded text-center text-sm font-semibold hover:bg-sky-500 transition"
                  >
                    View Report
                  </Link>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-center space-x-2">
                <button
                  onClick={() => paginate(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-2 rounded bg-white border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>

                {[...Array(totalPages)].map((_, index) => (
                  <button
                    key={index + 1}
                    onClick={() => paginate(index + 1)}
                    className={`px-3 py-2 rounded text-sm font-medium ${
                      currentPage === index + 1
                        ? 'bg-sky-400 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {index + 1}
                  </button>
                ))}

                <button
                  onClick={() => paginate(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 rounded bg-white border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default TestTypeDetail;
