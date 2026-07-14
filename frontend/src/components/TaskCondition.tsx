import type { Task13View } from '../api/types'
import { LatexBlock } from './LatexBlock'
import { formatPartA, formatPartB, splitEquationLines } from '../utils/formatTaskPrompts'

interface TaskConditionProps {
  task: Pick<Task13View, 'part_a_prompt' | 'part_b_prompt' | 'interval_display' | 'equation_latex'>
  compact?: boolean
}

export function TaskCondition({ task, compact = false }: TaskConditionProps) {
  const partA = formatPartA(task.part_a_prompt)
  const partB = formatPartB(task.part_b_prompt, task.interval_display)
  const equationLines = partA.equation ? splitEquationLines(partA.equation) : []

  return (
    <div className={compact ? 'task-condition task-condition--compact' : 'task-condition'}>
      <div className="task-prompt">
        <span className="task-prompt__label" aria-hidden="true">
          а)
        </span>
        <div className="task-prompt__content">
          <p className="task-prompt__text">{partA.lead}</p>
          {task.equation_latex ? (
            <div className="task-prompt__equation-math">
              <LatexBlock
                latex={task.equation_latex}
                className={compact ? 'latex-block--compact' : 'latex-block--equation'}
              />
            </div>
          ) : (
            equationLines.length > 0 && (
              <div className="task-prompt__equation-lines" aria-label={partA.equation}>
                {equationLines.map((line, index) => (
                  <span
                    key={`${line}-${index}`}
                    className={
                      line === '= 0'
                        ? 'task-prompt__equation-line task-prompt__equation-line--equals'
                        : 'task-prompt__equation-line'
                    }
                  >
                    {line}
                  </span>
                ))}
              </div>
            )
          )}
        </div>
      </div>

      <div className="task-prompt">
        <span className="task-prompt__label" aria-hidden="true">
          б)
        </span>
        <div className="task-prompt__content">
          <p className="task-prompt__text">{partB.lead}</p>
          {partB.interval && <p className="task-prompt__interval">{partB.interval}</p>}
        </div>
      </div>
    </div>
  )
}
