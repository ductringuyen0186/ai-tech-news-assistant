import React, { useState, useEffect } from 'react';
import { Activity, Server, Brain, Database, CheckCircle, XCircle, AlertCircle, Search, Zap } from 'lucide-react';
import api from '../lib/api';

interface HealthResponse {
  status: string;
  components: {
    api: string;
    ollama: string;
    database: string;
  };
  timestamp: string;
}

interface TestResult {
  endpoint: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  response?: any;
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Get API base URL from environment
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const fetchHealth = async () => {
    try {
      const response = await api.get('/health');
      setHealth(response.data);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealth(null);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const runAllTests = async () => {
    setIsLoading(true);
    const tests: TestResult[] = [];

    // Test endpoints
    const endpoints = [
      { name: 'Root', url: '/', method: 'GET' },
      { name: 'Health', url: '/health', method: 'GET' },
      { name: 'Articles', url: '/articles', method: 'GET' },
      { name: 'LLM Test', url: '/test-llm', method: 'GET' },
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await api.get(endpoint.url);

        tests.push({
          endpoint: endpoint.name,
          status: 'success',
          message: 'OK',
          response: response.data
        });
      } catch (error) {
        tests.push({
          endpoint: endpoint.name,
          status: 'error',
          message: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    // Test Search
    try {
      const response = await api.post('/search', { query: 'AI', limit: 3 });

      tests.push({
        endpoint: 'Search',
        status: response.data.success ? 'success' : 'error',
        message: `Found ${response.data.total} results`,
        response: response.data
      });
    } catch (error) {
      tests.push({
        endpoint: 'Search',
        status: 'error',
        message: error instanceof Error ? error.message : 'Search error'
      });
    }

    // Test Summarization
    try {
      const response = await api.post('/summarize', {
        text: 'Artificial intelligence is revolutionizing technology. Machine learning algorithms process data to make predictions. Deep learning uses neural networks for complex tasks.',
        max_length: 50
      });

      tests.push({
        endpoint: 'Summarization',
        status: response.data.success ? 'success' : 'error',
        message: `Summary generated (${response.data.method})`,
        response: response.data
      });
    } catch (error) {
      tests.push({
        endpoint: 'Summarization',
        status: 'error',
        message: error instanceof Error ? error.message : 'Summarization error'
      });
    }

    setTestResults(tests);
    setIsLoading(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
      case 'healthy':
      case 'online':
      case 'available':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
      case 'unavailable':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
      case 'healthy':
      case 'online':
      case 'available':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'error':
      case 'unavailable':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">AI Tech News Assistant Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Monitor system health and test AI features
        </p>
      </div>

      {/* System Health */}
      <div className="bg-white shadow-sm rounded-lg p-6 border">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <span>System Health</span>
        </h2>

        {health ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded-lg border ${getStatusColor(health.components.api)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Server className="w-5 h-5" />
                  <span className="font-medium">API Server</span>
                </div>
                {getStatusIcon(health.components.api)}
              </div>
              <p className="text-sm mt-1 capitalize">{health.components.api}</p>
            </div>

            <div className={`p-4 rounded-lg border ${getStatusColor(health.components.ollama)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Brain className="w-5 h-5" />
                  <span className="font-medium">Ollama LLM</span>
                </div>
                {getStatusIcon(health.components.ollama)}
              </div>
              <p className="text-sm mt-1 capitalize">{health.components.ollama}</p>
            </div>

            <div className={`p-4 rounded-lg border ${getStatusColor(health.components.database)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Database className="w-5 h-5" />
                  <span className="font-medium">Database</span>
                </div>
                {getStatusIcon(health.components.database)}
              </div>
              <p className="text-sm mt-1 capitalize">{health.components.database}</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-2" />
            <p className="text-gray-600">Unable to connect to backend</p>
            <p className="text-sm text-gray-500">Make sure the backend server is running</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow-sm rounded-lg p-6 border">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/search"
            className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center space-x-3">
              <Search className="w-8 h-8 text-blue-600 group-hover:text-blue-700" />
              <div>
                <h3 className="font-medium text-gray-900">Search Articles</h3>
                <p className="text-sm text-gray-600">Test search functionality</p>
              </div>
            </div>
          </a>

          <button
            onClick={runAllTests}
            disabled={isLoading}
            className="p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-sm transition-all group disabled:opacity-50"
          >
            <div className="flex items-center space-x-3">
              <Zap className="w-8 h-8 text-green-600 group-hover:text-green-700" />
              <div>
                <h3 className="font-medium text-gray-900">Run Tests</h3>
                <p className="text-sm text-gray-600">Test all endpoints</p>
              </div>
            </div>
          </button>

          <a
            href={`${apiBaseUrl}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:shadow-sm transition-all group"
          >
            <div className="flex items-center space-x-3">
              <Activity className="w-8 h-8 text-purple-600 group-hover:text-purple-700" />
              <div>
                <h3 className="font-medium text-gray-900">API Docs</h3>
                <p className="text-sm text-gray-600">View Swagger documentation</p>
              </div>
            </div>
          </a>
        </div>
      </div>

      {/* Test Results */}
      {testResults.length > 0 && (
        <div className="bg-white shadow-sm rounded-lg p-6 border">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Endpoint Test Results</h2>
          <div className="space-y-3">
            {testResults.map((test, index) => (
              <div key={index} className={`p-3 rounded-lg border ${getStatusColor(test.status)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(test.status)}
                    <span className="font-medium">{test.endpoint}</span>
                  </div>
                  <span className="text-sm">{test.message}</span>
                </div>
                {test.response && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                      View Response
                    </summary>
                    <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                      {JSON.stringify(test.response, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Getting Started */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-3">Getting Started</h2>
        <div className="space-y-2 text-blue-800">
          <p>✅ <strong>Backend:</strong> {apiBaseUrl} (FastAPI)</p>
          <p>✅ <strong>Frontend:</strong> http://localhost:5173 (React + Vite)</p>
          <p>🤖 <strong>AI Features:</strong> Search, Summarization, Mock Data</p>
          <p>📚 <strong>API Docs:</strong> {apiBaseUrl}/docs</p>
        </div>
        
        <div className="mt-4 p-3 bg-blue-100 rounded">
          <p className="text-sm text-blue-800">
            <strong>Next steps:</strong> Use the search page to test AI features, or run endpoint tests to verify functionality.
          </p>
        </div>
      </div>
    </div>
  );
}
