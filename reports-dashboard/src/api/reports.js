import axios from 'axios';

const API_BASE_URL = 'http://localhost:5001';

export const reportsApi = {
  // Get summary of all test types
  getSummary: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/reports/summary`);
    return response.data;
  },

  // Get all reports
  getAllReports: async (limit = 10) => {
    const response = await axios.get(`${API_BASE_URL}/api/reports`, {
      params: { limit }
    });
    return response.data;
  },

  // Get reports by test type
  getReportsByType: async (testType, limit = 10) => {
    const response = await axios.get(`${API_BASE_URL}/api/reports/${testType}`, {
      params: { limit }
    });
    return response.data;
  },

  // Get specific report
  getReport: async (testType, reportId) => {
    const response = await axios.get(`${API_BASE_URL}/api/reports/${testType}/${reportId}`);
    return response.data;
  },

  // Get historical data for charts
  getHistory: async (testType, limit = 20) => {
    const response = await axios.get(`${API_BASE_URL}/api/reports/${testType}/history`, {
      params: { limit }
    });
    return response.data;
  },

  // Get overall stats
  getStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/stats`);
    return response.data;
  },

  // Get HTML report URL
  getHtmlReportUrl: (testType, reportId) => {
    return `${API_BASE_URL}/api/reports/${testType}/${reportId}/html`;
  }
};
