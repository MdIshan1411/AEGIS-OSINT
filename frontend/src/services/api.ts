import axios from 'axios'
import type {
  Investigation,
  InvestigateRequest,
} from '@/types/api'
import type { EmailScanResponse } from '@/types/email-scanner'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  async createInvestigation(
    request: InvestigateRequest
  ): Promise<Investigation> {
    const response = await client.post<Investigation>(
      '/investigation/create',
      request
    )
    return response.data
  },

  async getInvestigation(investigationId: string): Promise<Investigation> {
    const response = await client.get<Investigation>(
      `/investigation/${investigationId}`
    )
    return response.data
  },

  async resolveConflict(
    investigationId: string,
    conflictId: string,
    resolution: 'EXPLAINED' | 'REJECTED',
    note: string
  ): Promise<any> {
    const response = await client.patch(
      `/investigate/${investigationId}/conflicts/${conflictId}`,
      {
        resolution,
        resolution_note: note,
      }
    )
    return response.data
  },

  async getCandidate(candidateId: string): Promise<any> {
    const response = await client.get(`/candidates/${candidateId}`)
    return response.data
  },

  async scanEmail(email: string): Promise<EmailScanResponse> {
    const response = await client.post<EmailScanResponse>(
      '/email-scanner/scan',
      { email }
    )
    return response.data
  },
}
