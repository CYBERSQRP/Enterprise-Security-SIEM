import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertService } from '../services/alertService';
import { AlertTriangle, CheckCircle, XCircle, User } from 'lucide-react';
import { formatDate, formatRelativeTime, getSeverityBgColor } from '../lib/utils';
import { useToast } from '../components/ui/Toast';
import { AlertStatus } from '../types';

export const AlertsPage: React.FC = () => {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<AlertStatus[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', { status: statusFilter }],
    queryFn: () => alertService.getAlerts({ status: statusFilter.length ? statusFilter : undefined }),
    refetchInterval: 10000,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => alertService.acknowledgeAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      addToast({ type: 'success', message: 'Alert acknowledged' });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: AlertStatus }) =>
      alertService.updateAlertStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      addToast({ type: 'success', message: 'Alert status updated' });
    },
  });

  const statuses: AlertStatus[] = ['new', 'acknowledged', 'investigating', 'resolved', 'false_positive'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Alert Management</h1>
        <div className="flex gap-2">
          {statuses.map((status) => (
            <button
              key={status}
              onClick={() =>
                setStatusFilter((prev) =>
                  prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
                )
              }
              className={`px-3 py-1 text-sm rounded-lg border ${
                statusFilter.includes(status)
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600'
              }`}
            >
              {status.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'New', count: data?.alerts.filter((a) => a.status === 'new').length || 0, color: 'blue' },
          { label: 'Acknowledged', count: data?.alerts.filter((a) => a.status === 'acknowledged').length || 0, color: 'yellow' },
          { label: 'Investigating', count: data?.alerts.filter((a) => a.status === 'investigating').length || 0, color: 'orange' },
          { label: 'Resolved', count: data?.alerts.filter((a) => a.status === 'resolved').length || 0, color: 'green' },
        ].map((stat) => (
          <div key={stat.label} className="glass-card p-4">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{stat.count}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="glass-card p-12 text-center text-gray-500 dark:text-gray-400">
            Loading alerts...
          </div>
        ) : data?.alerts.length === 0 ? (
          <div className="glass-card p-12 text-center text-gray-500 dark:text-gray-400">
            No alerts found
          </div>
        ) : (
          data?.alerts.map((alert) => (
            <div key={alert.id} className="glass-card p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityBgColor(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className={`status-badge status-${alert.status}`}>
                      {alert.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <AlertTriangle size={18} className="text-orange-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {alert.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-3">{alert.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                    <span>Rule: {alert.rule_name}</span>
                    <span>Events: {alert.event_count}</span>
                    <span>{formatRelativeTime(alert.created_at)}</span>
                    {alert.assignee && (
                      <span className="flex items-center gap-1">
                        <User size={14} />
                        {alert.assignee}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-2 ml-4">
                  {alert.status === 'new' && (
                    <button
                      onClick={() => acknowledgeMutation.mutate(alert.id)}
                      className="px-4 py-2 bg-yellow-500 text-white text-sm rounded-lg hover:bg-yellow-600 flex items-center gap-2"
                    >
                      <CheckCircle size={16} />
                      Acknowledge
                    </button>
                  )}
                  {(alert.status === 'new' || alert.status === 'acknowledged') && (
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: alert.id, status: 'investigating' })}
                      className="px-4 py-2 bg-orange-500 text-white text-sm rounded-lg hover:bg-orange-600"
                    >
                      Investigate
                    </button>
                  )}
                  {alert.status === 'investigating' && (
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: alert.id, status: 'resolved' })}
                      className="px-4 py-2 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600"
                    >
                      Resolve
                    </button>
                  )}
                  <button
                    onClick={() => updateStatusMutation.mutate({ id: alert.id, status: 'false_positive' })}
                    className="px-4 py-2 bg-gray-500 text-white text-sm rounded-lg hover:bg-gray-600 flex items-center gap-2"
                  >
                    <XCircle size={16} />
                    False Positive
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
