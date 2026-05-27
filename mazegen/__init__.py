#!/usr/bin/env python3
"""Maze Generator Module.

A reusable maze generation library that creates random mazes
with configurable dimensions, entry/exit points, and options.

Usage:
    from mazegen import MazeGenerator

    maze = MazeGenerator(width=20, height=15,
                         entry=(0, 0), exit_pos=(19, 14))
    maze.generate()
    print(maze.to_ascii(show_path=True))

Parameters:
    width: Number of cells horizontally (minimum 3).
    height: Number of cells vertically (minimum 3).
    entry: Entry cell coordinates as (x, y).
    exit_pos: Exit cell coordinates as (x, y).
    perfect: If True, generates a perfect maze (default True).
    seed: Random seed for reproducibility (default None).

Access the maze structure:
    maze.grid[y][x]  -> wall bitmask for cell (x, y)
    Bit 0 (1) = North, Bit 1 (2) = East,
    Bit 2 (4) = South, Bit 3 (8) = West

Get the solution:
    path = maze.solve()  -> list of 'N','E','S','W' directions
"""
from __future__ import annotations

import random
from collections import deque
from typing import Optional

# Direction constants (wall bitmask values)
N: int = 1
E: int = 2
S: int = 4
W: int = 8

OPPOSITE: dict[int, int] = {N: S, S: N, E: W, W: E}
DX: dict[int, int] = {N: 0, S: 0, E: 1, W: -1}
DY: dict[int, int] = {N: -1, S: 1, E: 0, W: 0}
DIRECTIONS: list[int] = [N, E, S, W]
DIR_CHAR: dict[int, str] = {N: 'N', E: 'E', S: 'S', W: 'W'}

# Digit patterns for "42" (3 wide x 5 tall, 1 = filled cell)
DIGIT_4: list[list[int]] = [
    [1, 0, 1],
    [1, 0, 1],
    [1, 1, 1],
    [0, 0, 1],
    [0, 0, 1],
]

DIGIT_2: list[list[int]] = [
    [1, 1, 1],
    [0, 0, 1],
    [1, 1, 1],
    [1, 0, 0],
    [1, 1, 1],
]


class MazeGenerator:
    """Generate random mazes with configurable options.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry cell coordinates (x, y).
        exit_pos: Exit cell coordinates (x, y).
        perfect: Whether maze is perfect (single path).
        seed: Random seed for reproducibility.
        grid: 2D list [y][x] of wall bitmasks.
    """

    def __init__(self, width: int, height: int,
                 entry: tuple[int, int],
                 exit_pos: tuple[int, int],
                 perfect: bool = True,
                 seed: Optional[int] = None) -> None:
        """Initialize the maze generator.

        Args:
            width: Number of cells horizontally.
            height: Number of cells vertically.
            entry: Entry coordinates (x, y).
            exit_pos: Exit coordinates (x, y).
            perfect: If True, generate perfect maze.
            seed: Random seed for reproducibility.

        Raises:
            ValueError: If parameters are invalid.
        """
        if width < 3 or height < 3:
            raise ValueError("Maze must be at least 3x3")
        if entry == exit_pos:
            raise ValueError("Entry and exit must be different")
        if not (0 <= entry[0] < width and 0 <= entry[1] < height):
            raise ValueError(f"Entry {entry} out of bounds")
        if not (0 <= exit_pos[0] < width
                and 0 <= exit_pos[1] < height):
            raise ValueError(f"Exit {exit_pos} out of bounds")

        self.width: int = width
        self.height: int = height
        self.entry: tuple[int, int] = entry
        self.exit_pos: tuple[int, int] = exit_pos
        self.perfect: bool = perfect
        self.seed: Optional[int] = seed
        self.grid: list[list[int]] = []
        self._pattern_cells: set[tuple[int, int]] = set()
        self._solution: list[str] = []
        self._rng: random.Random = random.Random(seed)
        self._has_42: bool = False

    # ----- internal helpers -----

    def _in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within maze bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _has_wall(self, x: int, y: int, d: int) -> bool:
        """Check if cell (x,y) has wall in direction d."""
        return bool(self.grid[y][x] & d)

    def _remove_wall(self, x: int, y: int, d: int) -> None:
        """Remove wall between (x,y) and neighbor in direction d."""
        nx: int = x + DX[d]
        ny: int = y + DY[d]
        if self._in_bounds(nx, ny):
            self.grid[y][x] &= ~d
            self.grid[ny][nx] &= ~OPPOSITE[d]

    # ----- 42 pattern -----

    def _place_42(self) -> bool:
        """Place '42' pattern of fully walled cells in center.

        Returns:
            True if placed, False if maze too small.
        """
        pw: int = 7   # 3 + 1 gap + 3
        ph: int = 5
        if self.width < pw + 4 or self.height < ph + 4:
            return False

        sx: int = (self.width - pw) // 2
        sy: int = (self.height - ph) // 2

        cells: set[tuple[int, int]] = set()
        for dy in range(5):
            for dx in range(3):
                if DIGIT_4[dy][dx]:
                    cells.add((sx + dx, sy + dy))
                if DIGIT_2[dy][dx]:
                    cells.add((sx + 4 + dx, sy + dy))

        if self.entry in cells or self.exit_pos in cells:
            return False

        self._pattern_cells = cells
        for cx, cy in cells:
            self.grid[cy][cx] = 0xF
        return True

    # ----- maze generation (DFS) -----

    def _generate_dfs(self) -> None:
        """Generate maze using iterative DFS / Recursive Backtracker."""
        sx: int = self.entry[0]
        sy: int = self.entry[1]
        if (sx, sy) in self._pattern_cells:
            found: bool = False
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) not in self._pattern_cells:
                        sx, sy = x, y
                        found = True
                        break
                if found:
                    break

        visited: set[tuple[int, int]] = {(sx, sy)}
        visited.update(self._pattern_cells)
        stack: list[tuple[int, int]] = [(sx, sy)]

        while stack:
            x, y = stack[-1]
            nbrs: list[tuple[int, int, int]] = []
            for d in DIRECTIONS:
                nx: int = x + DX[d]
                ny: int = y + DY[d]
                if (self._in_bounds(nx, ny)
                        and (nx, ny) not in visited):
                    nbrs.append((nx, ny, d))
            if nbrs:
                nx, ny, d = self._rng.choice(nbrs)
                self._remove_wall(x, y, d)
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

    # ----- imperfect maze -----

    def _check_3x3(self, ox: int, oy: int) -> bool:
        """Check if 3x3 area at (ox,oy) is fully open."""
        for dy in range(3):
            for dx in range(3):
                cx: int = ox + dx
                cy: int = oy + dy
                if not self._in_bounds(cx, cy):
                    return False
                if (cx, cy) in self._pattern_cells:
                    return False
                if dx < 2 and self._has_wall(cx, cy, E):
                    return False
                if dy < 2 and self._has_wall(cx, cy, S):
                    return False
        return True

    def _would_create_3x3(self, wx: int, wy: int,
                          wd: int) -> bool:
        """Check if removing wall creates a 3x3 open area."""
        self._remove_wall(wx, wy, wd)
        violation: bool = False
        for cy in range(max(0, wy - 2),
                        min(self.height - 2, wy + 1)):
            for cx in range(max(0, wx - 2),
                            min(self.width - 2, wx + 1)):
                if self._check_3x3(cx, cy):
                    violation = True
                    break
            if violation:
                break
        # Restore wall
        nx: int = wx + DX[wd]
        ny: int = wy + DY[wd]
        self.grid[wy][wx] |= wd
        self.grid[ny][nx] |= OPPOSITE[wd]
        return violation

    def _make_imperfect(self) -> None:
        """Remove extra walls to create loops (non-perfect)."""
        walls: list[tuple[int, int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self._pattern_cells:
                    continue
                for d in [E, S]:
                    nx: int = x + DX[d]
                    ny: int = y + DY[d]
                    if (self._in_bounds(nx, ny)
                            and (nx, ny) not in self._pattern_cells
                            and self._has_wall(x, y, d)):
                        walls.append((x, y, d))
        self._rng.shuffle(walls)
        target: int = max(1, len(walls) // 10)
        removed: int = 0
        for wx, wy, wd in walls:
            if removed >= target:
                break
            if not self._would_create_3x3(wx, wy, wd):
                self._remove_wall(wx, wy, wd)
                removed += 1

    # ----- public API -----

    def generate(self) -> None:
        """Generate the maze.

        Initializes the grid, places the 42 pattern,
        generates corridors using DFS, and solves.
        """
        self.grid = [[0xF] * self.width
                     for _ in range(self.height)]
        self._pattern_cells.clear()
        self._solution.clear()
        self._rng = random.Random(self.seed)

        self._has_42 = self._place_42()
        self._generate_dfs()
        if not self.perfect:
            self._make_imperfect()
        self._solution = self.solve()

    def solve(self) -> list[str]:
        """Find shortest path from entry to exit using BFS.

        Returns:
            List of direction characters ('N','E','S','W').
        """
        queue: deque[tuple[int, int, list[str]]] = deque()
        queue.append((self.entry[0], self.entry[1], []))
        visited: set[tuple[int, int]] = {self.entry}

        while queue:
            x, y, path = queue.popleft()
            if (x, y) == self.exit_pos:
                return path
            for d in DIRECTIONS:
                if not self._has_wall(x, y, d):
                    nx: int = x + DX[d]
                    ny: int = y + DY[d]
                    if (self._in_bounds(nx, ny)
                            and (nx, ny) not in visited):
                        visited.add((nx, ny))
                        queue.append(
                            (nx, ny, path + [DIR_CHAR[d]]))
        return []

    def get_solution(self) -> list[str]:
        """Get the cached solution path.

        Returns:
            List of direction characters.
        """
        return list(self._solution)

    def has_42_pattern(self) -> bool:
        """Check if the 42 pattern was placed.

        Returns:
            True if the 42 pattern is present.
        """
        return self._has_42

    def get_pattern_cells(self) -> set[tuple[int, int]]:
        """Get the set of cells used by the 42 pattern.

        Returns:
            Set of (x, y) coordinates.
        """
        return set(self._pattern_cells)

    def to_hex_grid(self) -> list[str]:
        """Return maze as list of hex strings, one per row.

        Returns:
            List of strings with one hex digit per cell.
        """
        result: list[str] = []
        for y in range(self.height):
            row: str = ""
            for x in range(self.width):
                row += format(self.grid[y][x], 'X')
            result.append(row)
        return result

    def write_output(self, filename: str) -> None:
        """Write maze to output file in required format.

        Args:
            filename: Output file path.
        """
        with open(filename, 'w') as f:
            for line in self.to_hex_grid():
                f.write(line + '\n')
            f.write('\n')
            f.write(f"{self.entry[0]},{self.entry[1]}\n")
            f.write(f"{self.exit_pos[0]},{self.exit_pos[1]}\n")
            f.write(''.join(self._solution) + '\n')

    def to_ascii(self, show_path: bool = False,
                 wall_color: str = "white",
                 path_color: str = "green",
                 pattern_color: str = "yellow") -> str:
        """Return colored block representation of the maze.

        Uses Unicode block characters for a graphical look.
        Each cell is rendered as a 2x2 block grid with 1-cell
        wide walls between them.

        Args:
            show_path: Whether to highlight the solution.
            wall_color: ANSI color name for walls.
            path_color: ANSI color name for path.
            pattern_color: ANSI color name for 42 pattern.

        Returns:
            Multi-line string with ANSI color codes.
        """
        BG_COLORS: dict[str, str] = {
            "white":   "\033[47m",
            "red":     "\033[41m",
            "green":   "\033[42m",
            "blue":    "\033[44m",
            "yellow":  "\033[43m",
            "cyan":    "\033[46m",
            "magenta": "\033[45m",
        }
        rst: str = "\033[0m"
        WALL: str = "  "   # 2 spaces with bg color = filled block
        OPEN: str = "  "   # 2 spaces, no color = empty

        wbg: str = BG_COLORS.get(wall_color, "\033[47m")
        pbg: str = BG_COLORS.get(path_color, "\033[42m")
        ptbg: str = BG_COLORS.get(pattern_color, "\033[43m")
        entry_bg: str = "\033[45m"   # magenta for entry
        exit_bg: str = "\033[41m"    # red for exit
        bold: str = "\033[1m"

        # Build path set
        path_set: set[tuple[int, int]] = set()
        if show_path and self._solution:
            px: int = self.entry[0]
            py: int = self.entry[1]
            path_set.add((px, py))
            for dc in self._solution:
                for d, c in DIR_CHAR.items():
                    if c == dc:
                        px += DX[d]
                        py += DY[d]
                        path_set.add((px, py))
                        break

        def wall_block(color: str) -> str:
            """Return a colored wall block (2 chars wide)."""
            return color + WALL + rst

        def cell_block(x: int, y: int) -> str:
            """Return the 2-char interior of cell (x, y)."""
            if (x, y) == self.entry:
                return entry_bg + bold + "IN" + rst
            if (x, y) == self.exit_pos:
                return exit_bg + bold + "EX" + rst
            if (x, y) in self._pattern_cells:
                return ptbg + WALL + rst
            if (x, y) in path_set:
                return pbg + WALL + rst
            return OPEN

        # Grid is (2*height+1) rows x (2*width+1) cols of 2-char blocks
        # Row 2*y   = top wall row for cell row y
        # Row 2*y+1 = cell interior row for cell row y
        # Col 2*x   = left wall col for cell col x
        # Col 2*x+1 = cell interior col for cell col x

        rows: list[str] = []

        for y in range(self.height):
            # --- top wall row ---
            top: str = ""
            for x in range(self.width):
                top += wall_block(wbg)
                if self._has_wall(x, y, N):
                    top += wall_block(wbg)
                else:
                    if (x, y) in path_set and (x, y - 1) in path_set:
                        top += wall_block(pbg)
                    else:
                        top += OPEN
            top += wall_block(wbg)
            rows.append(top)

            # --- cell interior row ---
            mid: str = ""
            for x in range(self.width):
                if self._has_wall(x, y, W):
                    mid += wall_block(wbg)
                else:
                    if (x, y) in path_set and (x - 1, y) in path_set:
                        mid += wall_block(pbg)
                    else:
                        mid += OPEN
                mid += cell_block(x, y)
            if self._has_wall(self.width - 1, y, E):
                mid += wall_block(wbg)
            else:
                mid += OPEN
            rows.append(mid)

        # --- bottom wall row ---
        bot: str = ""
        for x in range(self.width):
            bot += wall_block(wbg)
            if self._has_wall(x, self.height - 1, S):
                bot += wall_block(wbg)
            else:
                bot += OPEN
        bot += wall_block(wbg)
        rows.append(bot)

        return '\n'.join(rows)
