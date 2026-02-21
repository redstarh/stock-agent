import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAdvanEvents,
  fetchAdvanEventSummary,
  extractAdvanEvents,
  fetchAdvanPolicies,
  fetchAdvanRunByStock,
  fetchAdvanRunByTheme,
  getAdvanPolicy,
  createAdvanPolicy,
  updateAdvanPolicy,
  deleteAdvanPolicy,
  createDefaultPolicy,
  fetchAdvanRuns,
  getAdvanRun,
  createAdvanRun,
  deleteAdvanRun,
  fetchAdvanCompare,
  fetchAdvanEvaluation,
  fetchAdvanGuardrails,
  startAdvanOptimization,
} from '../api/simulationAdvan';
import type {
  EventExtractRequest,
  AdvanPolicyCreate,
  AdvanPolicyUpdate,
  AdvanSimulationRunCreate,
  OptimizeRequest,
} from '../types/simulationAdvan';

// --- Events ---

export function useAdvanEvents(params?: {
  market?: string;
  event_type?: string;
  ticker?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['advan', 'events', params],
    queryFn: () => fetchAdvanEvents(params),
  });
}

export function useAdvanEventSummary(market: string) {
  return useQuery({
    queryKey: ['advan', 'events', 'summary', market],
    queryFn: () => fetchAdvanEventSummary(market),
  });
}

export function useExtractEvents() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: EventExtractRequest) => extractAdvanEvents(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'events'] });
    },
  });
}

// --- Policies ---

export function useAdvanPolicies() {
  return useQuery({
    queryKey: ['advan', 'policies'],
    queryFn: fetchAdvanPolicies,
  });
}

export function useAdvanPolicy(id: number | null) {
  return useQuery({
    queryKey: ['advan', 'policy', id],
    queryFn: () => getAdvanPolicy(id!),
    enabled: id !== null,
  });
}

export function useCreateAdvanPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AdvanPolicyCreate) => createAdvanPolicy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'policies'] });
    },
  });
}

export function useUpdateAdvanPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AdvanPolicyUpdate }) =>
      updateAdvanPolicy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'policies'] });
    },
  });
}

export function useDeleteAdvanPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteAdvanPolicy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'policies'] });
    },
  });
}

export function useCreateDefaultPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => createDefaultPolicy(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'policies'] });
    },
  });
}

// --- Simulation Runs ---

export function useAdvanRuns(params?: {
  market?: string;
  policy_id?: number;
  status?: string;
}) {
  return useQuery({
    queryKey: ['advan', 'runs', params],
    queryFn: () => fetchAdvanRuns(params),
  });
}

export function useAdvanRun(runId: number | null) {
  return useQuery({
    queryKey: ['advan', 'run', runId],
    queryFn: () => getAdvanRun(runId!),
    enabled: runId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.run?.status;
      return status === 'running' || status === 'pending' ? 3000 : false;
    },
  });
}

export function useCreateAdvanRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AdvanSimulationRunCreate) => createAdvanRun(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'runs'] });
    },
  });
}

export function useDeleteAdvanRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (runId: number) => deleteAdvanRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'runs'] });
    },
  });
}

export function useAdvanRunByStock(runId: number | null) {
  return useQuery({
    queryKey: ['advan', 'run', runId, 'by-stock'],
    queryFn: () => fetchAdvanRunByStock(runId!),
    enabled: runId !== null,
  });
}

export function useAdvanRunByTheme(runId: number | null) {
  return useQuery({
    queryKey: ['advan', 'run', runId, 'by-theme'],
    queryFn: () => fetchAdvanRunByTheme(runId!),
    enabled: runId !== null,
  });
}

export function useAdvanCompare(runIds: number[]) {
  return useQuery({
    queryKey: ['advan', 'compare', runIds],
    queryFn: () => fetchAdvanCompare(runIds),
    enabled: runIds.length >= 2,
  });
}

// --- Evaluation ---

export function useAdvanEvaluation(runId: number | null) {
  return useQuery({
    queryKey: ['advan', 'evaluation', runId],
    queryFn: () => fetchAdvanEvaluation(runId!),
    enabled: runId !== null,
  });
}

export function useAdvanGuardrails(runId: number | null) {
  return useQuery({
    queryKey: ['advan', 'guardrails', runId],
    queryFn: () => fetchAdvanGuardrails(runId!),
    enabled: runId !== null,
  });
}

// --- Optimization ---

export function useStartOptimization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: OptimizeRequest) => startAdvanOptimization(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advan', 'policies'] });
      queryClient.invalidateQueries({ queryKey: ['advan', 'runs'] });
    },
  });
}
