import type { Task13View } from '../api/types'
import { normalizeEquationLatex } from './normalizeEquationLatex'

const HISTORY_KEY = 'task13-batch-history-v1'
const LEGACY_SESSION_KEY = 'task13-batch-v2'
const MAX_BATCHES = 10

export interface Task13BatchRecord {
  id: string
  createdAt: string
  tasks: Task13View[]
  results: Record<string, Task13TaskResult>
}

export interface Task13TaskResult {
  score: 0 | 1 | 2
  attemptId: string
  completedAt: string
}

interface BatchHistoryStore {
  batches: Task13BatchRecord[]
}

function normalizeTask(task: Task13View): Task13View {
  if (!task.equation_latex) {
    return task
  }

  return {
    ...task,
    equation_latex: normalizeEquationLatex(task.equation_latex),
  }
}

function normalizeTasks(tasks: Task13View[]): Task13View[] {
  return tasks
    .filter(
      (item): item is Task13View =>
        typeof item === 'object' &&
        item !== null &&
        typeof item.id === 'string' &&
        item.task_type === 'task_13',
    )
    .map(normalizeTask)
}

function normalizeResults(raw: unknown, tasks: Task13View[]): Record<string, Task13TaskResult> {
  if (typeof raw !== 'object' || raw === null) {
    return {}
  }

  const taskIds = new Set(tasks.map((task) => task.id))
  return Object.fromEntries(
    Object.entries(raw).flatMap(([taskId, value]) => {
      if (
        !taskIds.has(taskId) ||
        typeof value !== 'object' ||
        value === null ||
        ![0, 1, 2].includes((value as Task13TaskResult).score) ||
        typeof (value as Task13TaskResult).attemptId !== 'string' ||
        typeof (value as Task13TaskResult).completedAt !== 'string'
      ) {
        return []
      }
      return [[taskId, value as Task13TaskResult]]
    }),
  )
}

function readStore(): BatchHistoryStore {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) {
      return { batches: [] }
    }

    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null || !Array.isArray((parsed as BatchHistoryStore).batches)) {
      return { batches: [] }
    }

    const batches = (parsed as BatchHistoryStore).batches
      .filter(
        (item): item is Task13BatchRecord =>
          typeof item === 'object' &&
          item !== null &&
          typeof item.id === 'string' &&
          typeof item.createdAt === 'string' &&
          Array.isArray(item.tasks),
      )
      .map((batch) => ({
        ...batch,
        tasks: normalizeTasks(batch.tasks),
        results: normalizeResults(batch.results, normalizeTasks(batch.tasks)),
      }))

    return { batches }
  } catch {
    return { batches: [] }
  }
}

function writeStore(store: BatchHistoryStore): void {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(store))
}

function migrateLegacySessionBatch(): Task13BatchRecord | null {
  try {
    const raw = sessionStorage.getItem(LEGACY_SESSION_KEY)
    if (!raw) {
      return null
    }

    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return null
    }

    const tasks = normalizeTasks(parsed)
    sessionStorage.removeItem(LEGACY_SESSION_KEY)
    if (tasks.length === 0) {
      return null
    }

    return {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      tasks,
      results: {},
    }
  } catch {
    return null
  }
}

export function loadBatchHistory(): Task13BatchRecord[] {
  const store = readStore()
  if (store.batches.length > 0) {
    return [...store.batches].sort(
      (left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime(),
    )
  }

  const legacy = migrateLegacySessionBatch()
  if (!legacy) {
    return []
  }

  writeStore({ batches: [legacy] })
  return [legacy]
}

export function appendBatchToHistory(tasks: Task13View[]): Task13BatchRecord {
  const normalized = normalizeTasks(tasks)
  const record: Task13BatchRecord = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    tasks: normalized,
    results: {},
  }

  const store = readStore()
  const batches = [record, ...store.batches.filter((batch) => batch.id !== record.id)].slice(0, MAX_BATCHES)
  writeStore({ batches })

  return record
}

export function removeBatchFromHistory(batchId: string): void {
  const store = readStore()
  writeStore({ batches: store.batches.filter((batch) => batch.id !== batchId) })
}

export function saveTaskResult(taskId: string, result: Omit<Task13TaskResult, 'completedAt'>): void {
  const store = readStore()
  const completedAt = new Date().toISOString()
  const batches = store.batches.map((batch) => {
    if (!batch.tasks.some((task) => task.id === taskId)) {
      return batch
    }
    return {
      ...batch,
      results: {
        ...batch.results,
        [taskId]: { ...result, completedAt },
      },
    }
  })
  writeStore({ batches })
}

/** @deprecated Используйте loadBatchHistory */
export function loadTaskBatch(): Task13View[] {
  return loadBatchHistory()[0]?.tasks ?? []
}

/** @deprecated Используйте appendBatchToHistory */
export function saveTaskBatch(tasks: Task13View[]): void {
  appendBatchToHistory(tasks)
}

export function formatBatchTimestamp(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }

  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
