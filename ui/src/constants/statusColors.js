/**
 * Status and Decision Color Mappings
 * Maps all enum values to their corresponding badge CSS classes
 * All status/decision values are uppercase
 */

export const DECISION_VERDICT_COLORS = {
  ACCEPT: {
    class: 'badge-decision-accept',
    color: '#10b981',
    label: 'ACCEPT'
  },
  REVISE: {
    class: 'badge-decision-revise',
    color: '#f59e0b',
    label: 'REVISE'
  },
  CONSTRAIN: {
    class: 'badge-decision-constrain',
    color: '#3b82f6',
    label: 'CONSTRAIN'
  },
  ESCALATE: {
    class: 'badge-decision-escalate',
    color: '#ef4444',
    label: 'ESCALATE'
  }
};

export const PROBE_VERDICT_COLORS = {
  PASS: {
    class: 'badge-probe-pass',
    color: '#10b981',
    label: 'PASS'
  },
  FAIL: {
    class: 'badge-probe-fail',
    color: '#ef4444',
    label: 'FAIL'
  },
  UNCERTAIN: {
    class: 'badge-probe-uncertain',
    color: '#fbbf24',
    label: 'UNCERTAIN'
  },
  ERROR: {
    class: 'badge-probe-error',
    color: '#dc2626',
    label: 'ERROR'
  }
};

export const NODE_STATUS_COLORS = {
  STARTED: {
    class: 'badge-node-started',
    color: '#3b82f6',
    label: 'STARTED'
  },
  COMPLETED: {
    class: 'badge-node-completed',
    color: '#10b981',
    label: 'COMPLETED'
  },
  FAILED: {
    class: 'badge-node-failed',
    color: '#ef4444',
    label: 'FAILED'
  }
};

export const FAILURE_LABEL_COLORS = {
  INSTRUCTION_VIOLATION: {
    class: 'badge-label-instruction-violation',
    color: '#ef4444',
    label: 'INSTRUCTION_VIOLATION'
  },
  UNSUPPORTED_CLAIM: {
    class: 'badge-label-unsupported-claim',
    color: '#f59e0b',
    label: 'UNSUPPORTED_CLAIM'
  },
  INCONSISTENCY: {
    class: 'badge-label-inconsistency',
    color: '#fbbf24',
    label: 'INCONSISTENCY'
  },
  SCHEMA_VIOLATION: {
    class: 'badge-label-schema-violation',
    color: '#6366f1',
    label: 'SCHEMA_VIOLATION'
  },
  POLICY_VIOLATION: {
    class: 'badge-label-policy-violation',
    color: '#dc2626',
    label: 'POLICY_VIOLATION'
  },
  TOOL_MISUSE: {
    class: 'badge-label-tool-misuse',
    color: '#ea580c',
    label: 'TOOL_MISUSE'
  },
  HALLUCINATION: {
    class: 'badge-label-hallucination',
    color: '#ec4899',
    label: 'HALLUCINATION'
  },
  SAFETY_CONCERN: {
    class: 'badge-label-safety-concern',
    color: '#a855f7',
    label: 'SAFETY_CONCERN'
  },
  OTHER: {
    class: 'badge-label-other',
    color: '#6b7280',
    label: 'OTHER'
  }
};

/**
 * Helper function to get color info by verdict type and value
 */
export function getColorInfo(type, value) {
  const colorMaps = {
    decision: DECISION_VERDICT_COLORS,
    probe: PROBE_VERDICT_COLORS,
    node: NODE_STATUS_COLORS,
    label: FAILURE_LABEL_COLORS
  };

  return colorMaps[type]?.[value] || {
    class: '',
    color: '#6b7280',
    label: value
  };
}

/**
 * Helper function to get badge class name
 */
export function getBadgeClass(type, value) {
  return getColorInfo(type, value).class;
}

/**
 * Helper function to get color hex value
 */
export function getColorValue(type, value) {
  return getColorInfo(type, value).color;
}
