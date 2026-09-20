import { useState, useEffect } from 'react';
import { guardianApi } from '../services/api';
import { AuditRecord, AuditDetailResponse } from '../types/api';

export function useAudit(auditId: string) {
  const [data, setData] = useState<AuditDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    let pollInterval: ReturnType<typeof setInterval> | null = null;

    const fetchAudit = async () => {
      try {
        const response = await guardianApi.getAudit(auditId);
        if (isMounted) {
          setData(response);
          setError(null);

          // Stop polling if complete or failed
          if (response.audit.status === 'COMPLETE' || response.audit.status === 'FAILED') {
            if (pollInterval) clearInterval(pollInterval);
            setLoading(false);
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to fetch audit');
          setLoading(false);
        }
      }
    };

    fetchAudit();

    // Poll every 2 seconds
    pollInterval = setInterval(fetchAudit, 2000);

    return () => {
      isMounted = false;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [auditId]);

  return { data, loading, error };
}
