import api from './api';

export const productService = {
  async getAll() {
    const response = await api.get('/api/products');
    return response.data;
  },

  async getLowStock() {
    const response = await api.get('/api/products/low-stock');
    return response.data;
  },

  async getById(id) {
    const response = await api.get(`/api/products/${id}`);
    return response.data;
  },

  async create(payload) {
    const response = await api.post('/api/products', payload);
    return response.data;
  },

  async remove(id) {
    const res = await api.delete(`/api/products/${id}`);
    return res.data;
  },

  async remove(id) {
    const res = await api.delete(`/api/products/${id}`);
    return res.data;
  },

  async activate(id) {
    const res = await api.post(`/api/products/${id}/activate`);
    return res.data;
  },  

  async updateStock(productId, payload) {
    const response = await api.patch(`/api/products/${productId}/stock`, payload);
    return response.data;
  },
};

export default productService;