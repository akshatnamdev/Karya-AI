import api from './api';

export const aiService = {
  async askQuestion(question) {
    // Changed from /ask-public to /ask to send the JWT token and get the proper scope
    const response = await api.post('/api/ai/ask', {
      question,
      language: 'auto'
    });
    return response.data;
  },
};

export default aiService;