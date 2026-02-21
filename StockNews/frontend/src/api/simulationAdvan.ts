import { apiClient, API_BASE_URL } from './client';
import type {
  AdvanEventListResponse,
  EventExtractRequest,
  EventExtractResponse,
  AdvanPolicyListItem,
  AdvanPolicy,
  AdvanPolicyCreate,
  AdvanPolicyUpdate,
  AdvanSimulationRun,
  AdvanSimulationRunCreate,
  AdvanSimulationRunDetail,
  AdvanCompareResponse,
  AdvanEvalRunResponse,
  OptimizeRequest,
  OptimizeResponse,
} from '../types/simulationAdvan';

// --- Events ---

export function fetchAdvanEvents(params?: {
  market?: string;
  event_type?: string;
  ticker?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}): Promise<AdvanEventListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.market) queryParams.append('market', params.market);
  if (params?.event_type) queryParams.append('event_type', params.event_type);
  if (params?.ticker) queryParams.append('ticker', params.ticker);
  if (params?.date_from) queryParams.append('date_from', params.date_from);
  if (params?.date_to) queryParams.append('date_to', params.date_to);
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const query = queryParams.toString();
  return apiClient.get<AdvanEventListResponse>(`/advan/events${query ? `?${query}` : ''}`);
}

export async function extractAdvanEvents(request: EventExtractRequest): Promise<EventExtractResponse> {
  const resp = await fetch(`${API_BASE_URL}/advan/events/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!resp.ok) throw new Error(`Failed to extract events: ${resp.statusText}`);
  return resp.json();
}

export interface AdvanEventTypeSummary {
  event_type: string;
  count: number;
  ratio: number;
  avg_magnitude: number;
  avg_credibility: number;
  avg_novelty: number;
}

export function fetchAdvanEventSummary(market: string): Promise<AdvanEventTypeSummary[]> {
  return apiClient.get<AdvanEventTypeSummary[]>(`/advan/events/summary?market=${market}`);
}

// --- Policies ---

export function fetchAdvanPolicies(): Promise<AdvanPolicyListItem[]> {
  return apiClient.get<AdvanPolicyListItem[]>('/advan/policies');
}

export function getAdvanPolicy(id: number): Promise<AdvanPolicy> {
  return apiClient.get<AdvanPolicy>(`/advan/policies/${id}`);
}

export async function createAdvanPolicy(data: AdvanPolicyCreate): Promise<AdvanPolicy> {
  const resp = await fetch(`${API_BASE_URL}/advan/policies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Failed to create policy: ${resp.statusText}`);
  return resp.json();
}

export async function updateAdvanPolicy(id: number, data: AdvanPolicyUpdate): Promise<AdvanPolicy> {
  const resp = await fetch(`${API_BASE_URL}/advan/policies/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Failed to update policy: ${resp.statusText}`);
  return resp.json();
}

export async function deleteAdvanPolicy(id: number): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/advan/policies/${id}`, {
    method: 'DELETE',
  });
  if (!resp.ok) throw new Error(`Failed to delete policy: ${resp.statusText}`);
}

export async function createDefaultPolicy(): Promise<AdvanPolicy> {
  const resp = await fetch(`${API_BASE_URL}/advan/policies/create-default`, {
    method: 'POST',
  });
  if (!resp.ok) throw new Error(`Failed to create default policy: ${resp.statusText}`);
  return resp.json();
}

// --- Simulation Runs ---

export function fetchAdvanRuns(params?: {
  market?: string;
  policy_id?: number;
  status?: string;
}): Promise<AdvanSimulationRun[]> {
  const queryParams = new URLSearchParams();
  if (params?.market) queryParams.append('market', params.market);
  if (params?.policy_id) queryParams.append('policy_id', params.policy_id.toString());
  if (params?.status) queryParams.append('status', params.status);

  const query = queryParams.toString();
  return apiClient.get<AdvanSimulationRun[]>(`/advan/runs${query ? `?${query}` : ''}`);
}

export function getAdvanRun(runId: number): Promise<AdvanSimulationRunDetail> {
  return apiClient.get<AdvanSimulationRunDetail>(`/advan/runs/${runId}`);
}

export async function createAdvanRun(data: AdvanSimulationRunCreate): Promise<AdvanSimulationRun> {
  const resp = await fetch(`${API_BASE_URL}/advan/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`Failed to create advan run: ${resp.statusText}`);
  return resp.json();
}

export async function deleteAdvanRun(runId: number): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/advan/runs/${runId}`, {
    method: 'DELETE',
  });
  if (!resp.ok) throw new Error(`Failed to delete advan run: ${resp.statusText}`);
}

export function fetchAdvanCompare(runIds: number[]): Promise<AdvanCompareResponse> {
  return apiClient.get<AdvanCompareResponse>(
    `/advan/runs/compare?run_ids=${runIds.join(',')}`
  );
}

// --- Run Analysis ---

export interface AdvanDirectionStat {
  total: number;
  correct: number;
}

export interface AdvanStockResult {
  stock_code: string;
  stock_name: string | null;
  total: number;
  correct: number;
  accuracy: number;
  latest_prediction: string | null;
  latest_label: string | null;
  latest_realized_ret: number | null;
  by_direction: Record<string, AdvanDirectionStat>;
}

export interface AdvanThemeResult {
  theme: string;
  total_stocks: number;
  correct_count: number;
  accuracy_rate: number;
}

export function fetchAdvanRunByStock(runId: number): Promise<AdvanStockResult[]> {
  return apiClient.get<AdvanStockResult[]>(`/advan/runs/${runId}/by-stock`);
}

export function fetchAdvanRunByTheme(runId: number): Promise<AdvanThemeResult[]> {
  return apiClient.get<AdvanThemeResult[]>(`/advan/runs/${runId}/by-theme`);
}

// --- Evaluation ---

export function fetchAdvanEvaluation(runId: number): Promise<AdvanEvalRunResponse> {
  return apiClient.get<AdvanEvalRunResponse>(`/advan/evaluate/${runId}`);
}

export function fetchAdvanGuardrails(runId: number): Promise<any> {
  return apiClient.get<any>(`/advan/evaluate/${runId}/guardrails`);
}

// --- Optimization ---

export async function startAdvanOptimization(request: OptimizeRequest): Promise<OptimizeResponse> {
  const resp = await fetch(`${API_BASE_URL}/advan/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!resp.ok) throw new Error(`Failed to start optimization: ${resp.statusText}`);
  return resp.json();
}
