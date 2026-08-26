import api from './api';

export const dashboardService = {
  async getDashboardData() {
    const response = await api.get('/api/dashboard');
    return response.data;
  },
};

export default dashboardService;