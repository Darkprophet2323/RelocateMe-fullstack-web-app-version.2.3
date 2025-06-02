import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Navigation Component
const Navigation = ({ user, onLogout, currentPath }) => {
  const navItems = [
    { path: "/dashboard", name: "Dashboard", icon: "🏠" },
    { path: "/timeline", name: "Timeline", icon: "📅" },
    { path: "/progress", name: "Progress", icon: "📊" },
    { path: "/housing", name: "Housing", icon: "🏘️" },
    { path: "/employment", name: "Jobs", icon: "💼" },
    { path: "/visa", name: "Visa & Legal", icon: "📋" },
    { path: "/resources", name: "Resources", icon: "🔗" },
    { path: "/logistics", name: "Logistics", icon: "📦" }
  ];

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                🏔️ Relocate Me
              </span>
            </Link>
          </div>
          
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  currentPath === item.path
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-blue-700 hover:bg-gray-100'
                }`}
              >
                <span className="mr-1">{item.icon}</span>
                {item.name}
              </Link>
            ))}
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-gray-700 text-sm">Welcome, {user}</span>
            <button
              onClick={onLogout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-300 text-sm"
            >
              Logout
            </button>
          </div>
        </div>
        
        {/* Mobile Navigation */}
        <div className="md:hidden pb-3">
          <div className="grid grid-cols-4 gap-2">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-center py-2 px-1 rounded text-xs ${
                  currentPath === item.path
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600'
                }`}
              >
                <div>{item.icon}</div>
                <div>{item.name}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Login component
const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showReset, setShowReset] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${API}/auth/login`, credentials);
      localStorage.setItem("token", response.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      onLogin(response.data.access_token);
    } catch (err) {
      setError("Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Relocate Me</h1>
          <p className="text-gray-600">Your Journey to Peak District Starts Here</p>
        </div>

        {!showReset ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 transition duration-300 disabled:opacity-50"
            >
              {loading ? "Logging in..." : "Login"}
            </button>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setShowReset(true)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Forgot your password?
              </button>
            </div>
          </form>
        ) : (
          <PasswordResetForm onBack={() => setShowReset(false)} />
        )}

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Demo credentials: relocate_user / SecurePass2025!
          </p>
        </div>
      </div>
    </div>
  );
};

// Password Reset Component
const PasswordResetForm = ({ onBack }) => {
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${API}/auth/reset-password`, { username });
      setMessage(`Reset code generated: ${response.data.reset_code}`);
      setStep(2);
    } catch (err) {
      setError("Error requesting password reset. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await axios.post(`${API}/auth/complete-password-reset`, {
        username,
        reset_code: resetCode,
        new_password: newPassword
      });
      setMessage("Password reset successfully! You can now login with your new password.");
      setTimeout(() => onBack(), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Error resetting password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Reset Password</h2>
        <p className="text-gray-600">Step {step} of 2</p>
      </div>

      {message && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {message}
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {step === 1 ? (
        <form onSubmit={handleRequestReset} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your username"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition duration-300 disabled:opacity-50"
          >
            {loading ? "Requesting..." : "Request Reset Code"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleCompleteReset} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reset Code
            </label>
            <input
              type="text"
              value={resetCode}
              onChange={(e) => setResetCode(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter reset code"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter new password"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition duration-300 disabled:opacity-50"
          >
            {loading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
      )}

      <div className="text-center">
        <button
          onClick={onBack}
          className="text-gray-600 hover:text-gray-800 text-sm"
        >
          ← Back to Login
        </button>
      </div>
    </div>
  );
};

// Dashboard Page Component
const DashboardPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`${API}/dashboard/overview`);
        setDashboardData(response.data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div 
        className="relative bg-cover bg-center h-64 flex items-center justify-center text-white"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1473625247510-8ceb1760943f')"
        }}
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Your Phoenix to Peak District Journey</h1>
          <p className="text-lg">Making your relocation dreams a reality with expert guidance</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Progress</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData.relocation_progress.completion_percentage}%</p>
                  <p className="text-sm text-green-600 mt-1">
                    {dashboardData.relocation_progress.completed_steps_count}/{dashboardData.relocation_progress.total_steps} steps
                  </p>
                </div>
                <div className="text-3xl">📊</div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Days Until Move</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData.quick_stats.days_until_move}</p>
                  <p className="text-sm text-blue-600 mt-1">Target date set</p>
                </div>
                <div className="text-3xl">📅</div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Budget Allocated</p>
                  <p className="text-2xl font-bold text-gray-900">${dashboardData.quick_stats.budget_allocated.toLocaleString()}</p>
                  <p className="text-sm text-purple-600 mt-1">Financial planning</p>
                </div>
                <div className="text-3xl">💰</div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Phase</p>
                  <p className="text-xl font-bold text-gray-900">{dashboardData.relocation_progress.current_phase}</p>
                  <p className="text-sm text-orange-600 mt-1">Active stage</p>
                </div>
                <div className="text-3xl">🚀</div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link to="/timeline" className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
            <div className="text-center">
              <div className="text-4xl mb-3">📅</div>
              <h3 className="text-lg font-semibold mb-2">View Timeline</h3>
              <p className="text-sm opacity-90">Track your relocation milestones</p>
            </div>
          </Link>
          
          <Link to="/housing" className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
            <div className="text-center">
              <div className="text-4xl mb-3">🏠</div>
              <h3 className="text-lg font-semibold mb-2">Find Housing</h3>
              <p className="text-sm opacity-90">Explore Peak District properties</p>
            </div>
          </Link>
          
          <Link to="/resources" className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
            <div className="text-center">
              <div className="text-4xl mb-3">🔗</div>
              <h3 className="text-lg font-semibold mb-2">Resources</h3>
              <p className="text-sm opacity-90">Essential links and tools</p>
            </div>
          </Link>
        </div>

        {/* Recent Activity */}
        {dashboardData && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Activity</h2>
            <div className="space-y-4">
              {dashboardData.recent_activity.map((activity, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-700">{activity}</span>
                  <span className="text-sm text-gray-400">• Just now</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Timeline Page Component
const TimelinePage = () => {
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [fullResponse, categoryResponse] = await Promise.all([
          axios.get(`${API}/timeline/full`),
          axios.get(`${API}/timeline/by-category`)
        ]);
        setTimelineData({
          full: fullResponse.data,
          categories: categoryResponse.data
        });
      } catch (error) {
        console.error("Error fetching timeline data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const updateStepProgress = async (stepId, completed) => {
    try {
      await axios.post(`${API}/timeline/update-progress`, {
        step_id: stepId,
        completed: completed
      });
      
      // Refresh timeline data
      const [fullResponse, categoryResponse] = await Promise.all([
        axios.get(`${API}/timeline/full`),
        axios.get(`${API}/timeline/by-category`)
      ]);
      setTimelineData({
        full: fullResponse.data,
        categories: categoryResponse.data
      });
    } catch (error) {
      console.error("Error updating progress:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading timeline...</p>
        </div>
      </div>
    );
  }

  const categories = timelineData ? Object.keys(timelineData.categories) : [];
  const filteredSteps = activeCategory === "all" 
    ? timelineData?.full?.timeline || []
    : timelineData?.categories[activeCategory]?.steps || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div 
        className="relative bg-cover bg-center h-48 flex items-center justify-center text-white"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.pexels.com/photos/7550933/pexels-photo-7550933.jpeg')"
        }}
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Relocation Timeline</h1>
          <p className="text-lg">Your step-by-step journey to Peak District</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Overview */}
        {timelineData && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{timelineData.full.completed_steps}</div>
                <div className="text-gray-600">Steps Completed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{timelineData.full.completion_percentage.toFixed(1)}%</div>
                <div className="text-gray-600">Overall Progress</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">{timelineData.full.current_phase}</div>
                <div className="text-gray-600">Current Phase</div>
              </div>
            </div>
            <div className="mt-6">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${timelineData.full.completion_percentage}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {/* Category Filter */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveCategory("all")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                activeCategory === "all"
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              All Steps
            </button>
            {categories.map(category => (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  activeCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-100'
                }`}
              >
                {category} ({timelineData?.categories[category]?.completed_steps}/{timelineData?.categories[category]?.total_steps})
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Steps */}
        <div className="space-y-6">
          {filteredSteps.map((step, index) => (
            <div
              key={step.id}
              className={`bg-white rounded-xl shadow-lg p-6 border-l-4 ${
                step.is_completed ? 'border-green-500' : 'border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <input
                      type="checkbox"
                      checked={step.is_completed}
                      onChange={(e) => updateStepProgress(step.id, e.target.checked)}
                      className="mr-3 h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <h3 className={`text-lg font-semibold ${step.is_completed ? 'text-green-700 line-through' : 'text-gray-900'}`}>
                      {step.title}
                    </h3>
                    <span className="ml-3 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                      {step.category}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-3">{step.description}</p>
                  <div className="flex items-center text-sm text-gray-500">
                    <span className="mr-4">⏱️ {step.estimated_days} days</span>
                    {step.dependencies.length > 0 && (
                      <span>🔗 Depends on steps: {step.dependencies.join(", ")}</span>
                    )}
                  </div>
                  {step.resources.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Resources:</h4>
                      <div className="flex flex-wrap gap-2">
                        {step.resources.map((resource, idx) => (
                          <span key={idx} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                            {resource}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <div className="ml-4">
                  {step.is_completed ? (
                    <div className="text-green-500 text-2xl">✅</div>
                  ) : (
                    <div className="text-gray-400 text-2xl">⭕</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Resources Page Component
const ResourcesPage = () => {
  const [resources, setResources] = useState(null);
  const [loadingResources, setLoadingResources] = useState(true);

  useEffect(() => {
    const fetchResources = async () => {
      try {
        const response = await axios.get(`${API}/resources/all`);
        setResources(response.data);
      } catch (error) {
        console.error("Error fetching resources:", error);
      } finally {
        setLoadingResources(false);
      }
    };
    fetchResources();
  }, []);

  if (loadingResources) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading resources...</p>
        </div>
      </div>
    );
  }

  const ResourceCard = ({ resource, color }) => (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`block bg-gradient-to-br ${color} text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105`}
    >
      <h3 className="text-lg font-semibold mb-2">{resource.name}</h3>
      <p className="text-sm opacity-90">{resource.description}</p>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs opacity-75">Click to visit</span>
        <span className="text-lg">🔗</span>
      </div>
    </a>
  );

  const colors = [
    "from-blue-500 to-blue-600",
    "from-green-500 to-green-600", 
    "from-purple-500 to-purple-600",
    "from-red-500 to-red-600",
    "from-yellow-500 to-yellow-600",
    "from-indigo-500 to-indigo-600"
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div 
        className="relative bg-cover bg-center h-48 flex items-center justify-center text-white"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1588152850700-c82ecb8ba9b1')"
        }}
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Essential Resources</h1>
          <p className="text-lg">Everything you need for your relocation journey</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {resources && Object.entries(resources).map(([category, items], categoryIndex) => (
          <div key={category} className="mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 capitalize">
              {category.replace('_', ' & ')}
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {items.map((resource, index) => (
                <ResourceCard 
                  key={index} 
                  resource={resource} 
                  color={colors[(categoryIndex * 3 + index) % colors.length]}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Housing Page Component  
const HousingPage = () => {
  const [housingData, setHousingData] = useState(null);
  const [loadingHousing, setLoadingHousing] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [phoenixRes, peakRes] = await Promise.all([
          axios.get(`${API}/housing/phoenix`),
          axios.get(`${API}/housing/peak-district`)
        ]);
        setHousingData({
          phoenix: phoenixRes.data,
          peak_district: peakRes.data
        });
      } catch (error) {
        console.error("Error fetching housing data:", error);
      } finally {
        setLoadingHousing(false);
      }
    };
    fetchData();
  }, []);

  if (loadingHousing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading housing data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div 
        className="relative bg-cover bg-center h-48 flex items-center justify-center text-white"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1568190538421-53523065d4b8')"
        }}
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Housing Comparison</h1>
          <p className="text-lg">Find your perfect home in Peak District</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {housingData && (
          <div className="grid md:grid-cols-2 gap-8">
            {/* Phoenix Housing */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center mb-4">
                <span className="text-3xl mr-3">🌵</span>
                <h2 className="text-2xl font-bold text-orange-600">Phoenix, Arizona</h2>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Median Home Price:</span>
                  <span className="font-semibold">${housingData.phoenix.median_home_price.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Median Rent:</span>
                  <span className="font-semibold">${housingData.phoenix.median_rent}/month</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Price per sq ft:</span>
                  <span className="font-semibold">${housingData.phoenix.price_per_sqft}</span>
                </div>
                <div className="mt-6">
                  <h3 className="font-semibold text-gray-700 mb-3">Popular Neighborhoods:</h3>
                  <div className="flex flex-wrap gap-2">
                    {housingData.phoenix.popular_neighborhoods.map((area, index) => (
                      <span key={index} className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm">
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Peak District Housing */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center mb-4">
                <span className="text-3xl mr-3">🏔️</span>
                <h2 className="text-2xl font-bold text-green-600">Peak District, UK</h2>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Median Home Price:</span>
                  <span className="font-semibold">£{housingData.peak_district.median_home_price.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Median Rent:</span>
                  <span className="font-semibold">£{housingData.peak_district.median_rent}/month</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Price per sq ft:</span>
                  <span className="font-semibold">£{housingData.peak_district.price_per_sqft}</span>
                </div>
                <div className="mt-6">
                  <h3 className="font-semibold text-gray-700 mb-3">Popular Areas:</h3>
                  <div className="flex flex-wrap gap-2">
                    {housingData.peak_district.popular_areas.map((area, index) => (
                      <span key={index} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Property Search Links */}
        <div className="mt-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Property Search Platforms</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <a href="https://www.rightmove.co.uk" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">🏠</div>
                <h3 className="text-lg font-semibold mb-2">Rightmove</h3>
                <p className="text-sm opacity-90">UK's largest property portal</p>
              </div>
            </a>
            
            <a href="https://www.zoopla.co.uk" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">🔍</div>
                <h3 className="text-lg font-semibold mb-2">Zoopla</h3>
                <p className="text-sm opacity-90">Property search and valuation</p>
              </div>
            </a>
            
            <a href="https://www.spareroom.co.uk" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">🛏️</div>
                <h3 className="text-lg font-semibold mb-2">SpareRoom</h3>
                <p className="text-sm opacity-90">Room rental and flatshare</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// Employment Page Component
const EmploymentPage = () => {
  const [jobData, setJobData] = useState(null);
  const [jobListings, setJobListings] = useState(null);
  const [filteredJobs, setFilteredJobs] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedJobType, setSelectedJobType] = useState("all");
  const [loadingJobs, setLoadingJobs] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobOpportunitiesRes, jobListingsRes] = await Promise.all([
          axios.get(`${API}/jobs/opportunities`),
          axios.get(`${API}/jobs/listings`)
        ]);
        setJobData(jobOpportunitiesRes.data);
        setJobListings(jobListingsRes.data);
        setFilteredJobs(jobListingsRes.data.jobs);
      } catch (error) {
        console.error("Error fetching job data:", error);
      } finally {
        setLoadingJobs(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (jobListings) {
      let filtered = jobListings.jobs;
      
      if (selectedCategory !== "all") {
        filtered = filtered.filter(job => job.category === selectedCategory);
      }
      
      if (selectedJobType !== "all") {
        filtered = filtered.filter(job => job.job_type === selectedJobType);
      }
      
      setFilteredJobs(filtered);
    }
  }, [selectedCategory, selectedJobType, jobListings]);

  const JobCard = ({ job }) => (
    <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500 hover:shadow-xl transition-all duration-300">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{job.title}</h3>
          <div className="flex items-center text-gray-600 mb-2">
            <span className="text-sm mr-4">🏢 {job.company}</span>
            <span className="text-sm mr-4">📍 {job.location}</span>
          </div>
          {job.salary && (
            <div className="text-green-600 font-semibold mb-3">💰 {job.salary}</div>
          )}
        </div>
        <div className="flex flex-col items-end">
          <span className={`px-3 py-1 text-xs rounded-full ${
            job.job_type === 'remote' ? 'bg-purple-100 text-purple-800' :
            job.job_type === 'full-time' ? 'bg-blue-100 text-blue-800' :
            job.job_type === 'part-time' ? 'bg-green-100 text-green-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {job.job_type}
          </span>
          <span className="text-xs text-gray-500 mt-1">
            {new Date(job.posted_date).toLocaleDateString()}
          </span>
        </div>
      </div>
      
      <p className="text-gray-600 mb-4 text-sm">{job.description}</p>
      
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Requirements:</h4>
        <div className="flex flex-wrap gap-2">
          {job.requirements.slice(0, 3).map((req, index) => (
            <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              {req}
            </span>
          ))}
          {job.requirements.length > 3 && (
            <span className="px-2 py-1 text-xs bg-gray-200 text-gray-500 rounded">
              +{job.requirements.length - 3} more
            </span>
          )}
        </div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Benefits:</h4>
        <div className="flex flex-wrap gap-2">
          {job.benefits.slice(0, 2).map((benefit, index) => (
            <span key={index} className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
              {benefit}
            </span>
          ))}
          {job.benefits.length > 2 && (
            <span className="px-2 py-1 text-xs bg-green-200 text-green-600 rounded">
              +{job.benefits.length - 2} more
            </span>
          )}
        </div>
      </div>
      
      <div className="flex justify-between items-center">
        <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded">
          {job.category}
        </span>
        <a
          href={job.application_url}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-300 text-sm"
        >
          Apply Now →
        </a>
      </div>
    </div>
  );

  if (loadingJobs) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading employment data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div 
        className="relative bg-cover bg-center h-48 flex items-center justify-center text-white"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.pexels.com/photos/19860848/pexels-photo-19860848.jpeg')"
        }}
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Employment Opportunities</h1>
          <p className="text-lg">Build your career in Peak District</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Job Market Overview */}
        {jobData && (
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-orange-600 mb-6">Phoenix Job Market</h2>
              <div className="space-y-4">
                {Object.entries(jobData.phoenix_jobs).map(([sector, score]) => (
                  <div key={sector} className="flex justify-between">
                    <span className="text-gray-600 capitalize">{sector.replace('_', ' ')}:</span>
                    <span className="font-semibold">
                      {typeof score === 'number' && sector !== 'avg_salary_usd' ? `${score}%` : `$${score.toLocaleString()}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-green-600 mb-6">Peak District Opportunities</h2>
              <div className="space-y-4">
                {Object.entries(jobData.peak_district_jobs).map(([sector, score]) => (
                  <div key={sector} className="flex justify-between">
                    <span className="text-gray-600 capitalize">{sector.replace('_', ' ')}:</span>
                    <span className="font-semibold">
                      {typeof score === 'number' && sector !== 'avg_salary_gbp' ? `${score}%` : `£${score.toLocaleString()}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Job Listings Section */}
        {jobListings && (
          <>
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 md:mb-0">
                  Available Jobs ({filteredJobs.length})
                </h2>
                <div className="flex flex-col sm:flex-row gap-4">
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Categories</option>
                    {jobListings.categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                  <select
                    value={selectedJobType}
                    onChange={(e) => setSelectedJobType(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Types</option>
                    {jobListings.job_types.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="grid gap-6">
                {filteredJobs.map((job, index) => (
                  <JobCard key={job.id || index} job={job} />
                ))}
              </div>
              
              {filteredJobs.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">No jobs found matching your criteria.</p>
                </div>
              )}
            </div>

            {/* Remote Work Opportunities */}
            {jobData && (
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 mb-12">
                <h2 className="text-2xl font-bold text-purple-800 mb-6">Remote Work Opportunities</h2>
                <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {jobData.remote_work_opportunities.map((opportunity, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 text-center shadow-md">
                      <div className="text-2xl mb-2">💻</div>
                      <div className="text-sm font-medium text-gray-700">{opportunity}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Job Search Platforms */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Job Search Platforms</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <a href="https://uk.indeed.com" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">🔍</div>
                <h3 className="text-lg font-semibold mb-2">Indeed UK</h3>
                <p className="text-sm opacity-90">Leading job search platform</p>
              </div>
            </a>
            
            <a href="https://www.reed.co.uk" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">📄</div>
                <h3 className="text-lg font-semibold mb-2">Reed</h3>
                <p className="text-sm opacity-90">UK recruitment specialists</p>
              </div>
            </a>
            
            <a href="https://www.linkedin.com/jobs" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">💼</div>
                <h3 className="text-lg font-semibold mb-2">LinkedIn</h3>
                <p className="text-sm opacity-90">Professional networking</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// Visa Page Component
const VisaPage = () => {
  const [visaRequirements, setVisaRequirements] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [loadingVisa, setLoadingVisa] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [requirementsRes, checklistRes] = await Promise.all([
          axios.get(`${API}/visa/requirements`),
          axios.get(`${API}/visa/checklist`)
        ]);
        setVisaRequirements(requirementsRes.data);
        setChecklist(checklistRes.data);
      } catch (error) {
        console.error("Error fetching visa data:", error);
      } finally {
        setLoadingVisa(false);
      }
    };
    fetchData();
  }, []);

  if (loadingVisa) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading visa information...</p>
        </div>
      </div>
    );
  }

  const VisaTypeCard = ({ visa, index }) => {
    const colors = [
      "from-blue-500 to-blue-600",
      "from-green-500 to-green-600",
      "from-purple-500 to-purple-600",
      "from-red-500 to-red-600"
    ];

    return (
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <div className="flex items-center mb-4">
          <div className={`w-4 h-4 rounded-full bg-gradient-to-r ${colors[index % colors.length]} mr-3`}></div>
          <h3 className="text-xl font-bold text-gray-900">{visa.visa_type}</h3>
        </div>
        <h4 className="text-lg font-semibold text-gray-700 mb-3">{visa.title}</h4>
        <p className="text-gray-600 mb-6">{visa.description}</p>
        
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <h5 className="font-semibold text-blue-800 mb-3">💰 Cost & Timing</h5>
            <div className="space-y-2 text-sm">
              <div><strong>Fee:</strong> {visa.fee}</div>
              <div><strong>Processing:</strong> {visa.processing_time}</div>
            </div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <h5 className="font-semibold text-green-800 mb-3">✅ Key Requirements</h5>
            <ul className="text-sm space-y-1">
              {visa.eligibility.slice(0, 3).map((requirement, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2 mt-1.5"></span>
                  {requirement}
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        <div className="border-t pt-4">
          <h5 className="font-semibold text-gray-700 mb-3">📋 Application Process</h5>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h6 className="text-sm font-medium text-gray-600 mb-2">Steps:</h6>
              <ol className="text-sm space-y-1">
                {visa.application_process.slice(0, 4).map((step, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="w-5 h-5 bg-gray-200 text-gray-600 rounded-full mr-2 mt-0.5 text-xs flex items-center justify-center">
                      {idx + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
            <div>
              <h6 className="text-sm font-medium text-gray-600 mb-2">Required Documents:</h6>
              <ul className="text-sm space-y-1">
                {visa.required_documents.slice(0, 4).map((doc, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 mt-1.5"></span>
                    {doc}
                  </li>
                ))}
                {visa.required_documents.length > 4 && (
                  <li className="text-gray-500 text-xs">+{visa.required_documents.length - 4} more documents</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div 
        className="relative bg-cover bg-center h-48 flex items-center justify-center text-white"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.pexels.com/photos/8830672/pexels-photo-8830672.jpeg')"
        }}
      >
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Visa & Legal Requirements</h1>
          <p className="text-lg">Navigate UK immigration requirements</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Visa Types Overview */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Choose Your Visa Type</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl shadow-lg">
              <div className="text-center">
                <div className="text-4xl mb-3">💼</div>
                <h3 className="text-lg font-semibold mb-2">Skilled Worker</h3>
                <p className="text-sm opacity-90">Most common for professionals</p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl shadow-lg">
              <div className="text-center">
                <div className="text-4xl mb-3">👨‍👩‍👧‍👦</div>
                <h3 className="text-lg font-semibold mb-2">Family Visa</h3>
                <p className="text-sm opacity-90">Join family members in UK</p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl shadow-lg">
              <div className="text-center">
                <div className="text-4xl mb-3">🎓</div>
                <h3 className="text-lg font-semibold mb-2">Student Visa</h3>
                <p className="text-sm opacity-90">Study at UK institutions</p>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-red-500 to-red-600 text-white p-6 rounded-xl shadow-lg">
              <div className="text-center">
                <div className="text-4xl mb-3">✈️</div>
                <h3 className="text-lg font-semibold mb-2">Visitor Visa</h3>
                <p className="text-sm opacity-90">Short-term visits</p>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Visa Requirements */}
        {visaRequirements && (
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Detailed Visa Information</h2>
            {visaRequirements.visa_types.map((visa, index) => (
              <VisaTypeCard key={visa.visa_type} visa={visa} index={index} />
            ))}
          </div>
        )}

        {/* Document Checklist */}
        {checklist && (
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Document Checklist</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {Object.entries(checklist).map(([category, documents], index) => {
                const colors = [
                  "border-blue-500 bg-blue-50",
                  "border-green-500 bg-green-50",
                  "border-purple-500 bg-purple-50",
                  "border-red-500 bg-red-50"
                ];
                
                return (
                  <div key={category} className={`bg-white rounded-xl shadow-lg p-6 border-l-4 ${colors[index % colors.length]}`}>
                    <h3 className="text-lg font-bold text-gray-900 mb-4 capitalize">
                      {category.replace('_', ' ')}
                    </h3>
                    <ul className="space-y-3">
                      {documents.map((doc, idx) => (
                        <li key={idx} className="flex items-start">
                          <input
                            type="checkbox"
                            className="mr-3 mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="text-gray-700 text-sm">{doc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Official Resources */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Official Resources</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <a href="https://www.gov.uk/browse/visas-immigration" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-red-500 to-red-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">🏛️</div>
                <h3 className="text-lg font-semibold mb-2">UK Government</h3>
                <p className="text-sm opacity-90">Official visa information</p>
              </div>
            </a>
            
            <a href="https://www.lawsociety.org.uk" target="_blank" rel="noopener noreferrer" className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
              <div className="text-center">
                <div className="text-4xl mb-3">⚖️</div>
                <h3 className="text-lg font-semibold mb-2">Legal Society</h3>
                <p className="text-sm opacity-90">Find qualified lawyers</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );

const ProgressPage = () => (
  <div className="min-h-screen bg-gray-50 p-8">
    <h1 className="text-3xl font-bold mb-4">Progress Tracking</h1>
    <p>Progress tracking page - coming soon with detailed analytics!</p>
  </div>
);

// Main App component
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      axios.get(`${API}/auth/me`)
        .then(response => {
          setIsAuthenticated(true);
          setUser(response.data.username);
        })
        .catch(() => {
          localStorage.removeItem("token");
          delete axios.defaults.headers.common['Authorization'];
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (token) => {
    setIsAuthenticated(true);
    axios.get(`${API}/auth/me`)
      .then(response => {
        setUser(response.data.username);
      })
      .catch(console.error);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setUser("");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        {isAuthenticated ? (
          <AuthenticatedApp user={user} onLogout={handleLogout} />
        ) : (
          <Routes>
            <Route path="*" element={<Login onLogin={handleLogin} />} />
          </Routes>
        )}
      </BrowserRouter>
    </div>
  );
}

const AuthenticatedApp = ({ user, onLogout }) => {
  const location = useLocation();

  return (
    <>
      <Navigation user={user} onLogout={onLogout} currentPath={location.pathname} />
      <Routes>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/resources" element={<ResourcesPage />} />
        <Route path="/housing" element={<HousingPage />} />
        <Route path="/employment" element={<EmploymentPage />} />
        <Route path="/visa" element={<VisaPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/logistics" element={<div className="p-8">Logistics page coming soon!</div>} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
};

