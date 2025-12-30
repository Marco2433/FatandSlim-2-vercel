import { useState, useEffect } from 'react';
import axios from 'axios';
import { Sparkles, AlertCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AIUsageStatus({ className = "", onStatusChange = null }) {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUsage = async () => {
    try {
      const response = await axios.get(`${API}/ai/usage`, { withCredentials: true });
      setUsage(response.data);
      if (onStatusChange) {
        onStatusChange(response.data);
      }
    } catch (error) {
      console.error('Error fetching AI usage:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  if (loading || !usage) return null;

  const isLimitReached = usage.remaining === 0;
  
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs ${
      isLimitReached 
        ? 'bg-red-500/10 text-red-600 dark:text-red-400' 
        : 'bg-primary/10 text-primary'
    } ${className}`}>
      {isLimitReached ? (
        <>
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Limite IA atteinte</span>
        </>
      ) : (
        <>
          <Sparkles className="w-3.5 h-3.5" />
          <span>{usage.remaining}/{usage.limit} appels IA</span>
        </>
      )}
    </div>
  );
}
