*This project has been created as part of the 42 curriculum by rbriguet.*

# A-Maze-ing

## Description

A maze generator in Python that reads a configuration file, generates a random maze (optionally perfect), and outputs it in hexadecimal format. The program provides an interactive ASCII terminal display with solution path visualization and color customization.

The maze includes a visible "42" pattern drawn with fully closed cells, and supports reproducible generation via seeds.

## Instructions

### Installation

```bash
make install
```

### Run

```bash
python3 a_maze_ing.py config.txt
```

Or:
```bash
make run
```

### Debug mode

```bash
make debug
```

### Linting

```bash
make lint          # flake8 + mypy
make lint-strict   # flake8 + mypy --strict
```

### Clean

```bash
make clean
```

### Build package

```bash
make build
```

This creates `mazegen-1.0.0-py3-none-any.whl` at the project root.

## Configuration file format

The config file uses `KEY=VALUE` format. Lines starting with `#` are comments.

| Key | Required | Description | Example |
|-----|----------|-------------|---------|
| `WIDTH` | Yes | Maze width in cells | `WIDTH=20` |
| `HEIGHT` | Yes | Maze height in cells | `HEIGHT=15` |
| `ENTRY` | Yes | Entry cell coordinates (x,y) | `ENTRY=0,0` |
| `EXIT` | Yes | Exit cell coordinates (x,y) | `EXIT=19,14` |
| `OUTPUT_FILE` | Yes | Output filename | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Yes | Perfect maze (True/False) | `PERFECT=True` |
| `SEED` | No | Random seed for reproducibility | `SEED=42` |

Example config:
```
# A-Maze-ing configuration
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

## Maze generation algorithm

### Algorithm: Recursive Backtracker (Iterative DFS)

I chose the **Recursive Backtracker** algorithm (implemented iteratively with a stack) because:

1. **Guarantees perfect mazes** — naturally produces a spanning tree where there is exactly one path between any two cells.
2. **Simple to implement** — the algorithm is straightforward with a clear loop structure.
3. **Produces interesting mazes** — creates long, winding corridors with a natural feel.
4. **Easy to make imperfect** — to create non-perfect mazes, I simply remove extra walls after generation while checking the no-3x3-open-area constraint.

### How it works

1. Start from the entry cell, mark it as visited
2. Push it onto the stack
3. While the stack is not empty:
   - Look at the current cell (top of stack)
   - Find all unvisited neighbors
   - If there are unvisited neighbors: pick one at random, remove the wall between them, mark the neighbor as visited, push it
   - If no unvisited neighbors: pop (backtrack)
4. This visits every cell exactly once, creating a spanning tree

### Path solving

The shortest path is found using **BFS (Breadth-First Search)** from entry to exit, which guarantees the shortest path in an unweighted graph.

## Output file format

Each cell is encoded as a single hex digit representing its walls:

| Bit | Direction | Value |
|-----|-----------|-------|
| 0 (LSB) | North | 1 |
| 1 | East | 2 |
| 2 | South | 4 |
| 3 | West | 8 |

Example: `F` = all walls closed (1111), `0` = all walls open (0000), `A` = East+West closed (1010).

The file contains:
1. Hex grid (one row per line)
2. Empty line
3. Entry coordinates
4. Exit coordinates
5. Shortest path (N/E/S/W characters)

## Interactive features

| Key | Action |
|-----|--------|
| `r` | Regenerate maze with new seed |
| `s` | Show/Hide solution path |
| `c` | Cycle wall colors (white, red, green, blue, yellow, cyan, magenta) |
| `p` | Cycle 42 pattern colors |
| `q` | Quit |

## Reusable module: mazegen

The maze generation logic is packaged as `mazegen`, a standalone Python module installable via pip.

### Installation from package

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Building the package

```bash
pip install build
python3 -m build
```

### Usage

```python
from mazegen import MazeGenerator

# Create and generate a maze
maze = MazeGenerator(
    width=20, height=15,
    entry=(0, 0), exit_pos=(19, 14),
    perfect=True, seed=42
)
maze.generate()

# Get the solution path
path = maze.solve()  # ['E', 'E', 'S', 'E', ...]

# Access the grid
cell_walls = maze.grid[y][x]  # hex bitmask (0-15)

# ASCII display
print(maze.to_ascii(show_path=True))

# Write to file
maze.write_output("maze.txt")
```

### Parameters

- `width` (int): Number of cells horizontally (min 3)
- `height` (int): Number of cells vertically (min 3)
- `entry` (tuple): Entry coordinates (x, y)
- `exit_pos` (tuple): Exit coordinates (x, y)
- `perfect` (bool): Perfect maze if True (default True)
- `seed` (int | None): Random seed (default None)

## Team and project management

### Roles

Solo project by rbriguet.

### Planning

1. Design maze generator module (MazeGenerator class)
2. Implement DFS generation + 42 pattern
3. Implement BFS solver
4. Build config parser and main script
5. Add interactive ASCII display
6. Package as pip-installable module
7. Testing and documentation

### What worked well

- Separating the maze logic into a reusable module made testing easy
- The DFS algorithm naturally handles the perfect maze requirement
- Using bitmasks for wall encoding is efficient and matches the output format

### What could be improved

- Could add animation during generation
- Could support multiple algorithms (Kruskal, Prim, etc.)
- Could add MLX graphical display

### Tools used

- Python 3.10+
- flake8 and mypy for code quality
- setuptools for packaging
- AI (Claude) was used for initial code structure and documentation

## Resources

- [Maze generation algorithms - Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Recursive Backtracker](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking)
- [Think Labyrinth - Perfect Mazes](https://www.astrolog.org/labyrnth/algrithm.htm)
