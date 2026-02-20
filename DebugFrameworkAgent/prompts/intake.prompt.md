# Intake Questionnaire Prompt

Use this prompt to open a new session and collect the required information
before generating any experiments or flows.

---

## Instructions for Agent

Ask the user these five questions. Accept partial answers and infer where safe.

---

## Questions

**Q1 — Product**
Which product are you targeting?
- [ ] GNR
- [ ] CWF
- [ ] DMR

**Q2 — Objective**
What are you trying to test or validate? (free text)
> Example: "Stability under elevated mesh voltage", "Boot sequence after fuse programming"

**Q3 — Content Type**
Which execution content will the test use?
- [ ] Dragon (ULX binary + mesh/slice stress)
- [ ] Linux (Yocto/kernel stress)
- [ ] PYSVConsole (Python test scripts)
- [ ] FuseWizard (fuse read/write operations)
- [ ] None / Boot only

**Q4 — Test Structure**
What test execution pattern?
- [ ] Loops (repeat N times)
- [ ] Sweep (range over voltage or frequency)
- [ ] Shmoo (2D sweep from ShmooFile)
- [ ] Stability (long-duration loops, no sweep)

**Q5 — Scope**
How many experiments are you building today?
- [ ] One experiment
- [ ] Multiple independent experiments
- [ ] A multi-node automation flow

---

## Output Format

Record the collected answers as:

```
product:    {GNR|CWF|DMR}
objective:  {text}
content:    {Dragon|Linux|PYSVConsole|FuseWizard|None}
test_type:  {Loops|Sweep|Shmoo|Stability}
scope:      {single|multi|flow}
```

Then proceed to the Orchestrator agent with this context.
