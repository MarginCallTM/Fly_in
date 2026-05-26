# Fly-in — Rapport de stress-test

Simulation de toutes les cartes via `Simulator.run()`. Le score = nombre total de tours (VII.6). Format de sortie conforme à VII.5.

## 1. Synthèse des benchmarks

| Difficulté | Carte | Drones | Tours | Target | Marge | Verdict |
|---|---|---|---:|---:|---:|---|
| Easy | 01_linear_path.txt | 2 | 4 | 6 | +2 | ✅ sous target |
| Easy | 02_simple_fork.txt | 4 | 4 | 8 | +4 | ✅ sous target |
| Easy | 03_basic_capacity.txt | 4 | 4 | 6 | +2 | ✅ sous target |
| Medium | 01_dead_end_trap.txt | 5 | 8 | 12 | +4 | ✅ sous target |
| Medium | 02_circular_loop.txt | 6 | 15 | 15 | +0 | ✅ sous target |
| Medium | 03_priority_puzzle.txt | 5 | 7 | 12 | +5 | ✅ sous target |
| Hard | 01_maze_nightmare.txt | 8 | 13 | 30 | +17 | ✅ sous target |
| Hard | 02_capacity_hell.txt | 12 | 16 | 35 | +19 | ✅ sous target |
| Hard | 03_ultimate_challenge.txt | 15 | 26 | 45 | +19 | ✅ sous target |
| Challenger | 01_the_impossible_dream.txt | 25 | 67 | 45 | -22 | ⚠️ au-dessus (bonus) |
| Edge | one_drone.txt | 1 | 1 | — | — | ✅ ok |
| Edge | direct_path.txt | 3 | 1 | — | — | ✅ ok |
| Edge | blocked_only.txt | 1 | — | — | — | ⛔ NoSolutionError: No route connects the start hub to the end hub |

> *Challenger* = bonus optionnel, n'affecte pas la note (VII.7). *Edge* = cas limites sans target.

## 2. Traces de simulation (tour par tour)

Chaque ligne = un tour. Token `D<ID>-<zone>` (arrivée) ou `D<ID>-<source>-<dest>` (drone en vol vers une zone restricted). Les drones immobiles sont omis.

### [Easy] 01_linear_path.txt

- **2 drones** · 4 zones · 3 connexions · restricted : aucune
- **4 tours** · 6 mouvements (1.5/tour)

```
T1   D1-waypoint1
T2   D1-waypoint2 D2-waypoint1
T3   D1-goal D2-waypoint2
T4   D2-goal
```

### [Easy] 02_simple_fork.txt

- **4 drones** · 5 zones · 5 connexions · restricted : aucune
- **4 tours** · 12 mouvements (3.0/tour)

```
T1   D1-junction D2-junction
T2   D1-path_a D2-path_b D3-junction D4-junction
T3   D1-goal D2-goal D3-path_a D4-path_b
T4   D3-goal D4-goal
```

### [Easy] 03_basic_capacity.txt

- **4 drones** · 4 zones · 3 connexions · restricted : aucune
- **4 tours** · 12 mouvements (3.0/tour)

```
T1   D1-bottleneck D2-bottleneck
T2   D1-wide_area D2-wide_area D3-bottleneck D4-bottleneck
T3   D1-goal D2-goal D3-wide_area D4-wide_area
T4   D3-goal D4-goal
```

### [Medium] 01_dead_end_trap.txt

- **5 drones** · 6 zones · 5 connexions · restricted : aucune
- **8 tours** · 20 mouvements (2.5/tour)

```
T1   D1-junction D2-junction
T2   D1-correct_path D3-junction
T3   D1-intermediate D2-correct_path D4-junction
T4   D1-goal D2-intermediate D3-correct_path D5-junction
T5   D2-goal D3-intermediate D4-correct_path
T6   D3-goal D4-intermediate D5-correct_path
T7   D4-goal D5-intermediate
T8   D5-goal
```

### [Medium] 02_circular_loop.txt

- **6 drones** · 7 zones · 7 connexions · restricted : exit_point
- **15 tours** · 30 mouvements (2.0/tour)

```
T1   D1-loop_a D2-loop_a
T2   D1-loop_b D2-loop_b D3-loop_a D4-loop_a
T3   D1-loop_b-exit_point D3-loop_b D5-loop_a
T4   D1-exit_point
T5   D1-goal D2-loop_b-exit_point D4-loop_b D6-loop_a
T6   D2-exit_point
T7   D2-goal D3-loop_b-exit_point D5-loop_b
T8   D3-exit_point
T9   D3-goal D4-loop_b-exit_point D6-loop_b
T10  D4-exit_point
T11  D4-goal D5-loop_b-exit_point
T12  D5-exit_point
T13  D5-goal D6-loop_b-exit_point
T14  D6-exit_point
T15  D6-goal
```

### [Medium] 03_priority_puzzle.txt

- **5 drones** · 7 zones · 7 connexions · restricted : slow_path1
- **7 tours** · 22 mouvements (3.1/tour)

```
T1   D1-fast_junction D2-fast_junction D3-start-slow_path1
T2   D1-fast_path D3-slow_path1 D4-fast_junction
T3   D1-merge_point D2-fast_path D3-slow_path2 D5-start-slow_path1
T4   D1-goal D2-merge_point D3-merge_point D4-fast_path D5-slow_path1
T5   D2-goal D3-goal D4-merge_point D5-slow_path2
T6   D4-goal D5-merge_point
T7   D5-goal
```

### [Hard] 01_maze_nightmare.txt

- **8 drones** · 17 zones · 22 connexions · restricted : trap_loop1, trap_loop2
- **13 tours** · 48 mouvements (3.7/tour)

```
T1   D1-maze_a1 D2-maze_a1
T2   D1-maze_a2 D3-maze_a1
T3   D1-maze_c2 D2-maze_a2 D4-maze_a1
T4   D1-bottleneck D2-maze_c2 D3-maze_a2 D5-maze_a1
T5   D1-final_stretch1 D2-bottleneck D3-maze_c2 D4-maze_a2 D6-maze_a1
T6   D1-goal D2-final_stretch1 D3-bottleneck D4-maze_c2 D5-maze_a2 D7-maze_a1
T7   D2-goal D3-final_stretch1 D4-bottleneck D5-maze_c2 D6-maze_a2 D8-maze_a1
T8   D3-goal D4-final_stretch1 D5-bottleneck D6-maze_c2 D7-maze_a2
T9   D4-goal D5-final_stretch1 D6-bottleneck D7-maze_c2 D8-maze_a2
T10  D5-goal D6-final_stretch1 D7-bottleneck D8-maze_c2
T11  D6-goal D7-final_stretch1 D8-bottleneck
T12  D7-goal D8-final_stretch1
T13  D8-goal
```

### [Hard] 02_capacity_hell.txt

- **12 drones** · 15 zones · 21 connexions · restricted : restricted_tunnel1, restricted_tunnel2, restricted_tunnel3
- **16 tours** · 60 mouvements (3.8/tour)

```
T1   D1-gate3
T2   D1-waiting_area3 D2-gate3
T3   D1-convergence D2-waiting_area3 D3-gate3
T4   D1-final_bottleneck D2-convergence D3-waiting_area3 D4-gate3
T5   D1-goal D2-final_bottleneck D3-convergence D4-waiting_area3 D5-gate3
T6   D2-goal D3-final_bottleneck D4-convergence D5-waiting_area3 D6-gate3
T7   D3-goal D4-final_bottleneck D5-convergence D6-waiting_area3 D7-gate3
T8   D4-goal D5-final_bottleneck D6-convergence D7-waiting_area3 D8-gate3
T9   D5-goal D6-final_bottleneck D7-convergence D8-waiting_area3 D9-gate3
T10  D6-goal D7-final_bottleneck D8-convergence D9-waiting_area3 D10-gate3
T11  D7-goal D8-final_bottleneck D9-convergence D10-waiting_area3 D11-gate3
T12  D8-goal D9-final_bottleneck D10-convergence D11-waiting_area3 D12-gate3
T13  D9-goal D10-final_bottleneck D11-convergence D12-waiting_area3
T14  D10-goal D11-final_bottleneck D12-convergence
T15  D11-goal D12-final_bottleneck
T16  D12-goal
```

### [Hard] 03_ultimate_challenge.txt

- **15 drones** · 31 zones · 37 connexions · restricted : conv_restricted1, conv_restricted2, overflow1, overflow2
- **26 tours** · 180 mouvements (6.9/tour)

```
T1   D1-dist_gate1
T2   D1-maze_correct D2-dist_gate1
T3   D1-bottleneck1 D2-maze_correct D3-dist_gate1
T4   D1-bottleneck2 D2-bottleneck1 D3-maze_correct D4-dist_gate1
T5   D1-priority_hub D2-bottleneck2 D3-bottleneck1 D4-maze_correct D5-dist_gate1
T6   D1-conv_priority1 D2-priority_hub D3-bottleneck2 D4-bottleneck1 D5-maze_correct D6-dist_gate1
T7   D1-conv_priority2 D2-conv_priority1 D3-priority_hub D4-bottleneck2 D5-bottleneck1 D6-maze_correct D7-dist_gate1
T8   D1-final_merge D2-conv_priority2 D3-conv_priority1 D4-priority_hub D5-bottleneck2 D6-bottleneck1 D7-maze_correct D8-dist_gate1
T9   D1-final_gate1 D2-final_merge D3-conv_priority2 D4-conv_priority1 D5-priority_hub D6-bottleneck2 D7-bottleneck1 D8-maze_correct D9-dist_gate1
T10  D1-final_gate2 D2-final_gate1 D3-final_merge D4-conv_priority2 D5-conv_priority1 D6-priority_hub D7-bottleneck2 D8-bottleneck1 D9-maze_correct D10-dist_gate1
T11  D1-final_gate3 D2-final_gate2 D3-final_gate1 D4-final_merge D5-conv_priority2 D6-conv_priority1 D7-priority_hub D8-bottleneck2 D9-bottleneck1 D10-maze_correct D11-dist_gate1
T12  D1-goal D2-final_gate3 D3-final_gate2 D4-final_gate1 D5-final_merge D6-conv_priority2 D7-conv_priority1 D8-priority_hub D9-bottleneck2 D10-bottleneck1 D11-maze_correct D12-dist_gate1
T13  D2-goal D3-final_gate3 D4-final_gate2 D5-final_gate1 D6-final_merge D7-conv_priority2 D8-conv_priority1 D9-priority_hub D10-bottleneck2 D11-bottleneck1 D12-maze_correct D13-dist_gate1
T14  D3-goal D4-final_gate3 D5-final_gate2 D6-final_gate1 D7-final_merge D8-conv_priority2 D9-conv_priority1 D10-priority_hub D11-bottleneck2 D12-bottleneck1 D13-maze_correct D14-dist_gate1
T15  D4-goal D5-final_gate3 D6-final_gate2 D7-final_gate1 D8-final_merge D9-conv_priority2 D10-conv_priority1 D11-priority_hub D12-bottleneck2 D13-bottleneck1 D14-maze_correct D15-dist_gate1
T16  D5-goal D6-final_gate3 D7-final_gate2 D8-final_gate1 D9-final_merge D10-conv_priority2 D11-conv_priority1 D12-priority_hub D13-bottleneck2 D14-bottleneck1 D15-maze_correct
T17  D6-goal D7-final_gate3 D8-final_gate2 D9-final_gate1 D10-final_merge D11-conv_priority2 D12-conv_priority1 D13-priority_hub D14-bottleneck2 D15-bottleneck1
T18  D7-goal D8-final_gate3 D9-final_gate2 D10-final_gate1 D11-final_merge D12-conv_priority2 D13-conv_priority1 D14-priority_hub D15-bottleneck2
T19  D8-goal D9-final_gate3 D10-final_gate2 D11-final_gate1 D12-final_merge D13-conv_priority2 D14-conv_priority1 D15-priority_hub
T20  D9-goal D10-final_gate3 D11-final_gate2 D12-final_gate1 D13-final_merge D14-conv_priority2 D15-conv_priority1
T21  D10-goal D11-final_gate3 D12-final_gate2 D13-final_gate1 D14-final_merge D15-conv_priority2
T22  D11-goal D12-final_gate3 D13-final_gate2 D14-final_gate1 D15-final_merge
T23  D12-goal D13-final_gate3 D14-final_gate2 D15-final_gate1
T24  D13-goal D14-final_gate3 D15-final_gate2
T25  D14-goal D15-final_gate3
T26  D15-goal
```

### [Challenger] 01_the_impossible_dream.txt

- **25 drones** · 54 zones · 70 connexions · restricted : conv_restricted1, conv_restricted2, conv_restricted3, conv_restricted4, conv_restricted5, conv_restricted6, conv_restricted7, conv_restricted8, conv_restricted9, maze_loop1, maze_loop2, maze_loop3, maze_loop4, maze_loop5, maze_loop6, overflow_hell1, overflow_hell2, overflow_hell3, overflow_hell4, overflow_hell5, overflow_hell6
- **67 tours** · 475 mouvements (7.1/tour)

```
T1   D1-gate_hell1
T2   D1-maze_trap_a1 D2-gate_hell1
T3   D1-maze_trap_a2 D2-maze_trap_a1 D3-gate_hell1
T4   D1-micro_gate1 D2-maze_trap_a2 D3-maze_trap_a1 D4-gate_hell1
T5   D1-micro_gate1-overflow_hell1 D2-micro_gate1 D3-maze_trap_a2 D4-maze_trap_a1 D5-gate_hell1
T6   D1-overflow_hell1 D2-micro_gate1-overflow_hell1 D3-micro_gate1 D4-maze_trap_a2 D5-maze_trap_a1 D6-gate_hell1
T7   D1-overflow_hell1-conv_restricted1 D2-overflow_hell1 D3-micro_gate1-overflow_hell1 D4-micro_gate1 D5-maze_trap_a2 D6-maze_trap_a1 D7-gate_hell1
T8   D1-conv_restricted1 D3-overflow_hell1
T9   D1-conv_restricted1-conv_restricted2 D2-overflow_hell1-conv_restricted1 D4-micro_gate1-overflow_hell1 D5-micro_gate1 D6-maze_trap_a2 D7-maze_trap_a1 D8-gate_hell1
T10  D1-conv_restricted2 D2-conv_restricted1 D4-overflow_hell1
T11  D1-conv_restricted2-conv_restricted3 D2-conv_restricted1-conv_restricted2 D3-overflow_hell1-conv_restricted1 D5-micro_gate1-overflow_hell1 D6-micro_gate1 D7-maze_trap_a2 D8-maze_trap_a1 D9-gate_hell1
T12  D1-conv_restricted3 D2-conv_restricted2 D3-conv_restricted1 D5-overflow_hell1
T13  D1-final_merge D2-conv_restricted2-conv_restricted3 D3-conv_restricted1-conv_restricted2 D4-overflow_hell1-conv_restricted1 D6-micro_gate1-overflow_hell1 D7-micro_gate1 D8-maze_trap_a2 D9-maze_trap_a1 D10-gate_hell1
T14  D1-final_torture1 D2-conv_restricted3 D3-conv_restricted2 D4-conv_restricted1 D6-overflow_hell1
T15  D1-final_torture2 D2-final_merge D3-conv_restricted2-conv_restricted3 D4-conv_restricted1-conv_restricted2 D5-overflow_hell1-conv_restricted1 D7-micro_gate1-overflow_hell1 D8-micro_gate1 D9-maze_trap_a2 D10-maze_trap_a1 D11-gate_hell1
T16  D1-final_torture3 D2-final_torture1 D3-conv_restricted3 D4-conv_restricted2 D5-conv_restricted1 D7-overflow_hell1
T17  D1-final_torture4 D2-final_torture2 D3-final_merge D4-conv_restricted2-conv_restricted3 D5-conv_restricted1-conv_restricted2 D6-overflow_hell1-conv_restricted1 D8-micro_gate1-overflow_hell1 D9-micro_gate1 D10-maze_trap_a2 D11-maze_trap_a1 D12-gate_hell1
T18  D1-final_torture5 D2-final_torture3 D3-final_torture1 D4-conv_restricted3 D5-conv_restricted2 D6-conv_restricted1 D8-overflow_hell1
T19  D1-impossible_goal D2-final_torture4 D3-final_torture2 D4-final_merge D5-conv_restricted2-conv_restricted3 D6-conv_restricted1-conv_restricted2 D7-overflow_hell1-conv_restricted1 D9-micro_gate1-overflow_hell1 D10-micro_gate1 D11-maze_trap_a2 D12-maze_trap_a1 D13-gate_hell1
T20  D2-final_torture5 D3-final_torture3 D4-final_torture1 D5-conv_restricted3 D6-conv_restricted2 D7-conv_restricted1 D9-overflow_hell1
T21  D2-impossible_goal D3-final_torture4 D4-final_torture2 D5-final_merge D6-conv_restricted2-conv_restricted3 D7-conv_restricted1-conv_restricted2 D8-overflow_hell1-conv_restricted1 D10-micro_gate1-overflow_hell1 D11-micro_gate1 D12-maze_trap_a2 D13-maze_trap_a1 D14-gate_hell1
T22  D3-final_torture5 D4-final_torture3 D5-final_torture1 D6-conv_restricted3 D7-conv_restricted2 D8-conv_restricted1 D10-overflow_hell1
T23  D3-impossible_goal D4-final_torture4 D5-final_torture2 D6-final_merge D7-conv_restricted2-conv_restricted3 D8-conv_restricted1-conv_restricted2 D9-overflow_hell1-conv_restricted1 D11-micro_gate1-overflow_hell1 D12-micro_gate1 D13-maze_trap_a2 D14-maze_trap_a1 D15-gate_hell1
T24  D4-final_torture5 D5-final_torture3 D6-final_torture1 D7-conv_restricted3 D8-conv_restricted2 D9-conv_restricted1 D11-overflow_hell1
T25  D4-impossible_goal D5-final_torture4 D6-final_torture2 D7-final_merge D8-conv_restricted2-conv_restricted3 D9-conv_restricted1-conv_restricted2 D10-overflow_hell1-conv_restricted1 D12-micro_gate1-overflow_hell1 D13-micro_gate1 D14-maze_trap_a2 D15-maze_trap_a1 D16-gate_hell1
T26  D5-final_torture5 D6-final_torture3 D7-final_torture1 D8-conv_restricted3 D9-conv_restricted2 D10-conv_restricted1 D12-overflow_hell1
T27  D5-impossible_goal D6-final_torture4 D7-final_torture2 D8-final_merge D9-conv_restricted2-conv_restricted3 D10-conv_restricted1-conv_restricted2 D11-overflow_hell1-conv_restricted1 D13-micro_gate1-overflow_hell1 D14-micro_gate1 D15-maze_trap_a2 D16-maze_trap_a1 D17-gate_hell1
T28  D6-final_torture5 D7-final_torture3 D8-final_torture1 D9-conv_restricted3 D10-conv_restricted2 D11-conv_restricted1 D13-overflow_hell1
T29  D6-impossible_goal D7-final_torture4 D8-final_torture2 D9-final_merge D10-conv_restricted2-conv_restricted3 D11-conv_restricted1-conv_restricted2 D12-overflow_hell1-conv_restricted1 D14-micro_gate1-overflow_hell1 D15-micro_gate1 D16-maze_trap_a2 D17-maze_trap_a1 D18-gate_hell1
T30  D7-final_torture5 D8-final_torture3 D9-final_torture1 D10-conv_restricted3 D11-conv_restricted2 D12-conv_restricted1 D14-overflow_hell1
T31  D7-impossible_goal D8-final_torture4 D9-final_torture2 D10-final_merge D11-conv_restricted2-conv_restricted3 D12-conv_restricted1-conv_restricted2 D13-overflow_hell1-conv_restricted1 D15-micro_gate1-overflow_hell1 D16-micro_gate1 D17-maze_trap_a2 D18-maze_trap_a1 D19-gate_hell1
T32  D8-final_torture5 D9-final_torture3 D10-final_torture1 D11-conv_restricted3 D12-conv_restricted2 D13-conv_restricted1 D15-overflow_hell1
T33  D8-impossible_goal D9-final_torture4 D10-final_torture2 D11-final_merge D12-conv_restricted2-conv_restricted3 D13-conv_restricted1-conv_restricted2 D14-overflow_hell1-conv_restricted1 D16-micro_gate1-overflow_hell1 D17-micro_gate1 D18-maze_trap_a2 D19-maze_trap_a1 D20-gate_hell1
T34  D9-final_torture5 D10-final_torture3 D11-final_torture1 D12-conv_restricted3 D13-conv_restricted2 D14-conv_restricted1 D16-overflow_hell1
T35  D9-impossible_goal D10-final_torture4 D11-final_torture2 D12-final_merge D13-conv_restricted2-conv_restricted3 D14-conv_restricted1-conv_restricted2 D15-overflow_hell1-conv_restricted1 D17-micro_gate1-overflow_hell1 D18-micro_gate1 D19-maze_trap_a2 D20-maze_trap_a1 D21-gate_hell1
T36  D10-final_torture5 D11-final_torture3 D12-final_torture1 D13-conv_restricted3 D14-conv_restricted2 D15-conv_restricted1 D17-overflow_hell1
T37  D10-impossible_goal D11-final_torture4 D12-final_torture2 D13-final_merge D14-conv_restricted2-conv_restricted3 D15-conv_restricted1-conv_restricted2 D16-overflow_hell1-conv_restricted1 D18-micro_gate1-overflow_hell1 D19-micro_gate1 D20-maze_trap_a2 D21-maze_trap_a1 D22-gate_hell1
T38  D11-final_torture5 D12-final_torture3 D13-final_torture1 D14-conv_restricted3 D15-conv_restricted2 D16-conv_restricted1 D18-overflow_hell1
T39  D11-impossible_goal D12-final_torture4 D13-final_torture2 D14-final_merge D15-conv_restricted2-conv_restricted3 D16-conv_restricted1-conv_restricted2 D17-overflow_hell1-conv_restricted1 D19-micro_gate1-overflow_hell1 D20-micro_gate1 D21-maze_trap_a2 D22-maze_trap_a1 D23-gate_hell1
T40  D12-final_torture5 D13-final_torture3 D14-final_torture1 D15-conv_restricted3 D16-conv_restricted2 D17-conv_restricted1 D19-overflow_hell1
T41  D12-impossible_goal D13-final_torture4 D14-final_torture2 D15-final_merge D16-conv_restricted2-conv_restricted3 D17-conv_restricted1-conv_restricted2 D18-overflow_hell1-conv_restricted1 D20-micro_gate1-overflow_hell1 D21-micro_gate1 D22-maze_trap_a2 D23-maze_trap_a1 D24-gate_hell1
T42  D13-final_torture5 D14-final_torture3 D15-final_torture1 D16-conv_restricted3 D17-conv_restricted2 D18-conv_restricted1 D20-overflow_hell1
T43  D13-impossible_goal D14-final_torture4 D15-final_torture2 D16-final_merge D17-conv_restricted2-conv_restricted3 D18-conv_restricted1-conv_restricted2 D19-overflow_hell1-conv_restricted1 D21-micro_gate1-overflow_hell1 D22-micro_gate1 D23-maze_trap_a2 D24-maze_trap_a1 D25-gate_hell1
T44  D14-final_torture5 D15-final_torture3 D16-final_torture1 D17-conv_restricted3 D18-conv_restricted2 D19-conv_restricted1 D21-overflow_hell1
T45  D14-impossible_goal D15-final_torture4 D16-final_torture2 D17-final_merge D18-conv_restricted2-conv_restricted3 D19-conv_restricted1-conv_restricted2 D20-overflow_hell1-conv_restricted1 D22-micro_gate1-overflow_hell1 D23-micro_gate1 D24-maze_trap_a2 D25-maze_trap_a1
T46  D15-final_torture5 D16-final_torture3 D17-final_torture1 D18-conv_restricted3 D19-conv_restricted2 D20-conv_restricted1 D22-overflow_hell1
T47  D15-impossible_goal D16-final_torture4 D17-final_torture2 D18-final_merge D19-conv_restricted2-conv_restricted3 D20-conv_restricted1-conv_restricted2 D21-overflow_hell1-conv_restricted1 D23-micro_gate1-overflow_hell1 D24-micro_gate1 D25-maze_trap_a2
T48  D16-final_torture5 D17-final_torture3 D18-final_torture1 D19-conv_restricted3 D20-conv_restricted2 D21-conv_restricted1 D23-overflow_hell1
T49  D16-impossible_goal D17-final_torture4 D18-final_torture2 D19-final_merge D20-conv_restricted2-conv_restricted3 D21-conv_restricted1-conv_restricted2 D22-overflow_hell1-conv_restricted1 D24-micro_gate1-overflow_hell1 D25-micro_gate1
T50  D17-final_torture5 D18-final_torture3 D19-final_torture1 D20-conv_restricted3 D21-conv_restricted2 D22-conv_restricted1 D24-overflow_hell1
T51  D17-impossible_goal D18-final_torture4 D19-final_torture2 D20-final_merge D21-conv_restricted2-conv_restricted3 D22-conv_restricted1-conv_restricted2 D23-overflow_hell1-conv_restricted1 D25-micro_gate1-overflow_hell1
T52  D18-final_torture5 D19-final_torture3 D20-final_torture1 D21-conv_restricted3 D22-conv_restricted2 D23-conv_restricted1 D25-overflow_hell1
T53  D18-impossible_goal D19-final_torture4 D20-final_torture2 D21-final_merge D22-conv_restricted2-conv_restricted3 D23-conv_restricted1-conv_restricted2 D24-overflow_hell1-conv_restricted1
T54  D19-final_torture5 D20-final_torture3 D21-final_torture1 D22-conv_restricted3 D23-conv_restricted2 D24-conv_restricted1
T55  D19-impossible_goal D20-final_torture4 D21-final_torture2 D22-final_merge D23-conv_restricted2-conv_restricted3 D24-conv_restricted1-conv_restricted2 D25-overflow_hell1-conv_restricted1
T56  D20-final_torture5 D21-final_torture3 D22-final_torture1 D23-conv_restricted3 D24-conv_restricted2 D25-conv_restricted1
T57  D20-impossible_goal D21-final_torture4 D22-final_torture2 D23-final_merge D24-conv_restricted2-conv_restricted3 D25-conv_restricted1-conv_restricted2
T58  D21-final_torture5 D22-final_torture3 D23-final_torture1 D24-conv_restricted3 D25-conv_restricted2
T59  D21-impossible_goal D22-final_torture4 D23-final_torture2 D24-final_merge D25-conv_restricted2-conv_restricted3
T60  D22-final_torture5 D23-final_torture3 D24-final_torture1 D25-conv_restricted3
T61  D22-impossible_goal D23-final_torture4 D24-final_torture2 D25-final_merge
T62  D23-final_torture5 D24-final_torture3 D25-final_torture1
T63  D23-impossible_goal D24-final_torture4 D25-final_torture2
T64  D24-final_torture5 D25-final_torture3
T65  D24-impossible_goal D25-final_torture4
T66  D25-final_torture5
T67  D25-impossible_goal
```

### [Edge] one_drone.txt

- **1 drones** · 2 zones · 1 connexions · restricted : aucune
- **1 tours** · 1 mouvements (1.0/tour)

```
T1   D1-goal
```

### [Edge] direct_path.txt

- **3 drones** · 2 zones · 1 connexions · restricted : aucune
- **1 tours** · 3 mouvements (3.0/tour)

```
T1   D1-goal D2-goal D3-goal
```

### [Edge] blocked_only.txt

⛔ Aucune solution : `NoSolutionError: No route connects the start hub to the end hub` (comportement attendu : aucune route start→end).

