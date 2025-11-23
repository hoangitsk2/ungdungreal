# ungdungreal

A small, text-based adventure called **Treasure Trail**. Navigate a hidden grid, collect treasure, sip potions, and find the exit before your health runs out.

## How to play

1. Run the game (Python 3.9+):
   ```bash
   python game.py
   ```
2. Move with `n`, `s`, `e`, `w`. You can also type `hint` for a distance clue or `potion` to restore health when you have one.
3. The board reveals around you as you explore. Traps cost health, treasures raise your score, and potions give extra chances.
4. Reach the exit before your health hits zero to win.

### Optional flags
- `--size <number>`: change the board dimensions (minimum 5).
- `--seed <number>`: play the same layout repeatedly for practice.
- `--reveal`: show the full board after every move (useful for learning the map).

Enjoy the adventure!
