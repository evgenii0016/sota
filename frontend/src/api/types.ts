/** Типы API задания 13 — зеркало app/task13/models.py и app/models.py */

export type CommentSection =
  | 'одз'
  | 'преобразование'
  | 'серии'
  | 'отбор'
  | 'ответ_б'
  | 'общее'

export type Task13Score = 0 | 1 | 2

export interface Task13View {
  id: string
  task_type: 'task_13'
  statement: string
  part_a_prompt: string
  part_b_prompt: string
  interval_display?: string | null
  equation_latex?: string | null
}

export interface Task13BatchResponse {
  tasks: Task13View[]
}

export interface Task13CirclePoint {
  angle: string
}

export interface Task13CircleArc {
  from: string
  to: string
}

export interface Task13CircleDiagram {
  points?: Task13CirclePoint[]
  arcs?: Task13CircleArc[]
}

export interface Task13GradeRequest {
  solution_part_a: string
  answer_part_b: string
  circle_diagram?: Task13CircleDiagram | null
}

export interface Task13Comment {
  section: CommentSection
  ok: boolean
  text?: string | null
}

export interface Task13GradeResponse {
  score: Task13Score
  part_a_correct: boolean
  part_b_correct: boolean
  justified: boolean
  comments: Task13Comment[]
  justified_part_a?: boolean | null
  justified_part_b?: boolean | null
  method_errors?: string[]
  attempt_id?: string | null
}

export interface Task13DraftSolution {
  part_a?: string
  part_b?: string
}

export interface Task13AssistantMessage {
  role: 'user' | 'assistant'
  text: string
}

export interface Task13AssistantRequest {
  message: string
  draft_solution?: Task13DraftSolution
  history?: Task13AssistantMessage[]
}

export interface Task13AssistantResponse {
  reply: string
  uses_left: number
}

/** GET /attempts/{id} — расширенный GradeAttemptView для task_13 */
export interface Task13AttemptView {
  id: string
  task_id: string
  student_answer: string
  is_correct: boolean
  feedback: string
  llm_provider?: string | null
  duration_ms?: number | null
  created_at?: string | null
  score?: Task13Score | null
  solution_part_a?: string | null
  answer_part_b?: string | null
  comments?: Task13Comment[] | null
  part_a_correct?: boolean | null
  part_b_correct?: boolean | null
  justified?: boolean | null
  justified_part_a?: boolean | null
  justified_part_b?: boolean | null
  method_errors?: string[] | null
}

export function attemptToGrade(attempt: Task13AttemptView): Task13GradeResponse | null {
  if (attempt.score === null || attempt.score === undefined) {
    return null
  }
  if (attempt.part_a_correct == null || attempt.part_b_correct == null || attempt.justified == null) {
    return null
  }

  return {
    score: attempt.score,
    part_a_correct: attempt.part_a_correct,
    part_b_correct: attempt.part_b_correct,
    justified: attempt.justified,
    comments: attempt.comments ?? [],
    justified_part_a: attempt.justified_part_a,
    justified_part_b: attempt.justified_part_b,
    method_errors: attempt.method_errors ?? [],
    attempt_id: attempt.id,
  }
}

export interface ApiErrorBody {
  code: string
  message: string
  field?: string | null
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly field?: string | null

  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code
    this.field = body.field
  }
}
