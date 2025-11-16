import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { eventService } from '../services/eventService';
import { alertService } from '../services/alertService';
import { analyticsService } from '../services/analyticsService';
import { Activity, AlertTriangle, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatNumber, getSeverityColor } from '../lib/utils';

export const DashboardPage: React.FC = () => {
  const { data: eventStats } = useQuery({
    queryKey: ['eventStats'],
    queryFn: () => eventService.getEventStats(),
    refetchInterval: 5000,
  });

  const { data: alertStats } = useQuery({
    queryKey: ['alertStats'],
    queryFn: () => alertService.getAlertStats(),
    refetchInterval: 5000,
  });

  const { data: insights } = useQuery({
    queryKey: ['insights'],
    queryFn: () => analyticsService.getInsights(),
  });

  const metrics = [
    {
      title: 'Events Today',
      value: eventStats?.today_count || 0,
      change: eventStats?.change_percent || 0,
      icon: Activity,
      color: 'text-blue-600',
      bg: 'bg-blue-100 dark:bg-blue-900/20',
    },
    {
      title: 'Active Alerts',
      value: alertStats?.active_count || 0,
      change: alertStats?.new_today || 0,
      icon: AlertTriangle,
      color: 'text-red-600',
      bg: 'bg-red-100 dark:bg-red-900/20',
    },
    {
      title: 'Critical Incidents',
      value: alertStats?.critical_count || 0,
      change: -12,
      icon: TrendingDown,
      color: 'text-orange-600',
      bg: 'bg-orange-100 dark:bg-orange-900/20',
    },
    {
      title: 'Avg Response Time',
      value: '12m',
      change: -8,
      icon: Clock,
      color: 'text-green-600',
      bg: 'bg-green-100 dark:bg-green-900/20',
    },
  ];

  const severityData = [
    { name: 'Critical', value: alertStats?.by_severity?.critical || 0, color: '#dc2626' },
    { name: 'High', value: alertStats?.by_severity?.high || 0, color: '#ea580c' },
    { name: 'Medium', value: alertStats?.by_severity?.medium || 0, color: '#f59e0b' },
    { name: 'Low', value: alertStats?.by_severity?.low || 0, color: '#3b82f6' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Security Overview</h1>
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <div className="live-indicator">
            <span></span>
            <span></span>
          </div>
          Real-time monitoring active
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          const isPositive = metric.change > 0;
          return (
            <div key={index} className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`${metric.bg} p-3 rounded-lg`}>
                  <Icon className={metric.color} size={24} />
                </div>
                <div className={`flex items-center gap-1 text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  {Math.abs(metric.change)}%
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                {typeof metric.value === 'number' ? formatNumber(metric.value) : metric.value}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{metric.title}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Events Timeline */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Event Trends (24h)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={eventStats?.hourly_data || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Alert Severity Distribution */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Alert Severity Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Critical Alerts</h2>
          <Link to="/alerts" className="text-sm text-primary hover:underline">View all</Link>
        </div>
        <div className="space-y-3">
          {alertStats?.recent_alerts?.slice(0, 5).map((alert: any) => (
            <div key={alert.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                    {alert.severity.toUpperCase()}
                  </span>
                  <h3 className="font-medium text-gray-900 dark:text-white">{alert.title}</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{alert.description}</p>
              </div>
              <Link
                to={`/alerts`}
                className="ml-4 px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-blue-700"
              >
                Investigate
              </Link>
            </div>
          )) || <p className="text-gray-500 dark:text-gray-400 text-center py-8">No recent critical alerts</p>}
        </div>
      </div>

      {/* AI Insights */}
      {insights && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI-Generated Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.insights?.map((insight: any, index: number) => (
              <div key={index} className="p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded">
                <h4 className="font-medium text-gray-900 dark:text-white mb-1">{insight.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">{insight.description}</p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                  Confidence: {(insight.confidence * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
