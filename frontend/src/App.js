import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Authentication context
const AuthContext = React.createContext();

// Login component
const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Demo credentials: relocate_user / SecurePass2025!
          </p>
        </div>
      </div>
    </div>
  );
};

// Dashboard components
const HeroSection = () => (
  <div 
    className="relative bg-cover bg-center h-96 flex items-center justify-center text-white"
    style={{
      backgroundImage: "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1473625247510-8ceb1760943f')"
    }}
  >
    <div className="text-center">
      <h1 className="text-5xl font-bold mb-4">Your Phoenix to Peak District Journey</h1>
      <p className="text-xl mb-6">Making your relocation dreams a reality with expert guidance</p>
      <button className="bg-gradient-to-r from-green-500 to-blue-600 px-8 py-3 rounded-lg text-lg font-semibold hover:from-green-600 hover:to-blue-700 transition duration-300">
        Start Your Journey
      </button>
    </div>
  </div>
);

const StatsCard = ({ title, value, icon, change }) => (
  <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {change && (
          <p className="text-sm text-green-600 mt-1">
            +{change} from last month
          </p>
        )}
      </div>
      <div className="text-3xl">{icon}</div>
    </div>
  </div>
);

const ComparisonCard = ({ title, phoenixData, peakData, metric }) => (
  <div className="bg-white rounded-xl shadow-lg p-6">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-gray-600">Phoenix, AZ</span>
        <span className="font-semibold text-orange-600">{phoenixData}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-600">Peak District, UK</span>
        <span className="font-semibold text-green-600">{peakData}</span>
      </div>
      {metric && (
        <div className="pt-2 border-t">
          <span className="text-sm text-gray-500">{metric}</span>
        </div>
      )}
    </div>
  </div>
);

const ChromeExtensionCard = ({ extension }) => {
  const handleDownload = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}${extension.download_url}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${extension.extension_name.toLowerCase().replace(/\s+/g, '-')}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const data = await response.json();
        alert(data.message || 'Download not available yet');
      }
    } catch (error) {
      console.error('Download error:', error);
      alert('Download failed. Please try again.');
    }
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
      <h3 className="text-lg font-semibold text-purple-800 mb-2">{extension.extension_name}</h3>
      <p className="text-gray-600 mb-4">{extension.description}</p>
      <div className="mb-4">
        <h4 className="font-medium text-sm text-gray-700 mb-2">Features:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          {extension.features?.map((feature, index) => (
            <li key={index} className="flex items-center">
              <span className="w-2 h-2 bg-purple-400 rounded-full mr-2"></span>
              {feature}
            </li>
          ))}
        </ul>
      </div>
      <button 
        onClick={handleDownload}
        className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition duration-300 w-full"
      >
        Download Extension v{extension.version}
      </button>
      <div className="mt-3 text-xs text-gray-500">
        💡 Install: Extract and load as unpacked extension in Chrome Developer Mode
      </div>
    </div>
  );
};

const Dashboard = ({ user, onLogout }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [extensions, setExtensions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashboardRes, comparisonRes, extensionsRes] = await Promise.all([
          axios.get(`${API}/dashboard/overview`),
          axios.get(`${API}/comparison/phoenix-to-peak-district`),
          axios.get(`${API}/chrome-extensions`)
        ]);

        setDashboardData(dashboardRes.data);
        setComparisonData(comparisonRes.data);
        setExtensions(extensionsRes.data);
      } catch (error) {
        console.error("Error fetching data:", error);
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
          <p className="mt-4 text-gray-600">Loading your relocation dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Relocate Me</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user}</span>
              <button
                onClick={onLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-300"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <HeroSection />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatsCard
              title="Days Until Move"
              value={dashboardData.quick_stats.days_until_move}
              icon="📅"
            />
            <StatsCard
              title="Budget Allocated"
              value={`$${dashboardData.quick_stats.budget_allocated.toLocaleString()}`}
              icon="💰"
            />
            <StatsCard
              title="Properties Viewed"
              value={dashboardData.quick_stats.properties_viewed}
              icon="🏠"
              change="3"
            />
            <StatsCard
              title="Applications Sent"
              value={dashboardData.quick_stats.applications_sent}
              icon="📄"
              change="1"
            />
          </div>
        )}

        {/* Progress Section */}
        {dashboardData && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Relocation Progress</h2>
            <div className="mb-4">
              <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
                <span>Overall Progress</span>
                <span>{dashboardData.relocation_progress.completion_percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-green-500 to-blue-600 h-3 rounded-full"
                  style={{ width: `${dashboardData.relocation_progress.completion_percentage}%` }}
                ></div>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-green-700 mb-3">✅ Completed Steps</h3>
                <ul className="space-y-2">
                  {dashboardData.relocation_progress.completed_steps.map((step, index) => (
                    <li key={index} className="flex items-center text-green-600">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-orange-700 mb-3">⏳ Pending Steps</h3>
                <ul className="space-y-2">
                  {dashboardData.relocation_progress.pending_steps.map((step, index) => (
                    <li key={index} className="flex items-center text-orange-600">
                      <span className="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Location Comparison */}
        {comparisonData && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Phoenix vs Peak District Comparison</h2>
            
            {/* Visual Location Comparison */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div className="relative rounded-xl overflow-hidden shadow-lg">
                <div 
                  className="h-64 bg-cover bg-center"
                  style={{
                    backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1470164971321-eb5ac2c35f2e')"
                  }}
                >
                  <div className="absolute bottom-4 left-4 text-white">
                    <h3 className="text-2xl font-bold">Phoenix, Arizona</h3>
                    <p className="text-lg">Desert Paradise • 299 Sunny Days</p>
                    <div className="flex items-center mt-2">
                      <span className="bg-orange-500 text-white px-2 py-1 rounded text-sm mr-2">
                        🌡️ 75°F Avg
                      </span>
                      <span className="bg-blue-500 text-white px-2 py-1 rounded text-sm">
                        💰 $62k Income
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="relative rounded-xl overflow-hidden shadow-lg">
                <div 
                  className="h-64 bg-cover bg-center"
                  style={{
                    backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1565784900709-3bd5bb123a1e')"
                  }}
                >
                  <div className="absolute bottom-4 left-4 text-white">
                    <h3 className="text-2xl font-bold">Peak District, UK</h3>
                    <p className="text-lg">Natural Beauty • Rolling Hills</p>
                    <div className="flex items-center mt-2">
                      <span className="bg-green-500 text-white px-2 py-1 rounded text-sm mr-2">
                        🌡️ 48°F Avg
                      </span>
                      <span className="bg-purple-500 text-white px-2 py-1 rounded text-sm">
                        💰 £28k Income
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <ComparisonCard
                title="Cost of Living Index"
                phoenixData={comparisonData.from_location.cost_of_living_index}
                peakData={comparisonData.to_location.cost_of_living_index}
                metric={`${comparisonData.comparison_metrics.cost_difference_percent.toFixed(1)}% higher in Peak District`}
              />
              <ComparisonCard
                title="Safety Index"
                phoenixData={`${comparisonData.from_location.safety_index}/10`}
                peakData={`${comparisonData.to_location.safety_index}/10`}
                metric="Much safer in Peak District"
              />
              <ComparisonCard
                title="Average Temperature"
                phoenixData={`${comparisonData.from_location.weather_info.avg_temp_f}°F`}
                peakData={`${comparisonData.to_location.weather_info.avg_temp_f}°F`}
                metric="Cooler climate in Peak District"
              />
            </div>

            {/* Climate Change Visualization */}
            <div className="mt-8 bg-gradient-to-br from-blue-50 to-green-50 rounded-xl p-6 border border-blue-200">
              <h3 className="text-lg font-semibold text-blue-800 mb-4">🌤️ Climate Transition Overview</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="text-center">
                  <h4 className="font-medium text-orange-700 mb-2">From Phoenix Desert</h4>
                  <div className="bg-orange-100 rounded-lg p-4">
                    <div className="text-2xl mb-2">🌵</div>
                    <p className="text-sm text-orange-800">Hot & Dry</p>
                    <p className="text-xs text-orange-600">299 sunny days/year</p>
                  </div>
                </div>
                <div className="text-center">
                  <h4 className="font-medium text-green-700 mb-2">To Peak District</h4>
                  <div className="bg-green-100 rounded-lg p-4">
                    <div className="text-2xl mb-2">🏔️</div>
                    <p className="text-sm text-green-800">Cool & Lush</p>
                    <p className="text-xs text-green-600">120 sunny days/year</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Relocation Tips */}
            <div className="mt-6 bg-blue-50 rounded-xl p-6 border border-blue-200">
              <h3 className="text-lg font-semibold text-blue-800 mb-4">💡 Key Relocation Insights</h3>
              <ul className="space-y-2">
                {comparisonData.relocation_tips.map((tip, index) => (
                  <li key={index} className="flex items-start text-blue-700">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-3 mt-2"></span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Motivational Section */}
        <div className="mb-8">
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-8 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full -mr-16 -mt-16"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-white opacity-10 rounded-full -ml-12 -mb-12"></div>
            <div className="relative z-10">
              <h2 className="text-3xl font-bold mb-4">🌟 Your Journey Awaits</h2>
              <p className="text-xl mb-6">"The biggest adventure you can take is to live the life of your dreams."</p>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl mb-2">🎯</div>
                  <p className="font-semibold">Plan Smart</p>
                  <p className="text-sm opacity-90">Data-driven decisions</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">💪</div>
                  <p className="font-semibold">Stay Motivated</p>
                  <p className="text-sm opacity-90">Progress tracking</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">🏆</div>
                  <p className="font-semibold">Achieve Dreams</p>
                  <p className="text-sm opacity-90">New life awaits</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Chrome Extensions */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Chrome Extensions & Tools</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {extensions.map((extension, index) => (
              <ChromeExtensionCard key={index} extension={extension} />
            ))}
          </div>
        </div>

        {/* Destination Showcase */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Your New Home: Peak District</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div 
              className="relative h-64 bg-cover bg-center rounded-xl overflow-hidden"
              style={{
                backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1587713714775-fa70364f6445')"
              }}
            >
              <div className="absolute bottom-4 left-4 text-white">
                <h3 className="text-lg font-semibold">Stunning Landscapes</h3>
                <p className="text-sm">Rolling hills and natural beauty</p>
              </div>
            </div>
            <div 
              className="relative h-64 bg-cover bg-center rounded-xl overflow-hidden"
              style={{
                backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1594981005649-6ffab8d8a8d1')"
              }}
            >
              <div className="absolute bottom-4 left-4 text-white">
                <h3 className="text-lg font-semibold">Perfect Sunsets</h3>
                <p className="text-sm">Evening views you'll never forget</p>
              </div>
            </div>
            <div 
              className="relative h-64 bg-cover bg-center rounded-xl overflow-hidden"
              style={{
                backgroundImage: "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1609674794350-c26bb1e6045d')"
              }}
            >
              <div className="absolute bottom-4 left-4 text-white">
                <h3 className="text-lg font-semibold">Historic Villages</h3>
                <p className="text-sm">Rich culture and community</p>
              </div>
            </div>
          </div>
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

// Main App component
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Verify token is still valid
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
    // Get user info
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
        <Routes>
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <Dashboard user={user} onLogout={handleLogout} />
              ) : (
                <Login onLogin={handleLogin} />
              )
            }
          />
          <Route
            path="/dashboard"
            element={
              isAuthenticated ? (
                <Dashboard user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;