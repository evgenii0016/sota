import type { Task13Score } from '../api/types'

export const SCORE_CRITERIA: Record<Task13Score, string> = {
  2: 'Обоснованно получены верные ответы в обоих пунктах а и б.',
  1: 'Обоснованно получен верный ответ в пункте а или в пункте б.',
  0: 'Решение не соответствует критериям на 1 или 2 балла.',
}

export function scoreLabel(score: Task13Score): string {
  if (score === 1) {
    return '1 балл'
  }
  return `${score} ${score === 0 ? 'баллов' : 'балла'}`
}
