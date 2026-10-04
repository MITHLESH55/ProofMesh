import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ApiError } from '../services/api';

interface ErrorMessageProps {
  error: Error | ApiError | string | null;
  onRetry?: () => void;
  title?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ error, onRetry, title = 'Unable to load data' }) => {
  if (!error) return null;

  let message = 'An unexpected error occurred';
  let code = 'ERROR';
  let requestId = 'unknown';

  if (typeof error === 'string') {
    message = error;
  } else if (error instanceof ApiError) {
    message = error.message;
    code = error.code;
    requestId = error.requestId;
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <div className="bg-rose-950/40 border border-rose-900/60 rounded-xl p-6 text-slate-200">
      <div className="flex items-start gap-4">
        <div className="p-2 bg-rose-900/40 rounded-lg text-rose-400">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-rose-200">{title}</h3>
          <p className="mt-1 text-sm text-rose-300/90">{message}</p>
          <div className="mt-3 flex flex-wrap gap-4 text-xs font-mono text-slate-400">
            {code && <span>Code: <span className="text-slate-300">{code}</span></span>}
            {requestId && <span>Request ID: <span className="text-slate-300">{requestId}</span></span>}
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-rose-900/50 hover:bg-rose-900/80 text-rose-200 text-xs font-medium rounded-lg transition-colors border border-rose-800/60"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
