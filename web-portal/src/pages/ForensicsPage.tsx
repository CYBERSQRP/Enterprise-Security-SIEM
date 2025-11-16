import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@antml:react-query';
import { forensicsService } from '../services/forensicsService';
import { Upload, Download, Shield, CheckCircle, XCircle, FileText } from 'lucide-react';
import { formatDate, formatBytes } from '../lib/utils';
import { useToast } from '../components/ui/Toast';

export const ForensicsPage: React.FC = () => {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { data: evidenceList } = useQuery({
    queryKey: ['evidence'],
    queryFn: () => forensicsService.getEvidenceList(),
  });

  const collectMutation = useMutation({
    mutationFn: (formData: FormData) => forensicsService.collectEvidence(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
      addToast({ type: 'success', message: 'Evidence collected successfully' });
      setSelectedFile(null);
    },
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleCollect = () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('type', 'file');
    formData.append('source', 'web-upload');
    collectMutation.mutate(formData);
  };

  const getVerdictColor = (verdict: string) => {
    const colors: Record<string, string> = {
      malicious: 'text-red-600 bg-red-100 dark:bg-red-900/20',
      suspicious: 'text-orange-600 bg-orange-100 dark:bg-orange-900/20',
      clean: 'text-green-600 bg-green-100 dark:bg-green-900/20',
      unknown: 'text-gray-600 bg-gray-100 dark:bg-gray-900/20',
    };
    return colors[verdict] || colors.unknown;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Forensics Evidence</h1>
      </div>

      {/* Evidence Upload */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Collect Evidence</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <input
              type="file"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer bg-white dark:bg-gray-700 focus:outline-none"
            />
          </div>
          <button
            onClick={handleCollect}
            disabled={!selectedFile}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Upload size={16} />
            Collect
          </button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          All evidence will be cryptographically signed and chain of custody will be maintained
        </p>
      </div>

      {/* Evidence List */}
      <div className="glass-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Hash
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Analysis
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Collected
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
              {evidenceList?.map((evidence) => (
                <tr key={evidence.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <FileText size={16} className="text-gray-400" />
                      <span className="text-sm text-gray-900 dark:text-white capitalize">{evidence.type}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {evidence.source}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600 dark:text-gray-400">
                    {evidence.hash.substring(0, 16)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {formatBytes(evidence.size)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {evidence.analysis_results && evidence.analysis_results.length > 0 ? (
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getVerdictColor(evidence.analysis_results[0].verdict)}`}>
                        {evidence.analysis_results[0].verdict.toUpperCase()}
                      </span>
                    ) : (
                      <span className="text-sm text-gray-500 dark:text-gray-400">Pending</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                    {formatDate(evidence.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex gap-2">
                      <button className="p-1 text-blue-600 hover:text-blue-800">
                        <Download size={16} />
                      </button>
                      <button className="p-1 text-green-600 hover:text-green-800">
                        <Shield size={16} />
                      </button>
                    </div>
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
