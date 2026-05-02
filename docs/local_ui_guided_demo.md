# Local UI Guided Demo

## Purpose
The **Guided Demo** panel helps first-time users follow a safe sample workflow in the local beta browser UI.

## Demo steps
1. Load demo template
2. Review preview
3. Check case quality
4. Validate demo
5. Run demo
6. Review interpretation
7. Export demo results

## Expected outcome
Users should be able to complete one full sample pass from template load through result review and export actions.

## Reset behavior
- **Reset Guided Demo** returns the demo to step 1 and clears active state.
- Progress is stored in browser localStorage (`craneRunway.guidedDemoState`).

## Warning
The guided demo uses sample data and is not a design recommendation.

## Code-check limitation
No official CIRSOC/CISC/AISC compliance checks are performed in this guided demo.
