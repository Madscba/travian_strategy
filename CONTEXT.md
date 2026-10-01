# Travian Strategy

Context for a personal tool that plans the early game of one Travian Legends account. It finds fast build orders and advises the next move from the real village state.

## Business

The product serves one Travian Legends player who runs the tool locally. The player wants to grow the first village as fast as possible and found the second village early.

The early game is a long chain of small decisions: which resource field or building to raise next, when to train settlers, and when to collect task rewards and hero resources. A wrong order wastes hours of production. The tool simulates the economy of one village and searches for the order of actions that reaches a goal first.

The tool has two uses. The optimizer plans from a start state to a goal. The default goal is the second village, and the player can set another goal. The advisor reads the player's real village from pasted game pages, runs the optimizer from that state, and shows the next actions.

Adventures are random. A plan uses expected values, and the advisor re-plans when the player pastes the real outcome.

Game rules (costs, build times, effects) come from the Travian Legends knowledge base. The tool reads them into a stored game data snapshot, and every simulation uses one snapshot.

Outcomes that matter: less time to the second village, advice that matches the real game, and plans the player can follow by hand in the game.

## Language

### Planning

**Optimizer**:
The capability that searches for the fastest plan from a start state to a goal.
_Avoid_: Solver, planner, strategy simulator

**Advisor**:
The capability that runs the optimizer from the player's real village state and shows the next actions.
_Avoid_: Recommender, assistant, next-move engine

**Goal**:
The condition that ends a plan, for example "all resource fields at level 5". The default goal is the second village.
_Avoid_: Target, objective, end state

**Plan**:
An ordered list of actions with start times, from a start state to a goal.
_Avoid_: Build order, strategy, schedule

**Action**:
One player decision: construct, upgrade, train settlers, collect a task reward, or start an adventure.
_Avoid_: Move, step, command

**Policy**:
A rule that picks the next action from a game state. A hand-written rule and a learned agent are both policies.
_Avoid_: Agent, bot, strategy

**Baseline policy**:
A hand-written policy that sets the time that the optimizer must match or beat, for example "cheapest upgrade first".
_Avoid_: Heuristic, default strategy

**Second village**:
The default goal. The village has trained three settlers, and the account has the culture points for a second village. Travel and settling time are not part of it.
_Avoid_: Expansion, settle goal, village 2

### Village

**Game state**:
Everything that the simulator tracks at one moment: time, the village, the hero, and the tasks.
_Avoid_: State, snapshot, village state

**Tribe**:
The people that the player chose at account start. The tribe changes buildings, units, and build queue rules.
_Avoid_: Race, nation, faction

**Server speed**:
The multiplier of the game world that scales production, build times, and training times.
_Avoid_: Game speed, server type

**Field layout**:
The mix of resource fields in a village, written as wood-clay-iron-crop, for example 4-4-4-6.
_Avoid_: Village type, cropper type

**Resource field**:
One of the 18 places around the village that produce wood, clay, iron, or crop. A resource field always exists and starts at level 0.
_Avoid_: Field tile, resource tile, resource building

**Building site**:
One of the 22 places in the village center where the player can construct a building.
_Avoid_: Position, slot, spot

**Building**:
A structure on a building site, for example a Warehouse or a Main Building. A resource field is not a building.
_Avoid_: Structure, construction

**Construct**:
Put a new building on an empty building site at level 1.
_Avoid_: Build (for a new building), place

**Upgrade**:
Raise a resource field or a building by one level. This includes a resource field that goes from level 0 to level 1.
_Avoid_: Build (for a level increase), level up, improve

**Culture points**:
Points that the account accumulates over time from its buildings. The account needs a threshold of culture points for each new village.
_Avoid_: CP (in prose), culture

**Population**:
The number of inhabitants that the buildings and resource fields of a village need. The population consumes crop.
_Avoid_: Pop, inhabitants count

**Settler**:
A unit that founds a new village. A Residence, a Palace, or the tribe's equivalent building trains settlers.
_Avoid_: Settler troop, colonist

**Task**:
An in-game assignment with a fixed reward. The player collects the reward after the task condition is met.
_Avoid_: Quest, mission

**Hero**:
The unique unit of the player. In this product, the hero produces resources and goes on adventures.
_Avoid_: Avatar, champion

**Adventure**:
A trip of the hero with a random duration and a random reward.
_Avoid_: Expedition, quest

### Game data

**Game data snapshot**:
One stored copy of the game rules read from the knowledge base at one moment.
_Avoid_: Building data, static data, scrape result

**Knowledge base**:
The official Travian Legends web pages that list costs, build times, and effects. It is the source of every game data snapshot.
_Avoid_: Wiki, game data site
