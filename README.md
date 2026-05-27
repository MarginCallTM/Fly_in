*This project has been created as part of the 42 curriculum by acombier.*

# Fly-in — Drone Routing Simulation

## Description

Fly-in is a drone routing system. Given a network of connected **zones**,
it routes a whole fleet of drones from a single **start zone** to a single
**end zone** in as few simulation turns as possible, while respecting a set
of strict movement and capacity constraints.

The network is modelled as an **undirected weighted graph**:

- **Zones** are the nodes. Each zone has a type that drives its movement
  cost and accessibility: `normal` (cost 1), `priority` (cost 1, preferred),
  `restricted` (cost 2, reached after a 2-turn transit) and `blocked`
  (never entered). Zones also carry a `max_drones` capacity.
- **Connections** are the edges. Each connection has a `max_link_capacity`
  limiting how many drones may traverse it on the same turn.

The simulation runs turn by turn: at each turn every drone may move to an
adjacent zone, start a multi-turn move toward a restricted zone, or wait.
The output lists, one line per turn, every drone that moved.

The whole project is **object-oriented** and implements the graph, the
pathfinding and the traversal logic **from scratch** — no graph library
(`networkx`, `graphlib`, …) is used, as required by the subject.

## Instructions

The project targets **Python 3.10+**.

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
make install            # pip install -r requirements.txt
```

Dependencies: `colorama` (coloured terminal output), `matplotlib`
(optional graphical view), plus `flake8`, `mypy` and `pytest` for
development.

### Run

```bash
# Directly:
python3 main.py maps/easy/01_linear_path.txt

# Graphical animation of the simulation (matplotlib):
python3 main.py maps/easy/01_linear_path.txt --graph

# Through the Makefile:
make run MAP=maps/hard/03_ultimate_challenge.txt
```

### Other Makefile targets

```bash
make lint          # flake8 + mypy with the subject's flags
make lint-strict   # flake8 + mypy --strict
make debug         # run main.py under pdb
make clean         # remove __pycache__, .mypy_cache, .pytest_cache
```

### Map file format

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub:   goal 10 10 [color=yellow]
hub:       roof1 3 4 [zone=restricted color=red]
hub:       corridorA 4 3 [zone=priority color=green max_drones=2]
connection: hub-roof1
connection: corridorA-goal [max_link_capacity=2]
```

The parser reports the **line number and the cause** for any malformed
input (unknown zone type, duplicate connection, connection to an undefined
zone, negative capacity, dash in a name, missing/duplicate start or end…).

## Algorithm

The routing is split into three cooperating stages: **find routes**,
**assign drones to routes**, then **play the simulation**.

### 1. Shortest paths — Dijkstra from scratch (`router.py`)

`Router.shortest_path` is a hand-written **Dijkstra** using `heapq` purely
as a generic priority queue (allowed: it is a data structure, not a graph
library). Each zone's movement cost depends on its type
(`normal`/`priority` = 1, `restricted` = 2); `blocked` zones are never
expanded, so any path is valid by construction.

Ties are broken in favour of **priority zones**: the heap key is a tuple
`(cost, penalty, name)` where `penalty` increments by 1 for every
non-priority zone entered. At equal cost, the route crossing more
`priority` zones is preferred — exactly what the subject asks for.

### 2. Multiple routes & drone distribution

A single route is rarely enough: drones must spread out to keep the turn
count low. `Router.find_disjoint_paths` uses a **greedy residual-capacity**
strategy (inspired by flow-based / *lem-in* routing): it repeatedly takes
the current shortest path, then "consumes" one unit of capacity on every
intermediate zone (`max_drones`) and connection (`max_link_capacity`) it
crosses. A zone or connection drops out of the search once saturated. The
search stops when no path remains. A high-capacity route can be returned
several times — each copy is one parallel lane.

`PathPlanner.assign_drones_to_paths` then distributes drones over those
lanes with an **earliest-arrival** greedy rule: a lane already carrying
`k` drones delivers its next one at turn `k + lane.cost` (drones enter one
per turn). Each drone is placed on the lane with the smallest arrival turn,
filling fast lanes first and spilling onto slower ones only when it pays
off.

### 3. Turn-by-turn simulation & conflict handling (`simulator.py`)

The `Simulator` plays discrete turns until every drone reaches the end.
Capacity bookkeeping lives in the `Zone`/`Connection` models, so the engine
only decides *who* moves. Key rules from the subject (VII.2 / VII.3):

- **Simultaneous release** — drones are processed *most-advanced-first*
  (decreasing `path_index`). A slot freed by a leaving drone is therefore
  visible to a follower on the *same turn*, so a full chain of drones can
  shift forward at once.
- **Restricted zones (2-turn move)** — a drone first occupies the
  connection (output `D<ID>-<connection>`), then lands in the zone next turn
  (`D<ID>-<zone>`). It may never linger on the link, so the engine only
  engages the move if the destination zone will still have a free slot on
  arrival. A per-zone `incoming` counter reserves those pending slots to
  avoid overbooking.
- **Waiting** — a drone with no legal move simply stays put and is omitted
  from the turn's output line.
- **Deadlock guard** — a `max_turns` bound (1000) aborts a stuck
  simulation with a clear `RuntimeError` instead of looping forever.

### Complexity & adaptability

Each Dijkstra run is `O(E log V)`; routes are computed **once** up front
(at most `nb_drones` of them) and reused for the whole simulation — paths
are never recomputed per turn. The same pipeline adapts to every provided
topology without map-specific tuning.

## Visual Representation

The simulation provides visual feedback in two interchangeable forms,
selected at runtime. Both consume a *finished* simulation through a common
abstract `Renderer` interface (`renderer.py`), so they are fully swappable.

- **Terminal (default)** — `TerminalRenderer` prints the subject's
  turn-by-turn format: one line per turn of `D<ID>-<zone>` tokens. Each
  drone keeps a **stable colour** (via `colorama`) so it is easy to follow
  across turns, and a header recaps the fleet size and total turns. Drones
  that do not move are omitted; arrived drones disappear.
- **Graphical (`--graph`)** — `GraphicalRenderer` (matplotlib
  `FuncAnimation`) draws the static network — zones coloured **by type**,
  start as a square, end as a star, labelled — then animates one coloured
  dot per drone. A drone in transit toward a restricted zone is shown at
  the **middle of the connection**, making the 2-turn move visible at a
  glance.

These views turn an otherwise abstract turn log into something a reviewer
can read directly: the terminal output is precise and diff-able, while the
animation makes bottlenecks, waiting and multi-path distribution visible.

## Resources

- **Dijkstra's shortest path algorithm** — CLRS, *Introduction to
  Algorithms*; Wikipedia, "Dijkstra's algorithm".
- **Disjoint / multiple paths** — Suurballe's and Yen's algorithms; the
  *lem-in* (42) flow-based routing approach, which inspired the
  greedy residual-capacity distribution used here.
- **`heapq`** — Python standard library, binary-heap priority queue.
- **matplotlib animation** — `matplotlib.animation.FuncAnimation`
  documentation.

### Use of AI

An AI assistant was used as a **mentor/pair-programming guide**,
not as a code generator. It helped with:

- explaining concepts (Dijkstra, dataclasses, ABCs, mypy typing) and
  translating intuition from C to idiomatic Python;
- reviewing code for `flake8`/`mypy` compliance and edge cases;
- generating the documentation of this README file.


All code in this repository was written and is fully understood by the
author, who can explain and justify every line during peer review.

## Performance

Turn counts achieved on the provided maps (lower is better), against the
subject's reference targets:

| Map                       | Drones | Turns | Target      |
|---------------------------|:------:|:-----:|:-----------:|
| easy/01 linear path       | 2      | 4     | ≤ 6         |
| easy/02 simple fork       | 4      | 4     | ≤ 8         |
| easy/03 basic capacity    | 4      | 4     | ≤ 6         |
| medium/01 dead end trap   | 5      | 8     | ≤ 12        |
| medium/02 circular loop   | 6      | 15    | ≤ 15        |
| medium/03 priority puzzle | 5      | 7     | ≤ 12        |
| hard/01 maze nightmare    | 8      | 13    | ≤ 30        |
| hard/02 capacity hell     | 12     | 16    | ≤ 35        |
| hard/03 ultimate challenge| 15     | 26    | ≤ 45        |
