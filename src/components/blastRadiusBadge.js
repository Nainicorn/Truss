/**
 * Truss — Blast Radius Badge
 * 6-segment fill bar: none=0, low=1, medium=3, high=5, critical=6.
 */

const LEVEL_FILLS = {
  none: 0,
  low: 1,
  medium: 3,
  high: 5,
  critical: 6,
};

export function createBlastBadge(level) {
  const normalized = (level || 'none').toLowerCase();
  const fillCount = LEVEL_FILLS[normalized] ?? 0;

  const badge = document.createElement('span');
  badge.className = 'blast-badge';
  badge.setAttribute('data-level', normalized);

  const segments = document.createElement('span');
  segments.className = 'blast-segments';

  for (let i = 0; i < 6; i++) {
    const seg = document.createElement('span');
    seg.className = `blast-segment${i < fillCount ? ' filled' : ''}`;
    segments.appendChild(seg);
  }

  const label = document.createElement('span');
  label.className = 'blast-label';
  label.textContent = normalized.toUpperCase();

  badge.appendChild(segments);
  badge.appendChild(label);

  return badge;
}
