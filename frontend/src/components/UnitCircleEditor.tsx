import { useMemo, useRef, useState } from 'react'
import type { Task13CircleArc, Task13CircleDiagram, Task13CirclePoint } from '../api/types'
import { clickToAngle, radiansToSympy, snapAngleRadians } from '../utils/circleAngles'

const SIZE = 300
const CENTER = SIZE / 2
const RADIUS = 120

const TICK_LABELS: Array<{ steps: number; label: string }> = [
  { steps: 0, label: '0' },
  { steps: 1, label: 'π/6' },
  { steps: 2, label: 'π/3' },
  { steps: 3, label: 'π/2' },
  { steps: 6, label: 'π' },
]

interface UnitCircleEditorProps {
  value: Task13CircleDiagram
  onChange: (value: Task13CircleDiagram) => void
}

function pointCoords(steps: number): { x: number; y: number } {
  const angle = steps * (Math.PI / 6)
  return {
    x: CENTER + RADIUS * Math.cos(angle),
    y: CENTER - RADIUS * Math.sin(angle),
  }
}

function angleFromSympy(sympy: string): number | null {
  if (sympy === '0') {
    return 0
  }

  const match = sympy.match(/^(-?\d+)\*pi(?:\/(\d+))?$|^(-?)pi(?:\/(\d+))?$/)
  if (!match) {
    return null
  }

  if (match[3] !== undefined || match[1] === undefined) {
    const sign = match[3] === '-' ? -1 : 1
    const den = match[4] ? Number(match[4]) : 1
    return sign * (Math.PI / den)
  }

  const num = Number(match[1])
  const den = match[2] ? Number(match[2]) : 1
  return (num * Math.PI) / den
}

function arcPath(fromSympy: string, toSympy: string): string {
  const from = angleFromSympy(fromSympy)
  const to = angleFromSympy(toSympy)
  if (from === null || to === null) {
    return ''
  }

  const start = {
    x: CENTER + RADIUS * Math.cos(from),
    y: CENTER - RADIUS * Math.sin(from),
  }
  const end = {
    x: CENTER + RADIUS * Math.cos(to),
    y: CENTER - RADIUS * Math.sin(to),
  }

  let delta = to - from
  while (delta <= -Math.PI) {
    delta += 2 * Math.PI
  }
  while (delta > Math.PI) {
    delta -= 2 * Math.PI
  }

  const largeArc = Math.abs(delta) > Math.PI ? 1 : 0
  const sweep = delta >= 0 ? 0 : 1

  return `M ${start.x} ${start.y} A ${RADIUS} ${RADIUS} 0 ${largeArc} ${sweep} ${end.x} ${end.y}`
}

export function UnitCircleEditor({ value, onChange }: UnitCircleEditorProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [mode, setMode] = useState<'point' | 'arc'>('point')
  const [arcFrom, setArcFrom] = useState<string | null>(null)

  const points = value.points ?? []
  const arcs = value.arcs ?? []

  const tickMarks = useMemo(
    () =>
      Array.from({ length: 12 }, (_, index) => {
        const steps = index
        const outer = pointCoords(steps)
        const inner = {
          x: CENTER + (RADIUS - 8) * Math.cos(steps * (Math.PI / 6)),
          y: CENTER - (RADIUS - 8) * Math.sin(steps * (Math.PI / 6)),
        }
        return { steps, outer, inner }
      }),
    [],
  )

  function updateDiagram(nextPoints: Task13CirclePoint[], nextArcs: Task13CircleArc[]) {
    onChange({
      points: nextPoints.length > 0 ? nextPoints : undefined,
      arcs: nextArcs.length > 0 ? nextArcs : undefined,
    })
  }

  function handleCircleClick(event: React.MouseEvent<SVGSVGElement>) {
    const svg = svgRef.current
    if (!svg) {
      return
    }

    const rect = svg.getBoundingClientRect()
    const raw = clickToAngle(event.clientX, event.clientY, rect, CENTER, CENTER)
    const snapped = snapAngleRadians(raw)
    const sympy = radiansToSympy(snapped)

    if (mode === 'arc') {
      if (arcFrom === null) {
        setArcFrom(sympy)
        return
      }

      if (arcFrom !== sympy) {
        updateDiagram(points, [...arcs, { from: arcFrom, to: sympy }])
      }
      setArcFrom(null)
      return
    }

    if (event.shiftKey && points.length > 0) {
      const last = points[points.length - 1]
      if (last && last.angle !== sympy) {
        updateDiagram(points, [...arcs, { from: last.angle, to: sympy }])
      }
      return
    }

    if (points.some((point) => point.angle === sympy)) {
      return
    }

    updateDiagram([...points, { angle: sympy }], arcs)
  }

  function removePoint(angle: string) {
    updateDiagram(
      points.filter((point) => point.angle !== angle),
      arcs,
    )
  }

  function removeArc(index: number) {
    updateDiagram(
      points,
      arcs.filter((_, arcIndex) => arcIndex !== index),
    )
  }

  return (
    <div className="unit-circle">
      <div className="unit-circle__toolbar">
        <button
          type="button"
          className={`btn btn-sm ${mode === 'point' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => {
            setMode('point')
            setArcFrom(null)
          }}
        >
          Точки
        </button>
        <button
          type="button"
          className={`btn btn-sm ${mode === 'arc' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => {
            setMode('arc')
            setArcFrom(null)
          }}
        >
          Дуги
        </button>
        <span className="unit-circle__hint">
          {mode === 'point'
            ? 'Клик — отметить точку. Shift+клик — дуга от последней точки.'
            : arcFrom
              ? `Выберите конец дуги (от ${arcFrom})`
              : 'Клик — начало дуги, второй клик — конец.'}
        </span>
      </div>

      <svg
        ref={svgRef}
        className="unit-circle__svg"
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label="Единичная окружность"
        onClick={handleCircleClick}
      >
        <line x1={0} y1={CENTER} x2={SIZE} y2={CENTER} className="unit-circle__axis" />
        <line x1={CENTER} y1={0} x2={CENTER} y2={SIZE} className="unit-circle__axis" />
        <circle cx={CENTER} cy={CENTER} r={RADIUS} className="unit-circle__ring" />

        {tickMarks.map(({ steps, outer, inner }) => (
          <line
            key={steps}
            x1={inner.x}
            y1={inner.y}
            x2={outer.x}
            y2={outer.y}
            className="unit-circle__tick"
          />
        ))}

        {TICK_LABELS.map(({ steps, label }) => {
          const { x, y } = pointCoords(steps)
          return (
            <text
              key={label}
              x={x + (steps === 0 ? 8 : 4)}
              y={y - 6}
              className="unit-circle__label"
            >
              {label}
            </text>
          )
        })}

        {arcs.map((arc, index) => (
          <path key={`${arc.from}-${arc.to}-${index}`} d={arcPath(arc.from, arc.to)} className="unit-circle__arc" />
        ))}

        {points.map((point) => {
          const angle = angleFromSympy(point.angle)
          if (angle === null) {
            return null
          }
          const x = CENTER + RADIUS * Math.cos(angle)
          const y = CENTER - RADIUS * Math.sin(angle)
          return <circle key={point.angle} cx={x} cy={y} r={5} className="unit-circle__point" />
        })}
      </svg>

      {(points.length > 0 || arcs.length > 0) && (
        <ul className="unit-circle__list">
          {points.map((point) => (
            <li key={point.angle}>
              <span>Точка: {point.angle}</span>
              <button type="button" className="btn btn-sm btn-secondary" onClick={() => removePoint(point.angle)}>
                Удалить
              </button>
            </li>
          ))}
          {arcs.map((arc, index) => (
            <li key={`${arc.from}-${arc.to}-${index}`}>
              <span>
                Дуга: {arc.from} → {arc.to}
              </span>
              <button type="button" className="btn btn-sm btn-secondary" onClick={() => removeArc(index)}>
                Удалить
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
