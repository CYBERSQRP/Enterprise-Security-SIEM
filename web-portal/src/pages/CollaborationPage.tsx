import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { collaborationService } from '../services/collaborationService';
import { Users, MessageCircle, Plus, Video } from 'lucide-react';
import { formatDate } from '../lib/utils';
import { useAuthStore } from '../store/authStore';

export const CollaborationPage: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<any[]>([]);

  const { data: sessions } = useQuery({
    queryKey: ['collaborationSessions'],
    queryFn: () => collaborationService.getSessions(),
  });

  useEffect(() => {
    if (selectedSession) {
      collaborationService.joinSession(selectedSession);

      collaborationService.onMessage((msg) => {
        setMessages((prev) => [...prev, msg]);
      });

      return () => {
        collaborationService.leaveSession(selectedSession);
      };
    }
  }, [selectedSession]);

  const handleSendMessage = () => {
    if (message.trim() && selectedSession) {
      collaborationService.sendMessage(selectedSession, message);
      setMessage('');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Collaboration Hub</h1>
        <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus size={16} />
          New Session
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sessions List */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Active Sessions</h2>
          <div className="space-y-3">
            {sessions?.map((session) => (
              <div
                key={session.id}
                onClick={() => setSelectedSession(session.id)}
                className={`p-4 rounded-lg cursor-pointer transition-colors ${
                  selectedSession === session.id
                    ? 'bg-primary text-white'
                    : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">Incident #{session.incident_id.substring(0, 8)}</h4>
                  <span className={`px-2 py-1 text-xs rounded ${
                    session.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {session.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Users size={14} />
                  <span>{session.participants.length} participants</span>
                </div>
                <p className="text-xs mt-1 opacity-75">
                  Created {formatDate(session.created_at)}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-2 glass-card p-6 flex flex-col" style={{ height: '600px' }}>
          {selectedSession ? (
            <>
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Investigation Session
                </h2>
                <div className="flex gap-2">
                  <button className="px-3 py-1 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 flex items-center gap-2">
                    <Video size={16} />
                    Start Call
                  </button>
                </div>
              </div>

              {/* Participants */}
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Participants</h3>
                <div className="flex gap-2">
                  {sessions?.find(s => s.id === selectedSession)?.participants.map((participant) => (
                    <div
                      key={participant.user_id}
                      className="flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-sm"
                    >
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: participant.color }}
                      />
                      {participant.username}
                    </div>
                  ))}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto scrollbar-thin mb-4 space-y-3">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.user === user?.username ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] px-4 py-2 rounded-lg ${
                        msg.user === user?.username
                          ? 'bg-primary text-white'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                      }`}
                    >
                      <div className="text-xs opacity-75 mb-1">{msg.user}</div>
                      <div>{msg.message}</div>
                      <div className="text-xs opacity-75 mt-1">{formatDate(msg.timestamp)}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Message Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <button
                  onClick={handleSendMessage}
                  className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <MessageCircle size={16} />
                  Send
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
              Select a session to start collaborating
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
