import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { incidentService } from '../services/incidentService';
import { Plus, Calendar, User, PlayCircle } from 'lucide-react';
import { formatDate, getSeverityBgColor } from '../lib/utils';
import { useToast } from '../components/ui/Toast';

export const IncidentsPage: React.FC = () => {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidentService.getIncidents(),
    refetchInterval: 15000,
  });

  const createMutation = useMutation({
    mutationFn: incidentService.createIncident,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      addToast({ type: 'success', message: 'Incident created successfully' });
      setShowCreateModal(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Incident Response</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus size={16} />
          Create Incident
        </button>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {['open', 'investigating', 'contained', 'resolved', 'closed'].map((status) => (
          <div key={status} className="glass-card p-4">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {incidents?.filter((i) => i.status === status).length || 0}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">{status}</p>
          </div>
        ))}
      </div>

      {/* Incidents List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="glass-card p-12 text-center text-gray-500 dark:text-gray-400">
            Loading incidents...
          </div>
        ) : incidents?.length === 0 ? (
          <div className="glass-card p-12 text-center text-gray-500 dark:text-gray-400">
            No incidents found
          </div>
        ) : (
          incidents?.map((incident) => (
            <div key={incident.id} className="glass-card p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityBgColor(incident.severity)}`}>
                      {incident.severity.toUpperCase()}
                    </span>
                    <span className={`status-badge status-${incident.status === 'open' ? 'new' : incident.status === 'resolved' ? 'resolved' : 'investigating'}`}>
                      {incident.status.toUpperCase()}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {incident.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-3">{incident.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                    <span className="flex items-center gap-1">
                      <Calendar size={14} />
                      {formatDate(incident.created_at)}
                    </span>
                    <span className="flex items-center gap-1">
                      <User size={14} />
                      {incident.assignee}
                    </span>
                    <span>Alerts: {incident.alert_ids.length}</span>
                    <span>Evidence: {incident.evidence_ids.length}</span>
                  </div>
                </div>
                <div className="flex gap-2 ml-4">
                  {incident.playbook_id && (
                    <button className="px-4 py-2 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 flex items-center gap-2">
                      <PlayCircle size={16} />
                      Run Playbook
                    </button>
                  )}
                  <button className="px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-blue-700">
                    View Details
                  </button>
                </div>
              </div>

              {/* Timeline Preview */}
              {incident.timeline.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Recent Activity</h4>
                  <div className="space-y-2">
                    {incident.timeline.slice(-3).map((event, index) => (
                      <div key={index} className="flex items-center gap-3 text-sm">
                        <span className="text-gray-500 dark:text-gray-400 w-32">{formatDate(event.timestamp)}</span>
                        <span className="text-gray-600 dark:text-gray-400">{event.user}:</span>
                        <span className="text-gray-900 dark:text-white">{event.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
