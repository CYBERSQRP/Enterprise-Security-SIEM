import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'MMM d, yyyy HH:mm:ss');
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'text-critical',
    high: 'text-high',
    medium: 'text-medium',
    low: 'text-low',
    info: 'text-info',
  };
  return colors[severity] || 'text-gray-500';
}

export function getSeverityBgColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'bg-red-100 dark:bg-red-900/20',
    high: 'bg-orange-100 dark:bg-orange-900/20',
    medium: 'bg-yellow-100 dark:bg-yellow-900/20',
    low: 'bg-blue-100 dark:bg-blue-900/20',
    info: 'bg-indigo-100 dark:bg-indigo-900/20',
  };
  return colors[severity] || 'bg-gray-100 dark:bg-gray-900/20';
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num);
}

export function truncate(str: string, length: number): string {
  return str.length > length ? str.substring(0, length) + '...' : str;
}
