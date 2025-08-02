import React, { useState } from 'react';
import { Send, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface FormData {
  field1: string;
  field2: string;
  field3: string;
  field4: string;
  field5: string; // NEW
}

interface ApiResponse {
  success: boolean;
  result?: string;
  error?: string;
}

function App() {
  const [formData, setFormData] = useState<FormData>({
    field1: '',
    field2: '',
    field3: '',
    field4: '',
    field5: '' // NEW
  });
  
  const [output, setOutput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!formData.field1 || !formData.field2 || !formData.field3 || !formData.field4 || !formData.field5) {
      setStatus('error');
      setOutput('Please fill in all fields');
      return;
    }

    setLoading(true);
    setStatus('idle');
    
    try {
      const response = await fetch('http://localhost:5000/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data: ApiResponse = await response.json();
      
      if (data.success && data.result) {
        setOutput(data.result);
        setStatus('success');
      } else {
        setOutput(data.error || 'An error occurred');
        setStatus('error');
      }
    } catch (error) {
      setOutput('Failed to connect to server. Make sure the Flask backend is running on port 5000.');
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      field1: '',
      field2: '',
      field3: '',
      field4: '',
      field5: '' // NEW
    });
    setOutput('');
    setStatus('idle');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8 pt-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Data Processing Interface
          </h1>
          <p className="text-lg text-gray-600">
            Enter your data below and get processed results instantly
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
              Input Parameters
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="field1" className="block text-sm font-medium text-gray-700 mb-2">
                    Field 1
                  </label>
                  <input
                    type="text"
                    id="field1"
                    value={formData.field1}
                    onChange={(e) => handleInputChange('field1', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="Enter value..."
                  />
                </div>
                
                <div>
                  <label htmlFor="field2" className="block text-sm font-medium text-gray-700 mb-2">
                    Field 2
                  </label>
                  <input
                    type="text"
                    id="field2"
                    value={formData.field2}
                    onChange={(e) => handleInputChange('field2', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="Enter value..."
                  />
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="field3" className="block text-sm font-medium text-gray-700 mb-2">
                    Field 3
                  </label>
                  <input
                    type="text"
                    id="field3"
                    value={formData.field3}
                    onChange={(e) => handleInputChange('field3', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="Enter value..."
                  />
                </div>
                
                <div>
                  <label htmlFor="field4" className="block text-sm font-medium text-gray-700 mb-2">
                    Field 4
                  </label>
                  <input
                    type="text"
                    id="field4"
                    value={formData.field4}
                    onChange={(e) => handleInputChange('field4', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="Enter value..."
                  />
                </div>
              </div>

              {/* NEW Field 5 */}
              <div>
                <label htmlFor="field5" className="block text-sm font-medium text-gray-700 mb-2">
                  Field 5
                </label>
                <input
                  type="text"
                  id="field5"
                  value={formData.field5}
                  onChange={(e) => handleInputChange('field5', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Enter value..."
                />
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  ) : (
                    <Send className="w-5 h-5 mr-2" />
                  )}
                  {loading ? 'Processing...' : 'Process Data'}
                </button>
                
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-6 py-3 border border-gray-300 hover:border-gray-400 text-gray-700 hover:text-gray-900 font-semibold rounded-lg transition-colors"
                >
                  Reset
                </button>
              </div>
            </form>
          </div>

          {/* Output Display */}
          {/* (Rest of the output code remains unchanged) */}
        </div>
      </div>
    </div>
  );
}

export default App;
