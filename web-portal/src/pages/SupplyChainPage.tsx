import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supplyChainService } from '../services/supplyChainService';
import { Package, AlertTriangle, CheckCircle, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';
import { formatDate } from '../lib/utils';
import { useToast } from '../components/ui/Toast';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export const SupplyChainPage: React.FC = () => {
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const { data: vendors } = useQuery({
    queryKey: ['vendors'],
    queryFn: () => supplyChainService.getVendors(),
  });

  const { data: riskTrends } = useQuery({
    queryKey: ['riskTrends'],
    queryFn: () => supplyChainService.getRiskTrends(),
  });

  const assessMutation = useMutation({
    mutationFn: (vendorId: string) => supplyChainService.assessVendor(vendorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      addToast({ type: 'success', message: 'Vendor assessment completed' });
    },
  });

  const getRiskColor = (score: number) => {
    if (score >= 75) return 'text-red-600 bg-red-100 dark:bg-red-900/20';
    if (score >= 50) return 'text-orange-600 bg-orange-100 dark:bg-orange-900/20';
    if (score >= 25) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
    return 'text-green-600 bg-green-100 dark:bg-green-900/20';
  };

  const getRiskLevel = (score: number) => {
    if (score >= 75) return 'Critical';
    if (score >= 50) return 'High';
    if (score >= 25) return 'Medium';
    return 'Low';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Supply Chain Security</h1>
        <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700">
          Add Vendor
        </button>
      </div>

      {/* Risk Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Vendors', value: vendors?.length || 0, icon: Package },
          { label: 'Critical Risk', value: vendors?.filter(v => v.risk_score >= 75).length || 0, icon: AlertTriangle },
          { label: 'Compliant', value: vendors?.filter(v => Object.values(v.compliance_status).every(Boolean)).length || 0, icon: CheckCircle },
          { label: 'Pending Review', value: vendors?.filter(v => !v.last_assessment).length || 0, icon: RefreshCw },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="glass-card p-4">
              <Icon className="text-blue-600 mb-2" size={24} />
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
            </div>
          );
        })}
      </div>

      {/* Risk Trends */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Trends</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={riskTrends?.data || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="avg_risk_score" stroke="#ef4444" strokeWidth={2} name="Avg Risk Score" />
            <Line type="monotone" dataKey="critical_count" stroke="#f97316" strokeWidth={2} name="Critical Vendors" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Vendors List */}
      <div className="glass-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Vendor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Vulnerabilities
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Compliance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Last Assessment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
              {vendors?.map((vendor) => (
                <tr key={vendor.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{vendor.name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{vendor.domain}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 text-sm font-medium rounded ${getRiskColor(vendor.risk_score)}`}>
                        {getRiskLevel(vendor.risk_score)}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">({vendor.risk_score})</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex gap-2">
                      {vendor.vulnerabilities.filter(v => v.severity === 'critical').length > 0 && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                          {vendor.vulnerabilities.filter(v => v.severity === 'critical').length} Critical
                        </span>
                      )}
                      {vendor.vulnerabilities.filter(v => v.severity === 'high').length > 0 && (
                        <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded">
                          {vendor.vulnerabilities.filter(v => v.severity === 'high').length} High
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {Object.values(vendor.compliance_status).every(Boolean) ? (
                      <CheckCircle className="text-green-600" size={20} />
                    ) : (
                      <AlertTriangle className="text-yellow-600" size={20} />
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                    {vendor.last_assessment ? formatDate(vendor.last_assessment) : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => assessMutation.mutate(vendor.id)}
                      className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                    >
                      <RefreshCw size={16} />
                      Assess
                    </button>
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
