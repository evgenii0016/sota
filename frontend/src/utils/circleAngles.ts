function gcd(a: number, b: number): number {
  let x = Math.abs(a)
  let y = Math.abs(b)
  while (y !== 0) {
    ;[x, y] = [y, x % y]
  }
  return x
}

/** Угол в радианах → ближайшее k·π/6. */
export function snapAngleRadians(radians: number): number {
  const step = Math.PI / 6
  return Math.round(radians / step) * step
}

/** k·π/6 → символьная строка для SymPy (pi/6, -pi/2, …). */
export function stepsToSympy(steps: number): string {
  if (steps === 0) {
    return '0'
  }

  const absSteps = Math.abs(steps)
  const g = gcd(absSteps, 6)
  const num = absSteps / g
  const den = 6 / g
  const sign = steps < 0 ? '-' : ''

  if (den === 1) {
    if (num === 1) {
      return `${sign}pi`
    }
    return `${sign}${num}*pi`
  }

  if (num === 1) {
    return `${sign}pi/${den}`
  }

  return `${sign}${num}*pi/${den}`
}

export function radiansToSympy(radians: number): string {
  const snapped = snapAngleRadians(radians)
  const steps = Math.round(snapped / (Math.PI / 6))
  return stepsToSympy(steps)
}

/** Клик по SVG → угол от центра (радианы, 0 справа, против часовой). */
export function clickToAngle(
  clientX: number,
  clientY: number,
  rect: DOMRect,
  centerX: number,
  centerY: number,
): number {
  const x = clientX - rect.left - centerX
  const y = centerY - (clientY - rect.top)
  return Math.atan2(y, x)
}
