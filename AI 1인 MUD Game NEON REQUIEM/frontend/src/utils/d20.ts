export type RollMode = 'normal' | 'adv' | 'dis';

export type D20Roll = {
  mode: RollMode;
  rolls: [number] | [number, number];
  chosen: number;
};

export type D20HitResolution = {
  roll: D20Roll;
  attackBonus: number;
  targetAC: number;
  total: number;
  hit: boolean;
  crit: boolean;
  fumble: boolean;
};

export function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

export function clampInt(v: number, min: number, max: number): number {
  const n = Math.trunc(v);
  if (n < min) return min;
  if (n > max) return max;
  return n;
}

function rollOnceD20(): number {
  return 1 + Math.floor(Math.random() * 20);
}

export function rollD20(mode: RollMode = 'normal'): D20Roll {
  if (mode === 'adv' || mode === 'dis') {
    const a = rollOnceD20();
    const b = rollOnceD20();
    const chosen = mode === 'adv' ? Math.max(a, b) : Math.min(a, b);
    return { mode, rolls: [a, b], chosen };
  }
  const a = rollOnceD20();
  return { mode, rolls: [a], chosen: a };
}

export function resolveD20Hit(args: {
  attackBonus: number;
  targetAC: number;
  mode?: RollMode;
}): D20HitResolution {
  const attackBonus = Math.trunc(args.attackBonus || 0);
  const targetAC = Math.trunc(args.targetAC || 0);
  const roll = rollD20(args.mode ?? 'normal');
  const chosen = roll.chosen;
  const crit = chosen === 20;
  const fumble = chosen === 1;
  const total = chosen + attackBonus;
  const hit = crit || (!fumble && total >= targetAC);
  return { roll, attackBonus, targetAC, total, hit, crit, fumble };
}

/**
 * 확률(p) → 단일 d20에서 필요한 최소 눈(DC)로 변환.
 * - 자연 1은 무조건 실패, 자연 20은 무조건 성공(치명타)으로 취급하므로,
 *   DC는 2~20 범위로 클램프한다.
 *
 * 단일 d20 기준: 성공 확률 p ≈ (21 - DC) / 20
 * => DC ≈ 21 - 20p
 */
export function chanceToD20Dc(successChance: number): number {
  const p = clamp01(successChance);
  const dc = Math.ceil(21 - 20 * p);
  return clampInt(dc, 2, 20);
}

export function resolveD20Check(args: {
  dc: number;
  mode?: RollMode;
}): {
  roll: D20Roll;
  dc: number;
  hit: boolean;
  crit: boolean;
  fumble: boolean;
} {
  const dc = clampInt(args.dc, 2, 20);
  const roll = rollD20(args.mode ?? 'normal');
  const chosen = roll.chosen;
  const crit = chosen === 20;
  const fumble = chosen === 1;
  const hit = crit || (!fumble && chosen >= dc);
  return { roll, dc, hit, crit, fumble };
}

export function formatD20Check(r: { roll: D20Roll; dc: number; hit: boolean; crit: boolean; fumble: boolean }): string {
  const modeTag = r.roll.mode === 'normal' ? '' : `(${r.roll.mode})`;
  const rollsStr =
    r.roll.rolls.length === 2 ? `[${r.roll.rolls[0]},${r.roll.rolls[1]}]→${r.roll.chosen}` : `${r.roll.chosen}`;
  const resultTag = r.crit ? 'CRIT' : r.fumble ? 'FUMBLE' : r.hit ? 'HIT' : 'MISS';
  return `🎲 d20${modeTag}: ${rollsStr} vs DC ${r.dc} ⇒ ${resultTag}`;
}

export function formatD20Resolution(r: D20HitResolution): string {
  const modeTag = r.roll.mode === 'normal' ? '' : `(${r.roll.mode})`;
  const rollsStr = r.roll.rolls.length === 2 ? `[${r.roll.rolls[0]},${r.roll.rolls[1]}]→${r.roll.chosen}` : `${r.roll.chosen}`;
  const resultTag = r.crit ? 'CRIT' : r.fumble ? 'FUMBLE' : r.hit ? 'HIT' : 'MISS';
  const sign = r.attackBonus >= 0 ? '+' : '-';
  const ab = Math.abs(r.attackBonus);
  return `🎲 d20${modeTag}: ${rollsStr} ${sign} ${ab} = ${r.total} vs AC ${r.targetAC} ⇒ ${resultTag}`;
}

