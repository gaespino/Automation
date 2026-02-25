# THR Tools Debug Workflows

## Overview

Common end-to-end debug workflows using the Portfolio tools.

---

## Workflow 1: MCA Failure Analysis

```mermaid
flowchart TD
    A[Receive failing unit] --> B[Run MCA Decoder\n/thr-tools/mca-decoder]
    B --> C{Identify error bank}
    C -->|MESH| D[Run MCA Report\n/thr-tools/mca-report\nOptions: MESH]
    C -->|CORE| E[Run MCA Report\nOptions: CORE]
    C -->|IO| F[Run MCA Report\nOptions: IO]
    D & E & F --> G[Review report sheet in Excel]
    G --> H{Reproducible?}
    H -->|Yes| I[File DPMB Request\n/thr-tools/dpmb]
    H -->|No| J[Document in Unit Portfolio\n/portfolio]
```

---

## Workflow 2: PTC Experiment Loop Analysis

```mermaid
flowchart TD
    A[PTC experiment complete] --> B[Collect log files]
    B --> C[PTC Loop Parser\n/thr-tools/loop-parser\nbucket + WW + lots]
    C --> D[Parsed Excel output]
    D --> E[Framework Report Builder\n/thr-tools/framework-report]
    E --> F[Multi-sheet analysis report]
    F --> G[Document in Unit Portfolio]
```

---

## Workflow 3: Fuse Configuration

```mermaid
flowchart TD
    A[Select product] --> B[Get compute.csv + io.csv\nfrom configs/fuses/]
    B --> C[Fuse File Generator\n/thr-tools/fuse-generator]
    C --> D[Select fuses + IPs]
    D --> E[.fuse file download]
    E --> F[Flash to unit]
```

---

## Workflow 4: Experiment Design & Automation

```mermaid
flowchart TD
    A[Plan experiment] --> B[Experiment Builder\n/thr-tools/experiment-builder]
    B --> C[experiments.json]
    C --> D[Automation Designer\n/thr-tools/automation-designer]
    D --> E[automation_flow.json]
    E --> F[Execute via DebugFramework]
    F --> G[Framework Report Builder\n/thr-tools/framework-report]
```

---

## Workflow 5: File Consolidation

```mermaid
flowchart TD
    A[Multiple PPV report files] --> B[File Handler\n/thr-tools/file-handler]
    B --> C{Operation}
    C -->|Merge| D[Combined sheets workbook]
    C -->|Append| E[Stacked rows workbook]
    D & E --> F[Upload to Unit Portfolio\n/portfolio]
```

---

## Notes

- All tools use file upload/download — no direct filesystem writes from the browser
- DPMB requests require network access to the DPMB service
- Framework Report accepts missing DataFrames (empty substituted with a warning)
