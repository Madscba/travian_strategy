# Plan: Early-game planner

This plan implements the PRD in `documentation/prds/2026-10-01-early-game-planner.md`. The vocabulary follows `CONTEXT.md`.

## How to run this plan

- Run the stages in order. A stage starts only after the gate of the previous stage passes.
- Run each step with the `baby-steps` skill: propose the step, agree, implement only that step, review, accept.
- Place backend code with the `layered-architecture` skill. Update `CONTEXT.md` with the `domain-modeling` skill when a term changes.

### Test workflow for each stage

1. **Conceptual tests.** Before the first step of a stage, a separate agent writes the conceptual tests for the stage. The agent gets the PRD, `CONTEXT.md`, this plan, and the stage goal. It gets no implementation context.
   - The tests are few and well chosen, in plain language (given, when, then).
   - Where the stage has concrete numbers, the agent computes the expected values by hand from the stored test snapshot and shows the calculation.
   - The agent writes them to `documentation/plans/tests/stage-<n>-conceptual-tests.md`.
   - The player reviews and accepts the list.
2. **Implementation.** The steps of the stage, in baby steps. Each step has its own check.
3. **Gate.** The conceptual tests become code and run. Every test passes, and the gate check of the stage passes. When a test fails, the player decides whether the code or the expectation is wrong.

## Stage 0: Clean slate

Goal: the repository holds only the planning documents.

| Step | Change | Check |
|---|---|---|
| 0.1 | Tag the current `main` as `legacy`. Push the tag. | `git tag` lists `legacy`. The remote has the tag. |
| 0.2 | Delete every file except `CONTEXT.md`, `documentation/`, and `.git`. | `git ls-files` lists only `CONTEXT.md` and `documentation/`. |

Gate: the player reviews the tree. Stage 0 has no conceptual tests.

## Stage 1: Codebase setup

Goal: the app runs in this repository with the names of the layered-architecture skill.

| Step | Change | Check |
|---|---|---|
| 1.1 | Set up the backend and the frontend. Keep `.devcontainer/`. | `bun run dev` starts both servers. |
| 1.2 | Replace `.azuredevops/ci.yml` with a GitHub Actions workflow that runs the same backend and frontend jobs. | The workflow is green on a pull request. |
| 1.3 | Rename the health slice to the skill names: `router.py` to `controller.py` (exports `controller`), `service.py` to `services.py`. Set the app title and the home page text to the product name. | `bun run dev` starts both servers. The browser at `http://localhost:3000` shows the health status "ok". |
| 1.4 | The repository uses the global skills `layered-architecture`, `domain-modeling`, `baby-steps`, and `write-prd`. Add the `### Structure` terms to `CONTEXT.md`. | The skills load in a new Claude Code session. |
| 1.5 | Write `README.md` and `CLAUDE.md` for the new layout and commands. | `bun run check` passes. The player reads both files. |

Gate: conceptual tests (setup scope: dev start, health response, checks), then `bun run dev`, `bun run check`, and CI are green.

## Stage 2: Infrastructure

Goal: the remaining core machinery exists and works end to end.

| Step | Change | Check |
|---|---|---|
| 2.1 | Add pytest and pytest-asyncio, the `*_test.py` convention, and the `integration` marker. Add a controller test for health. | `uv run pytest` passes. |
| 2.2 | Add `core/errors.py` (`AppError`, `ProblemDetail`) and the error handlers in `main.py`. | A test route that raises an `AppError` subclass returns a problem document with the right status and `type`. A validation error returns `validation_error`. |
| 2.3 | Add Wireup. Give the health slice a `dependencies.py`. Set up the container in `main.py`. | The health controller test passes with the injected service. |
| 2.4 | Add Postgres in Docker, `core/db/` (engine, base, session, dependencies), and Alembic in `backend/migrations/`. Make health report the database status. | `bun run migrate` succeeds on an empty database. An integration test reads the database status through health. The browser shows "database ok". |
| 2.5 | Add a core background-job capability: CPU-bound work runs in a worker process and reports progress. Add the core WebSocket transport for progress events. | An integration test starts a test job and receives ordered progress events and a final result over WebSocket. |
| 2.6 | Frontend foundation: run shadcn init, add a router (recommendation: TanStack Router), a layout with navigation, and four empty pages: Game data, New plan, Plan, Plans. | The browser shows the navigation and the four pages. `bun run check` passes. |
| 2.7 | Extend CI: pytest with a Postgres service, and a check that the generated TypeScript client matches the OpenAPI schema. | CI is green on a pull request. |

Gate: conceptual tests (problem document shape, database round trip, job progress over WebSocket, page navigation), then all checks green.

## Stage 3: Game data from the knowledge base

Goal: a refresh from the knowledge base stores a complete game data snapshot for all Legends tribes.

| Step | Change | Check |
|---|---|---|
| 3.1 | Survey the knowledge base (no product code). List the source of each rule that the engine needs: buildings, prerequisites, units and settlers per tribe, culture point thresholds per server speed, tasks and rewards, hero production and adventures, tribe queue rules, and the fresh-account start state. Decide on browser automation or plain HTTP for each page type. Write the result to `documentation/plans/2026-10-01-knowledge-base-survey.md`. | The player reviews the coverage table and decides every gap. |
| 3.2 | Conceptual tests for stage 3 (separate agent). | The player accepts the list. |
| 3.3 | Define the domain records of the snapshot content in the `game_data` slice. | `ty check` passes. |
| 3.4 | Add the knowledge base port and the scraper adapter for buildings. Store HTML fixtures. | Fixture tests pass, for example the Warehouse level 7 cost and build time. |
| 3.5 | Extend the adapter to units and settlers, culture point thresholds, tasks, hero rules, and tribe rules, as the survey decided. One entity type per baby step. | Fixture tests pass for each entity type. |
| 3.6 | Add the snapshot persistence model, the Alembic migration, and the snapshot repository adapter. | An integration test inserts and reads a snapshot. |
| 3.7 | Add the refresh service as a background job, and the controller: start refresh, progress over WebSocket, list snapshots, read one snapshot. A failed refresh stores nothing and names the failed page. | Controller tests pass, including the failure path with no stored snapshot. |
| 3.8 | Build the Game data page: snapshot list with counts, refresh button with progress, building table. | In the browser, a live refresh shows progress and adds a snapshot with all tribes. The Warehouse table matches the game. |
| 3.9 | Export one live snapshot as the stored test snapshot for the engine tests. | The file loads into the snapshot records. |

Gate: conceptual tests pass, and a live refresh succeeds.

## Stage 4: Simulation engine

Goal: a pure engine in `features/planning/private/engine/` simulates one village for every Legends tribe. Every rule value comes from the snapshot. All engine tests use the stored test snapshot.

| Step | Change | Check |
|---|---|---|
| 4.1 | Conceptual tests for stage 4 (separate agent). They include scenario tests with hand-computed end states, for example 15 fixed actions from a fresh account with the end-state population, culture point production, and elapsed time. | The player accepts the list and the calculations. |
| 4.2 | Game rules: build them from snapshot content. | Rule values equal snapshot values, for example the Warehouse level 7 cost. |
| 4.3 | Game state and the fresh-account start state from tribe, field layout, and server speed. | The start state matches the fresh-account facts of the survey for two field layouts. |
| 4.4 | Time and production: production per resource field level, production buildings, server speed, storage caps. | One hour at known levels gives the exact stock. Stock stops at the cap. |
| 4.5 | Upgrade and construct: valid actions, costs, build times with the Main Building reduction and server speed, prerequisites, maximum levels. | Knowledge-base unit tests for cost, time, and prerequisite cases. |
| 4.6 | Build queues and tribe rules, for example the Roman parallel queue. | One test for each tribe-specific rule. |
| 4.7 | Population, crop consumption, and culture points. | Hand-computed values after a fixed sequence of actions. |
| 4.8 | Settlers: training building, cost, time, and the condition for three settlers. | Knowledge-base unit tests for each tribe's training building. |
| 4.9 | Tasks: conditions and reward collection actions. | A task reward adds the exact resources from the snapshot. |
| 4.10 | Hero: resource production and adventures with expected values. | Hand-computed hero output and adventure result. |
| 4.11 | Goals (second village, custom goal), advance to the next event, and plan replay: a fixed list of actions gives a timeline. | The 15-action scenario test passes. |

Gate: all conceptual tests of stage 4 pass, including the scenario tests.

## Stage 5: Policies and optimizer

Goal: the optimizer finds a plan to the second village that is as fast as or faster than the best baseline policy.

| Step | Change | Check |
|---|---|---|
| 5.1 | Conceptual tests for stage 5 (separate agent). | The player accepts the list. |
| 5.2 | Policy interface and two baseline policies (for example cheapest upgrade first, and highest production gain per resource). Run a policy to a goal to get a plan. | Each baseline policy reaches the second village for every tribe. The times are reported. |
| 5.3 | Optimizer search with a fixed tie-break. It re-simulates the final plan before it returns. | For every tribe, the optimizer time is less than or equal to the best baseline time. Two runs give the same plan. The runtime is reported. |
| 5.4 | Speed pass, only if the runtime is too long for the player. | The stage 4 and 5 tests still pass. The runtime is reported before and after. |

Gate: conceptual tests pass.

## Stage 6: Planning API

Goal: a plan runs and is stored through the API.

| Step | Change | Check |
|---|---|---|
| 6.1 | Conceptual tests for stage 6 (separate agent). | The player accepts the list. |
| 6.2 | Plan persistence model, migration, and plan repository adapter. | An integration test inserts and reads a plan. |
| 6.3 | Game rules repository adapter: read a stored snapshot into game rules. | An integration test reads the test snapshot and compares rule values. |
| 6.4 | Optimizer service as a background job with progress, the create-plan orchestrator, and the controller: create a plan from a fresh account, progress over WebSocket, read a plan, list plans. | Controller tests pass, including an unknown snapshot and an invalid goal. |

Gate: conceptual tests pass. A run of the default goal through the API stores a plan.

## Stage 7: Planning UI

Goal: the player creates and reads plans in the browser.

| Step | Change | Check |
|---|---|---|
| 7.1 | New plan page: tribe, field layout, server speed, goal (second village or custom), snapshot, run with progress. | In the browser, a run starts, shows progress, and opens the plan. |
| 7.2 | Plan page: milestones with the baseline time, and the action timeline with in-game start and finish times. | In the browser, the timeline matches the stored plan. |
| 7.3 | Plan page: resource chart (stock, cap, production) and the culture point curve. | In the browser, the chart shows the caps and the curve reaches the threshold at the goal time. |
| 7.4 | Plans page: list with inputs, snapshot, and time to goal. | In the browser, the list opens each plan. |

Gate: the player runs the default goal for their tribe and follows the first actions in the real game as a sanity check.

## Stage 8: Advisor

Goal: the advisor plans from pasted game pages.

| Step | Change | Check |
|---|---|---|
| 8.1 | The player supplies real game page samples, as the survey lists. Conceptual tests for stage 8 (separate agent). | The player accepts the list. |
| 8.2 | Village page port and parser adapter with the samples as fixtures. | Fixture tests pass. A missing page gives a named error. |
| 8.3 | Parsed-state preview: endpoint and New plan page option "From game pages". | In the browser, the preview matches the real village. |
| 8.4 | Advisor run: create a plan from pages. The plan page highlights the next actions. | In the browser, the next actions are shown at the top. |
| 8.5 | Re-plan: paste again after an adventure or a delay to get a new plan. | In the browser, a second paste gives a new plan from the new state. |

Gate: conceptual tests pass. The player follows advisor actions in the real game for one day.

## Later phase

- A learned policy (reinforcement learning) that implements the policy interface.
