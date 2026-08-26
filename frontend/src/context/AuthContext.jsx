import { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = authService.getUser();
    if (savedUser && authService.isAuthenticated()) {
      setUser(savedUser);
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    try {
      const data = await authService.login(credentials);
      setUser(data.user);
      return { success: true, data, redirectTo: data.redirect_to };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed. Please try again.',
      };
    }
  };

  const register = async (userData) => {
    try {
      const data = await authService.register(userData);
      setUser(data.user);
      return { success: true, data, redirectTo: data.redirect_to };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed.',
      };
    }
  };

  const registerCustomer = async (customerData) => {
    try {
      const data = await authService.registerCustomer(customerData);
      setUser(data.user);
      return { success: true, data, redirectTo: data.redirect_to };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed.',
      };
    }
  };

  const logout = () => {
    setUser(null);
    authService.logout();
  };

  // Role helpers
  const isPlatformAdmin = user?.role === 'platform_admin';
  const isBusinessOwner = user?.role === 'business_owner';
  const isCustomer = user?.role === 'customer';

  const value = {
    user,
    loading,
    login,
    register,
    registerCustomer,
    logout,
    isAuthenticated: !!user,
    isPlatformAdmin,
    isBusinessOwner,
    isCustomer,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthContext;