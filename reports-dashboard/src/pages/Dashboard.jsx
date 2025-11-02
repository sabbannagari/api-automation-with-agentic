import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const TEST_TYPE_COLORS = {
  integration: 'from-sky-300 to-sky-400',
  system: 'from-teal-300 to-teal-400',
  component: 'from-blue-300 to-blue-400',
  regression: 'from-emerald-300 to-emerald-400',
  sanity: 'from-cyan-300 to-cyan-400'
};

const TEST_TYPE_BADGES = {
  integration: 'bg-sky-50 text-sky-600',
  system: 'bg-teal-50 text-teal-600',
  component: 'bg-blue-50 text-blue-600',
  regression: 'bg-emerald-50 text-emerald-600',
  sanity: 'bg-cyan-50 text-cyan-600'
};

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, statsData] = await Promise.all([
        reportsApi.getSummary(),
        reportsApi.getStats()
      ]);
      setSummary(summaryData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-sky-400 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
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

  const testTypesWithData = Object.entries(summary || {}).filter(([_, data]) => data.has_reports);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Overall Stats */}
      {stats && (
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">📈 Overall Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-gray-500 text-xs font-medium mb-1">Total Tests</div>
              <div className="text-2xl font-bold text-gray-800">{stats.overall_summary.total_tests}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-gray-500 text-xs font-medium mb-1">Passed</div>
              <div className="text-2xl font-bold text-green-600">{stats.overall_summary.passed}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-gray-500 text-xs font-medium mb-1">Failed</div>
              <div className="text-2xl font-bold text-red-600">{stats.overall_summary.failed}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-gray-500 text-xs font-medium mb-1">Pass Rate</div>
              <div className="text-2xl font-bold text-sky-500">{stats.overall_summary.pass_rate}</div>
            </div>
          </div>
        </div>
      )}

      {/* Test Types Grid */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">🧪 Test Types</h2>

        {testTypesWithData.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <p className="text-gray-500 text-lg">No test reports available yet</p>
            <p className="text-gray-400 text-sm mt-2">Run some tests to see reports here</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {testTypesWithData.map(([testType, data]) => (
              <div
                key={testType}
                className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300"
              >
                <div className={`bg-gradient-to-r ${TEST_TYPE_COLORS[testType]} p-3`}>
                  <div className="flex items-center justify-between">
                    <span className="text-white font-bold text-base uppercase">{testType}</span>
                    <span className="bg-white/20 backdrop-blur text-white px-2 py-0.5 rounded-full text-xs">
                      {data.total_reports} reports
                    </span>
                  </div>
                </div>

                <div className="p-4">
                  {data.latest ? (
                    <>
                      <div className="mb-3">
                        <div className="text-gray-500 text-xs mb-1">Latest Result</div>
                        <div className="text-xs text-gray-400">
                          {new Date(data.latest.timestamp).toLocaleString()}
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 mb-3">
                        <div className="text-center">
                          <div className="text-xl font-bold text-gray-800">{data.latest.summary.total}</div>
                          <div className="text-xs text-gray-500">Tests</div>
                        </div>
                        <div className="text-center">
                          <div className="text-xl font-bold text-green-600">{data.latest.summary.passed}</div>
                          <div className="text-xs text-gray-500">Passed</div>
                        </div>
                        <div className="text-center">
                          <div className="text-xl font-bold text-red-600">{data.latest.summary.failed}</div>
                          <div className="text-xs text-gray-500">Failed</div>
                        </div>
                      </div>

                      <div className="mb-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-600">Pass Rate</span>
                          <span className="font-semibold text-sky-500">{data.latest.summary.pass_rate}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-gradient-to-r from-sky-300 to-sky-400 h-1.5 rounded-full transition-all duration-500"
                            style={{ width: data.latest.summary.pass_rate }}
                          ></div>
                        </div>
                      </div>

                      <div className="flex space-x-2">
                        <Link
                          to={`/report/${testType}/${data.latest.id}`}
                          className="flex-1 bg-sky-400 text-white py-1.5 px-3 rounded-lg text-center font-semibold hover:bg-sky-500 transition text-xs"
                        >
                          View Latest
                        </Link>
                        <Link
                          to={`/test-type/${testType}`}
                          className="flex-1 bg-slate-400 text-white py-1.5 px-3 rounded-lg text-center font-semibold hover:bg-slate-500 transition text-xs"
                        >
                          History
                        </Link>
                      </div>
                    </>
                  ) : (
                    <p className="text-gray-500 text-center py-4">No reports yet</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
