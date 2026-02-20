# Skill: Automation Flow Designer

This skill provides the complete domain knowledge for generating Debug Framework automation flow files from a set of experiments.

---

## 1. Overview

An automation flow is a directed acyclic graph (DAG) of **nodes**, each representing either a hardware test experiment or a control point (Start/End). The runtime engine (`AutomationFlows.py` → `FlowTestExecutor`) walks this graph, executing experiments and routing to the next node based on pass/fail outcomes.

---

## 2. Output: 4-File Export Set

| File | Description |
|------|-------------|
| `FrameworkAutomationStructure.json` | Graph topology: node IDs, types, connections |
| `FrameworkAutomationFlows.json` | Experiment data: field dicts keyed by experiment name |
| `FrameworkAutomationInit.ini` | Runtime config: connection info + per-experiment INI values |
| `FrameworkAutomationPositions.json` | Canvas layout: x/y positions for visualization |

All 4 files must be written to the same output folder.

---

## 3. File Formats

### 3.1 `FrameworkAutomationStructure.json`

```json
{
  "StartNode": {
    "name": "StartNode",
    "flow": null,
    "outputNodeMap": {
      "0": "Baseline_Mesh"
    },
    "instanceType": "StartNode"
  },
  "Baseline_Mesh": {
    "name": "Baseline_Mesh",
    "flow": "Baseline_Mesh",
    "outputNodeMap": {
      "0": "PPVC_Mesh",
      "1": "EndNode"
    },
    "instanceType": "SingleFailFlowInstance"
  },
  "PPVC_Mesh": {
    "name": "PPVC_Mesh",
    "flow": "PPVC_Mesh",
    "outputNodeMap": {
      "0": "EndNode",
      "1": "Characterization"
    },
    "instanceType": "SingleFailFlowInstance"
  },
  "Characterization": {
    "name": "Characterization",
    "flow": "Characterization",
    "outputNodeMap": {
      "0": "EndNode"
    },
    "instanceType": "CharacterizationFlowInstance"
  },
  "EndNode": {
    "name": "EndNode",
    "flow": null,
    "outputNodeMap": {},
    "instanceType": "EndNode"
  }
}
```

**Rules:**
- `flow` references a key in `FrameworkAutomationFlows.json`. `StartNode` and `EndNode` have `flow: null`.
- `outputNodeMap` keys are port numbers as strings (`"0"`, `"1"`, `"2"`, `"3"`).
- `instanceType` must exactly match one of the class names from Section 5.

### 3.2 `FrameworkAutomationFlows.json`

This is the experiment data file — same format as the ExperimentBuilder export:

```json
{
  "Baseline_Mesh": {
    "Experiment": "Enabled",
    "Test Name": "Baseline Loop Test",
    "Test Mode": "Mesh",
    "Test Type": "Loops",
    ...all experiment fields...
  },
  "PPVC_Mesh": {
    ...
  }
}
```

**Source:** Use the experiment JSON provided by the user as input. Copy experiment entries by name, using the same name keys as in the `flow` field of the structure.

### 3.3 `FrameworkAutomationInit.ini`

```ini
[connection]
COM_Port = 8
IP_Address = 192.168.1.100

[Baseline_Mesh]
TTL_Folder = C:\SystemDebug\AutomationFlow\TTL_DragonFC_FAIL
Pass_String = Test Complete
Fail_String = FAILED

[PPVC_Mesh]
TTL_Folder = C:\SystemDebug\AutomationFlow\TTL_DragonFC_PASS
Pass_String = Test Complete
Fail_String = Test Failed
```

**Rules:**
- `[connection]` section always comes first with `COM_Port` and `IP_Address`.
- Each experiment node gets its own named section. Keys use underscores (not spaces).
- `StartNode` and `EndNode` do not appear in the INI.
- If the user leaves a value blank, write an empty value: `TTL_Folder = `.

### 3.4 `FrameworkAutomationPositions.json`

Auto-computed left-to-right grid layout. Use BFS traversal from `StartNode`:

```json
{
  "StartNode": {"x": 100, "y": 300},
  "Baseline_Mesh": {"x": 350, "y": 300},
  "PPVC_Mesh": {"x": 600, "y": 200},
  "EndNode_pass": {"x": 850, "y": 200},
  "EndNode_fail": {"x": 600, "y": 400}
}
```

**Layout algorithm:**
- Each BFS level is a column separated by 250px horizontally.
- Nodes in the same column are spaced 150px vertically, centered around y=300.
- Multiple `EndNode` instances (if the graph has multiple end points) get unique IDs in positions but share `instanceType: EndNode`.

---

## 4. Port Semantics

| Port | Meaning | Color |
|------|---------|-------|
| `"0"` | Pass / Success | Teal `#1abc9c` |
| `"1"` | Fail / Error | Red `#e74c3c` |
| `"2"` | Alternative path | Orange |
| `"3"` | Critical error / abort | Purple |

When translating a user's natural language description to ports:
- "if it passes" / "on success" / "pass path" → port `"0"`
- "if it fails" / "on failure" / "fail path" → port `"1"`
- "alternative" / "secondary" → port `"2"`
- "on error" / "abort" → port `"3"`

---

## 5. Node Type Reference

### `StartNode`
- **Purpose:** Entry point of the flow. Always present, always first.
- **Experiment:** None (`flow: null`).
- **Outgoing ports:** Only port `"0"` — connects to the first experiment node.
- **When to use:** Always. Every flow has exactly one StartNode.

### `EndNode`
- **Purpose:** Terminal node. Flow execution stops here.
- **Experiment:** None (`flow: null`).
- **Outgoing ports:** None (`outputNodeMap: {}`).
- **When to use:** Always. A flow may have multiple EndNodes (one per terminal branch).

### `SingleFailFlowInstance`
- **Purpose:** Runs the experiment N times (per `Loops`). Routes to FAIL port on the **first** individual failure.
- **Outgoing ports:** `0` = pass, `1` = fail.
- **When to use:** Standard test nodes where you want to catch failures quickly. Most common node type.

### `AllFailFlowInstance`
- **Purpose:** Runs the experiment N times. Only routes to FAIL port if **all** iterations fail.
- **Outgoing ports:** `0` = pass, `1` = fail.
- **When to use:** Stress/characterization where occasional failures are acceptable; you only care about consistent failure.

### `MajorityFailFlowInstance`
- **Purpose:** Runs N times. Routes to FAIL if the majority (>50%) of iterations fail.
- **Outgoing ports:** `0` = pass, `1` = fail.
- **When to use:** Statistical sampling tests where robustness is measured by majority outcome.

### `AdaptiveFlowInstance`
- **Purpose:** Uses historical run data to make intelligent routing decisions. Adjusts behavior based on past results.
- **Outgoing ports:** `0` = pass, `1` = fail, `2` = alternative.
- **When to use:** Long-running characterization campaigns where past data should influence test selection.

### `CharacterizationFlowInstance`
- **Purpose:** Uses previous characterization run data to guide experiment selection. Typically generates data-driven proposals.
- **Outgoing ports:** `0` = pass, `1` = fail.
- **When to use:** When running characterization workflows that build on accumulated test data.

### `DataCollectionFlowInstance`
- **Purpose:** Runs a complete full-data-collection experiment. Collects all available metrics.
- **Outgoing ports:** `0` = complete, `1` = error.
- **When to use:** When you need comprehensive data sweeps rather than pass/fail validation.

### `AnalysisFlowInstance`
- **Purpose:** Generates summary reports and experiment proposals based on collected data.
- **Outgoing ports:** `0` = analysis complete, `1` = error.
- **When to use:** As a terminal or near-terminal node after data collection, to produce actionable output.

---

## 6. Flow Design Patterns

### Pattern A: Simple Linear
```
StartNode → Exp1 → Exp2 → EndNode
```
On any failure in Exp1/Exp2 → directly to EndNode (no recovery path).

### Pattern B: Fault-Tolerant Fallback
```
StartNode → PrimaryExp
  Pass → SecondaryExp → EndNode
  Fail → FallbackExp → EndNode
```
Failures route to a fallback experiment before terminating.

### Pattern C: Characterization Chain
```
StartNode → Baseline
  Pass → PPVC → EndNode
  Fail → Characterization
    Pass → DataCollection → Analysis → EndNode
    Fail → EndNode
```
Failed baseline triggers a deep characterization sub-flow.

### Pattern D: Parallel Test + Merge
```
StartNode → Exp1
  Pass → Exp3 (merge point) → EndNode
  Fail → Exp2 → Exp3 (merge point) → EndNode
```
Both paths eventually converge at a shared node.

---

## 7. Node Naming Convention

- Use descriptive names matching the experiment name when possible: `Baseline_Mesh`, `PPVC_Mesh`.
- Always name control nodes exactly: `StartNode`, `EndNode`.
- If multiple EndNodes exist, use: `EndNode_pass`, `EndNode_fail`, etc. — but in the structure JSON they all have `instanceType: "EndNode"`.

---

## 8. Validation Rules

| Rule | Level |
|------|-------|
| Exactly one node with `instanceType == "StartNode"` | Error |
| All nodes with non-null `flow` must reference a key in the Flows JSON | Error |
| No `flow` references to non-existent experiments | Error |
| All port targets (`outputNodeMap` values) must reference existing node IDs | Error |
| No orphaned nodes (every node reachable from StartNode) | Warning |
| `StartNode` and `EndNode` must have `flow == null` | Error |
| At least one `EndNode` must exist | Error |

---

## 9. Unit Configuration Merge

Before writing the INI file, merge the unit config values into the `[connection]` section:

| Unit Config Field | INI Key |
|------------------|---------|
| `COM Port` | `COM_Port` |
| `IP Address` | `IP_Address` |
| `Visual ID` | `Visual_ID` (optional, document in INI comment) |
| `Bucket` | `Bucket` (optional) |
| `600W Unit` | `600W_Unit` (optional, true/false) |
| `Check Core` | `Check_Core` (optional) |

---

## 10. Import: Load Existing Flow Config

If the user provides an existing flow folder with the 3 required files:
1. Parse `FrameworkAutomationStructure.json` → load current node graph.
2. Parse `FrameworkAutomationFlows.json` → load current experiments.
3. Parse `FrameworkAutomationInit.ini` → load current connection + per-experiment config.
4. Display current graph topology to the user.
5. Allow additions, deletions, or modifications to nodes and connections.
6. Re-validate and re-export all 4 files.
