const DECIMAL_APPROX_RE = /≈|~\s*\d|(?<![\w.])(?:\d+\.\d+|\.\d+)(?![\w.])/

export interface FieldValidationError {
  field: 'solution_part_a' | 'answer_part_b'
  message: string
}

export function validateTask13Submission(
  solutionPartA: string,
  answerPartB: string,
): FieldValidationError[] {
  const errors: FieldValidationError[] = []
  const partA = solutionPartA.trim()
  const partB = answerPartB.trim()

  if (!partA) {
    errors.push({ field: 'solution_part_a', message: 'Заполните решение пункта а.' })
  } else if (partA.length > 16000) {
    errors.push({
      field: 'solution_part_a',
      message: 'Решение пункта а слишком длинное (максимум 16000 символов).',
    })
  } else if (DECIMAL_APPROX_RE.test(partA)) {
    errors.push({
      field: 'solution_part_a',
      message: 'Нужно точное значение, без десятичных приближений (≈, 8.377).',
    })
  }

  if (partB.length > 512) {
    errors.push({
      field: 'answer_part_b',
      message: 'Ответ пункта б слишком длинный (максимум 512 символов).',
    })
  } else if (DECIMAL_APPROX_RE.test(partB)) {
    errors.push({
      field: 'answer_part_b',
      message: 'Нужно точное значение, без десятичных приближений (≈, 8.377).',
    })
  }

  return errors
}
