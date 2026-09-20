import axios from 'axios';
import { AuditRecord, AuditDetailResponse } from '../types/api';

const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

export const guardianApi = {
  getAudits: async (): Promise<AuditRecord[]> => {
    const { data } = await api.get('/audits');
    return data;
  },
  
  getAudit: async (id: string): Promise<AuditDetailResponse> => {
    const { data } = await api.get(`/audits/${id}`);
    return data;
  },
  
  createAudit: async (repoUrl: string): Promise<{status: string}> => {
    const { data } = await api.post('/audits', { repo_url: repoUrl });
    return data;
  },

  getIntegrations: async () => {
    const { data } = await api.get('/integrations');
    return data;
  }
};
