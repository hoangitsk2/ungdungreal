"""
Text-based Treasure Trail game.
Move through a grid, gather treasure, and reach the exit before health runs out.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

Position = Tuple[int, int]


@dataclass
class Cell:
    """Represents a single board cell."""

    kind: str = "empty"  # empty, exit, trap, treasure, potion
    discovered: bool = False

    def display(self, is_player: bool, reveal: bool) -> str:
        if is_player:
            return "🙂"
        if not (self.discovered or reveal):
            return "■"
        return {
            "empty": "·",
            "exit": "⬜",
            "trap": "⚠",
            "treasure": "💎",
            "potion": "✚",
        }[self.kind]


@dataclass
class Player:
    position: Position
    health: int = 3
    score: int = 0
    inventory: Dict[str, int] = field(default_factory=lambda: {"potion": 0})

    def apply_event(self, cell: Cell) -> str:
        if cell.kind == "trap":
            self.health -= 1
            return "You triggered a trap and lost 1 health!"
        if cell.kind == "treasure":
            self.score += 10
            return "Treasure found! +10 score."
        if cell.kind == "potion":
            self.inventory["potion"] += 1
            return "You picked up a potion. Use it to restore health."
        return ""

    def use_potion(self) -> str:
        if self.inventory["potion"] <= 0:
            return "No potions available."
        self.inventory["potion"] -= 1
        self.health += 1
        return "You used a potion and recovered 1 health."


class Game:
    directions = {
        "n": (-1, 0),
        "s": (1, 0),
        "w": (0, -1),
        "e": (0, 1),
    }

    def __init__(self, size: int = 7, seed: Optional[int] = None):
        self.size = size
        self.random = random.Random(seed)
        self.board: List[List[Cell]] = [[Cell() for _ in range(size)] for _ in range(size)]
        self.player = Player(position=(0, 0))
        self.exit = self._random_empty_cell(exclude={(0, 0)})
        self.traps = self._populate("trap", count=max(3, size // 2))
        self.treasures = self._populate("treasure", count=max(2, size // 3))
        self.potions = self._populate("potion", count=2)
        self.board[self.exit[0]][self.exit[1]].kind = "exit"
        self.discover_radius(self.player.position, radius=1)

    def _random_empty_cell(self, exclude: Set[Position]) -> Position:
        while True:
            pos = (self.random.randrange(self.size), self.random.randrange(self.size))
            if pos in exclude:
                continue
            cell = self.board[pos[0]][pos[1]]
            if cell.kind == "empty":
                return pos

    def _populate(self, kind: str, count: int) -> Set[Position]:
        positions = set()
        exclude = {(0, 0), self.exit}
        while len(positions) < count:
            pos = self._random_empty_cell(exclude=exclude | positions)
            positions.add(pos)
            r, c = pos
            self.board[r][c].kind = kind
        return positions

    def discover_radius(self, position: Position, radius: int) -> None:
        pr, pc = position
        for r in range(max(0, pr - radius), min(self.size, pr + radius + 1)):
            for c in range(max(0, pc - radius), min(self.size, pc + radius + 1)):
                self.board[r][c].discovered = True

    def move(self, direction: str) -> str:
        if direction not in self.directions:
            return "Invalid direction. Use n/s/e/w."
        dr, dc = self.directions[direction]
        r, c = self.player.position
        nr, nc = r + dr, c + dc
        if not (0 <= nr < self.size and 0 <= nc < self.size):
            return "You bumped into a wall!"

        self.player.position = (nr, nc)
        self.discover_radius(self.player.position, radius=1)
        cell = self.board[nr][nc]
        message = self.player.apply_event(cell)
        if cell.kind != "exit":
            cell.kind = "empty"
        return message or ""

    def is_over(self) -> bool:
        if self.player.health <= 0:
            return True
        return self.player.position == self.exit

    def render(self, reveal: bool = False) -> str:
        lines = []
        for r, row in enumerate(self.board):
            line = []
            for c, cell in enumerate(row):
                is_player = (r, c) == self.player.position
                line.append(cell.display(is_player, reveal=reveal))
            lines.append(" ".join(line))
        return "\n".join(lines)

    def status(self) -> str:
        return f"Health: {self.player.health} | Score: {self.player.score} | Potions: {self.player.inventory['potion']}"

    def reveal_hint(self) -> str:
        visible_exit = abs(self.player.position[0] - self.exit[0]) + abs(
            self.player.position[1] - self.exit[1]
        )
        return f"You sense the exit is about {visible_exit} steps away."

    def turn(self, command: str) -> str:
        cmd = command.lower().strip()
        if cmd == "hint":
            return self.reveal_hint()
        if cmd == "potion":
            return self.player.use_potion()
        return self.move(cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play the Treasure Trail game.")
    parser.add_argument(
        "--size", type=int, default=7, help="Board size (width and height)."
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--reveal",
        action="store_true",
        help="Reveal full board (for practicing or debugging).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = Game(size=max(5, args.size), seed=args.seed)
    print("Welcome to Treasure Trail!")
    print("Find the exit, gather treasure, and avoid traps. Commands: n, s, e, w, hint, potion.")
    print(game.status())
    print(game.render())

    while not game.is_over():
        command = input("Your move: ")
        message = game.turn(command)
        if message:
            print(message)
        if game.player.health <= 0:
            print("You collapsed in the dungeon. Game over!")
            break
        if game.player.position == game.exit:
            print("You found the exit! Well played.")
            break
        print(game.status())
        print(game.render(reveal=args.reveal))

    print("Final board:")
    print(game.render(reveal=True))
    print(game.status())


if __name__ == "__main__":
    main()
