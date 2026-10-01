# PRD: Early-game planner

## Problem Statement

I play Travian Legends. In the early game, I make a long chain of small decisions: which resource field or building to upgrade next, when to construct a Warehouse, when to train settlers, and when to collect task rewards and hero resources. A wrong order wastes hours of production and delays the second village.

Community guides give a generic plan. They do not use my tribe, my field layout, my server speed, or the real state of my village. I cannot test an idea against the real game rules without playing for days.

## Solution

A local web app that simulates the economy of one village with the real game rules and searches for the fastest plan to a goal.

- The app reads the game rules from the Travian Legends knowledge base into a stored game data snapshot.
- The optimizer starts from a fresh account (tribe, field layout, server speed) and finds the fastest plan to a goal. The default goal is the second village: three settlers are trained, and the account has the culture points for a second village. I can also set my own goal.
- The advisor reads my real village from pasted game pages, runs the optimizer from that state, and shows the next actions.
- The plan page shows the milestones, an action timeline with in-game start and finish times, and a resource chart.
- Adventures are random. A plan uses expected values. When the real outcome differs, I paste my pages again and the advisor re-plans.

## User Stories

### Game data

1. As a player, I want to refresh the game rules from the knowledge base with one button, so that my plans use the current rules.
2. As a player, I want to see the progress of a refresh, so that I know the app works during the minutes that a refresh takes.
3. As a player, I want each refresh stored as a separate game data snapshot, so that an old plan stays reproducible after the rules change.
4. As a player, I want a list of snapshots with date and counts of buildings, units, and tasks, so that I can see if a refresh is complete.
5. As a player, I want to see the table of one building in a snapshot, so that I can compare numbers with the game.
6. As a player, I want a refresh that fails on one page to report which page failed, so that I can fix the scraper or try again.
7. As a player, I want a failed refresh to store no partial snapshot, so that no plan uses incomplete rules.
8. As a player, I want the latest complete snapshot selected by default, so that I do not have to choose one each time.

### Fresh-account plans (optimizer)

9. As a player, I want to choose my tribe from all Legends tribes, so that the plan uses the buildings, settlers, and queue rules of my tribe.
10. As a player, I want to choose my field layout, for example 4-4-4-6 or 3-3-3-9, so that the plan matches my village.
11. As a player, I want to choose the server speed, so that times and production match my game world.
12. As a player, I want the second village as the default goal, so that I can run the most common plan with no extra input.
13. As a player, I want to set my own goal with target levels for resource fields and buildings and a culture point threshold, so that I can plan other milestones.
14. As a player, I want the optimizer to run in the background with a progress bar, so that the page stays usable during a long run.
15. As a player, I want the optimizer to put correctness before speed, so that I can trust the times in the plan.
16. As a player, I want the same inputs to give the same plan, so that I can compare runs.
17. As a player, I want the plan to be at least as fast as the best baseline policy, so that I know that the search adds value.
18. As a player, I want to see the time of the best baseline policy next to the plan time, so that I see the gain.

### Simulated rules

19. As a player, I want production to follow the level of each resource field and the production buildings, so that resource stocks are correct.
20. As a player, I want resource stocks to stop at the Warehouse and Granary caps, so that the plan shows waste from full storage.
21. As a player, I want construct and upgrade costs and times from the snapshot, so that each action has the real price.
22. As a player, I want the Main Building to reduce build times, so that the plan values a Main Building upgrade correctly.
23. As a player, I want building prerequisites enforced, so that the plan never constructs a building that the game does not allow yet.
24. As a player, I want the build queue rules of my tribe, for example the Roman parallel queue for fields and buildings, so that the plan uses every queue slot.
25. As a player, I want population and crop consumption simulated, so that the plan never starves the village.
26. As a player, I want culture points to accumulate from buildings over time, so that the plan knows when the second village is allowed.
27. As a player, I want settler training in the Residence, the Palace, or the tribe's equivalent building, so that the second-village goal is complete.
28. As a player, I want task rewards as actions that the plan collects when the condition is met, so that the plan uses free resources.
29. As a player, I want hero resource production simulated, so that the plan includes the hero output.
30. As a player, I want adventures as actions with expected duration and reward, so that the plan includes them without random results.

### Plan view

31. As a player, I want milestones at the top of the plan, for example time to goal and the first Warehouse level, so that I see the result at once.
32. As a player, I want an action timeline with in-game start and finish times, so that I can follow the plan by hand in the game.
33. As a player, I want a resource chart with stock, storage cap, and production for each resource over time, so that I see bottlenecks.
34. As a player, I want a culture point curve, so that I see when the second village becomes possible.
35. As a player, I want a list of my saved plans with inputs and time to goal, so that I can go back to an earlier plan.
36. As a player, I want to see which snapshot a plan used, so that I know which rules were in force.

### Advisor

37. As a player, I want to paste the content of my real game pages, so that the advisor starts from my real village without a login to Travian.
38. As a player, I want the advisor to show what it read from my pages, so that I can check the parsed state before I trust the advice.
39. As a player, I want a clear message when a page is missing or cannot be parsed, so that I know what to paste again.
40. As a player, I want the next actions highlighted at the top of an advisor plan, so that I know what to do now.
41. As a player, I want to paste my pages again after an adventure or a delay, so that the advisor re-plans from the real outcome.

### Later phase

42. As a player, I want a policy interface that a learned agent can implement later, so that a reinforcement-learning agent can plug in without engine changes.

## Implementation Decisions

### Stack and structure

- The app uses this stack: Python 3.14, FastAPI on Granian, Wireup, async SQLAlchemy, Alembic, Postgres in Docker, React 19, TanStack Query, Tailwind, shadcn, bun, and a TypeScript client generated from OpenAPI.
- The backend follows the layered-architecture skill: a core of supplier-neutral machinery plus vertical slices. The vocabulary follows `CONTEXT.md`.
- The app runs locally for one user. It has no login.

### Slices

- **health**: liveness.
- **game_data**: refresh and read game data snapshots.
  - A knowledge base port returns domain records for buildings, units, culture point thresholds, tasks, and hero rules. The scraper adapter is the only code that knows the browser automation library.
  - A snapshot repository port stores and reads snapshots.
  - A refresh runs as a background job with progress. A refresh either stores a complete snapshot or stores nothing.
- **planning**: create, run, store, and read plans. The advisor belongs to this slice.
  - A plan repository port stores plans with inputs, snapshot reference, timeline, and series.
  - A game rules repository port reads a stored snapshot and returns the engine rules. The slices share data through the database.
  - A village page port parses pasted game pages into a game state.
  - An orchestrator runs the fixed sequence: build the start state, run the optimizer, store the plan.

### Simulation engine (deep module)

- The engine lives in the private folder of the planning slice. It is pure and synchronous, with no I/O and no framework imports.
- The interface is small and stable:
  - Game rules: built once from a snapshot. Every rule value comes from the snapshot.
  - Game state: immutable, holding time, resources, levels, queues, culture points, population, hero, and tasks.
  - Valid actions: from a game state and the rules.
  - Apply action: from a game state, an action, and the rules, to the next game state.
  - Advance: to the next event (a queue finish, a resource threshold, an adventure return).
  - Goal: a predicate on a game state. The second village and a custom goal are two goal types.
  - Policy: from a game state and the rules, to the next action.
  - Optimizer: from a start state, a goal, and the rules, to a plan.
- The optimizer re-simulates its final plan with the engine before it returns the plan. A plan that fails the re-simulation is an error.
- Random events use expected values from the snapshot.

### API contracts

- Game data: start a refresh, read refresh progress over WebSocket, list snapshots, read one snapshot.
- Planning: create a plan from a fresh account or from pasted pages, read run progress over WebSocket, read a plan, list plans.
- Every known error is an `AppError` subclass and reaches the client as a problem document.

### Persistence

- A snapshot is one row with metadata plus structured content for buildings, units, thresholds, tasks, and hero rules.
- A plan is one row with inputs, the snapshot reference, status, the action timeline, milestones, and resource series.
- Alembic autogenerate creates every migration.

## Testing Decisions

- Tests are few and well chosen. Each test checks external behavior through a public interface.
- Before each stage, a separate agent with no implementation context writes the conceptual tests for that stage in plain language. The player reviews them before implementation starts.
- Where a stage has concrete numbers, the conceptual tests include hand-computed expected values from the snapshot. Example: apply 15 fixed actions to a fresh account and check the end-state population, the culture point production, and the elapsed time.
- At the end of each stage, the conceptual tests become code, run, and pass. When a test fails, the player decides whether the code or the expectation is wrong.
- Modules with tests:
  - Simulation engine: knowledge-base unit tests for each rule, plus scenario tests.
  - Scraper and page parsers: stored HTML fixtures in, domain records out.
  - Repository adapters: integration tests against Postgres in Docker.
  - Controllers: HTTP tests for status codes and problem documents.
- The backend tests use pytest and pytest-asyncio. Each test file `*_test.py` sits next to the code that it tests. The `integration` marker selects the tests that need Postgres.

## Out of Scope

- More than one village after the second village is founded.
- Combat, raids, troop training other than settlers, and oases.
- Gold features: Plus account, production bonuses bought with gold, instant finish, and the NPC merchant.
- Travel time and settling time for the second village.
- A login to a Travian account, and any automated action in the real game.
- A learned agent. Only the policy interface is in scope.
- Several users, accounts, and hosting.

## Further Notes

- Risk: knowledge-base unit tests prove each rule alone. They do not prove how the rules combine over time, for example rounding, storage overflow, and queue timing. Scenario tests and advisor re-plans from real pages reduce this risk.
- Risk: the knowledge base can lack task rewards, culture point thresholds, or hero rules. Stage 3 starts with a survey of the knowledge base. A gap goes back to the player for a decision.
- Risk: the advisor needs real game page samples. The player supplies them before stage 8.
- The scraper takes minutes for a full pass. That is acceptable, because a refresh is rare and runs in the background.
