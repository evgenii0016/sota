import type {
  ApiErrorBody,
  Task13AssistantRequest,
  Task13AssistantResponse,
  Task13AttemptView,
  Task13BatchResponse,
  Task13GradeRequest,
  Task13GradeResponse,
  Task13View,
} from './types'
import { ApiError } from './types'
import { normalizeEquationLatex } from '../utils/normalizeEquationLatex'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

function normalizeTask13View(task: Task13View): Task13View {
  if (!task.equation_latex) {
    return task
  }

  return {
    ...task,
    equation_latex: normalizeEquationLatex(task.equation_latex),
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let body: ApiErrorBody = {
      code: 'unknown_error',
      message: response.statusText || 'Ошибка запроса',
    }
    try {
      const parsed = (await response.json()) as Partial<ApiErrorBody>
      if (parsed.code && parsed.message) {
        body = parsed as ApiErrorBody
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(response.status, body)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function createTask13Batch(count = 3): Promise<Task13BatchResponse> {
  return request<Task13BatchResponse>(`/tasks/task13/batch?count=${count}`, {
    method: 'POST',
  }).then((response) => ({
    ...response,
    tasks: response.tasks.map(normalizeTask13View),
  }))
}

export function getTask13(taskId: string): Promise<Task13View> {
  return request<Task13View>(`/tasks/${taskId}`).then(normalizeTask13View)
}

export function gradeTask13(
  taskId: string,
  body: Task13GradeRequest,
): Promise<Task13GradeResponse> {
  return request<Task13GradeResponse>(`/tasks/${taskId}/grade`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function getAttempt(attemptId: string): Promise<Task13AttemptView> {
  return request<Task13AttemptView>(`/attempts/${attemptId}`)
}

export function getTaskAttempts(taskId: string): Promise<Task13AttemptView[]> {
  return request<Task13AttemptView[]>(`/tasks/${taskId}/attempts`)
}

export function askAssistant(
  taskId: string,
  body: Task13AssistantRequest,
): Promise<Task13AssistantResponse> {
  return request<Task13AssistantResponse>(`/tasks/${taskId}/assistant`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
