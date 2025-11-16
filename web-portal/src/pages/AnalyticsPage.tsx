import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tantml:react-query';
import { analyticsService } from '../services/analyticsService';
import { Brain, TrendingUp, Target, Activity, PlayCircle } from 'lucide-react';
import { formatDate } from '../lib/utils';
import { useToast } from '../components/ui/Toast';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const { data: models } = useQuery({
    queryKey: ['predictiveModels'],
    queryFn: () => analyticsService.getModels(),
  });

  const { data: insights } = useQuery({
    queryKey: ['analyticsInsights'],
    queryFn: () => analyticsService.getInsights(),
  });

  const { data: threatTrends } = useQuery({
    queryKey: ['threatTrends'],
    queryFn: () => analyticsService.getThreatTrends(),
  });

  const trainMutation = useMutation({
    mutationFn: (modelId: string) => analyticsService.trainModel(modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['predictiveModels'] });
      addToast({ type: 'success', message: 'Model training started' });
    },
  });

  const getModelIcon = (type: string) => {
    switch (type) {
      case 'threat_forecast': return TrendingUp;
      case 'anomaly_detection': return Target;
      case 'risk_prediction': return Activity;
      default: return Brain;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Predictive Analytics</h1>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
          <Brain className="text-green-600" size={20} />
          <span className="text-sm font-medium text-green-800 dark:text-green-200">AI Models Active</span>
        </div>
      </div>

      {/* AI Models */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {models?.map((model) => {
          const Icon = getModelIcon(model.type);
          return (
            <div key={model.id} className="glass-card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                  <Icon className="text-blue-600" size={24} />
                </div>
                <button
                  onClick={() => trainMutation.mutate(model.id)}
                  className="px-3 py-1 bg-primary text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-1"
                >
                  <PlayCircle size={14} />
                  Train
                </button>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{model.name}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Accuracy</span>
                  <span className="font-medium text-gray-900 dark:text-white">{(model.accuracy * 100).toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Last Trained</span>
                  <span className="text-gray-900 dark:text-white">{formatDate(model.last_trained)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Predictions</span>
                  <span className="font-medium text-gray-900 dark:text-white">{model.predictions.length}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Threat Trends */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Threat Trends</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={threatTrends?.hourly || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="threats" stroke="#ef4444" strokeWidth={2} name="Threats Detected" />
            <Line type="monotone" dataKey="anomalies" stroke="#f97316" strokeWidth={2} name="Anomalies" />
            <Line type="monotone" dataKey="predicted" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" name="Predicted" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Insights */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI-Generated Insights</h2>
          <div className="space-y-3">
            {insights?.insights?.map((insight: any, index: number) => (
              <div key={index} className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900 dark:text-white">{insight.title}</h4>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {(insight.confidence * 100).toFixed(0)}% confident
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{insight.description}</p>
                {insight.recommendation && (
                  <p className="text-sm text-blue-700 dark:text-blue-300 mt-2">
                    Recommendation: {insight.recommendation}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Risk Scores */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Risk Entities</h2>
          <div className="space-y-3">
            {insights?.risk_entities?.map((entity: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">{entity.name}</h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400 capitalize">{entity.type}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900 dark:text-white">{entity.score}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Risk Score</div>
                  </div>
                  <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        entity.score >= 75 ? 'bg-red-600' :
                        entity.score >= 50 ? 'bg-orange-600' :
                        entity.score >= 25 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${entity.score}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Anomaly Detection */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Anomalies</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
              {insights?.anomalies?.map((anomaly: any, index: number) => (
                <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {formatDate(anomaly.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white capitalize">
                    {anomaly.type}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                    {anomaly.description}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {(anomaly.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-800">
                      Under Review
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
