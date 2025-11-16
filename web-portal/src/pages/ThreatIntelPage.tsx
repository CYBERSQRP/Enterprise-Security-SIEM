import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { threatIntelService } from '../services/threatIntelService';
import { Shield, Plus, RefreshCw, Search, Database } from 'lucide-react';
import { formatDate, getSeverityBgColor } from '../lib/utils';
import { useToast } from '../components/ui/Toast';

export const ThreatIntelPage: React.FC = () => {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [lookupValue, setLookupValue] = useState('');
  const [lookupResult, setLookupResult] = useState<any>(null);

  const { data: feeds } = useQuery({
    queryKey: ['threatFeeds'],
    queryFn: () => threatIntelService.getFeeds(),
  });

  const { data: iocStats } = useQuery({
    queryKey: ['iocStats'],
    queryFn: () => threatIntelService.getIOCStats(),
  });

  const syncMutation = useMutation({
    mutationFn: (feedId: string) => threatIntelService.syncFeed(feedId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threatFeeds'] });
      addToast({ type: 'success', message: 'Feed synced successfully' });
    },
  });

  const handleLookup = async () => {
    try {
      const result = await threatIntelService.lookupIOC(lookupValue);
      setLookupResult(result);
      if (!result) {
        addToast({ type: 'info', message: 'No threat intelligence found for this indicator' });
      }
    } catch (error) {
      addToast({ type: 'error', message: 'Lookup failed' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Threat Intelligence</h1>
        <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus size={16} />
          Add Feed
        </button>
      </div>

      {/* IOC Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="glass-card p-4">
          <Database className="text-blue-600 mb-2" size={24} />
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
            {iocStats?.total_iocs || 0}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">Total IOCs</p>
        </div>
        {['ip', 'domain', 'url', 'hash'].map((type) => (
          <div key={type} className="glass-card p-4">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {iocStats?.by_type?.[type] || 0}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">{type}s</p>
          </div>
        ))}
      </div>

      {/* IOC Lookup */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">IOC Lookup</h2>
        <div className="flex gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={lookupValue}
              onChange={(e) => setLookupValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLookup()}
              placeholder="Enter IP, domain, URL, or hash..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <button
            onClick={handleLookup}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700"
          >
            Lookup
          </button>
        </div>

        {lookupResult && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900 dark:text-white">Threat Found</h4>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityBgColor(lookupResult.severity)}`}>
                {lookupResult.severity.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Type:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{lookupResult.type}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{(lookupResult.confidence * 100).toFixed(0)}%</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">First Seen:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{formatDate(lookupResult.first_seen)}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Sources:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{lookupResult.sources.join(', ')}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Threat Feeds */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Configured Feeds</h2>
        <div className="space-y-3">
          {feeds?.map((feed) => (
            <div key={feed.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-4">
                <Shield className={feed.enabled ? 'text-green-600' : 'text-gray-400'} size={24} />
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">{feed.name}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{feed.source}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">{feed.ioc_count}</span> IOCs
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Updated {formatDate(feed.last_updated)}
                </div>
                <button
                  onClick={() => syncMutation.mutate(feed.id)}
                  className="px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <RefreshCw size={16} />
                  Sync
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
