import curses
import random
import tkinter
from tkinter import messagebox
from qa_tasks import tasks  # imported Q&A module

# Constants
grid_size = 10
ship_sizes = [5, 4, 3, 3, 2]
ship_names = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
row_labels = [chr(ord('A') + i) for i in range(grid_size)]
col_labels = [str(i + 1) for i in range(grid_size)]

# Q&A set; each question maps to a list of acceptable answers
#tasks = [
#    ("What is 2+2?", ["4", "four"]),
#    ("Name the capital of France.", ["Paris", "PARIS"]),
    #Jane
    
#]



def center_text(text, width):
    pad = max((width - len(text)) // 2, 0)
    return ' ' * pad + text

class BattleshipGrid:
    def __init__(self):
        self.ships = [[' ']*grid_size for _ in range(grid_size)]
        self.attacks = [[' ']*grid_size for _ in range(grid_size)]
        self.message = ''

    def place_ship(self, x, y, size, direction, mark):
        if direction == 'H':
            if y + size > grid_size:
                return False, "Out of bounds horizontally."
            for i in range(size):
                if self.ships[x][y+i] != ' ':
                    return False, "Collision detected."
            for i in range(size):
                self.ships[x][y+i] = mark
        else:
            if x + size > grid_size:
                return False, "Out of bounds vertically."
            for i in range(size):
                if self.ships[x+i][y] != ' ':
                    return False, "Collision detected."
            for i in range(size):
                self.ships[x+i][y] = mark
        return True, ''

    def attack(self, x, y):
        if self.attacks[x][y] != ' ':
            return False, "Already attacked."
        self.attacks[x][y] = 'X' if self.ships[x][y] != ' ' else 'O'
        return True, "Hit!" if self.attacks[x][y] == 'X' else "Miss."

    def draw(self, stdscr, title, offset_x=0, show_ships=True):
        width = 4 + grid_size * 3
        stdscr.addstr(0, offset_x, center_text(title, width))
        for j, lbl in enumerate(col_labels):
            stdscr.addstr(1, offset_x + 4 + j*3, lbl.rjust(2))
        for i in range(grid_size):
            stdscr.addstr(2+i, offset_x, row_labels[i] + '  ')
            for j in range(grid_size):
                if show_ships:
                    cell = self.ships[i][j] if self.ships[i][j] != ' ' else self.attacks[i][j]
                else:
                    cell = self.attacks[i][j]
                if cell == 'X': color = curses.color_pair(2)
                elif cell == 'O': color = curses.color_pair(3)
                elif show_ships and self.ships[i][j] != ' ': color = curses.color_pair(1)
                else: color = curses.A_NORMAL
                stdscr.addstr(2+i, offset_x + 4 + j*3, f"[{cell}]", color)
        if self.message:
            stdscr.addstr(2 + grid_size, offset_x, self.message)
        stdscr.refresh()

    def stats(self):
        hits = sum(cell=='X' for row in self.attacks for cell in row)
        misses = sum(cell=='O' for row in self.attacks for cell in row)
        return hits, misses

# get player name
def get_name(stdscr, num):
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Player {num}, enter your name: ")
        curses.echo()
        name = stdscr.getstr(0, len(f"Player {num}, enter your name: "), 20).decode().strip()
        curses.noecho()
        if name:
            return name
        stdscr.addstr(1, 0, "Invalid name.")
        stdscr.refresh(); curses.napms(1000)

# deployment phase: mouse + h/v only
def deploy_phase(stdscr, name, grid):
    idx = 0
    direction = 'H'
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    ship_list = ", ".join(f"{n}({s})" for n,s in zip(ship_names, ship_sizes))
    while idx < len(ship_sizes):
        stdscr.clear(); grid.message = ''
        grid.draw(stdscr, f"{name}'s Deployment")
        stdscr.addstr(2+grid_size+1, 0, "Reference: " + ship_list)
        base = 3 + grid_size + 1
        stdscr.addstr(base, 0, "Press 'h'/'v' to change orientation.")
        stdscr.addstr(base+1, 0, f"Orientation: {'Horizontal' if direction=='H' else 'Vertical'}")
        stdscr.addstr(base+2, 0, f"Placing {ship_names[idx]} (size {ship_sizes[idx]})")
        stdscr.addstr(base+3, 0, "Click a cell to place ship :D")
        stdscr.refresh()
        key = stdscr.getch()
        if key == ord('h'):
            direction = 'H'; continue
        if key == ord('v'):
            direction = 'V'; continue
        if key == curses.KEY_MOUSE:
            _, mx, my, _, _ = curses.getmouse()
            gx, gy = my-2, (mx-4)//3
            if 0<=gx<grid_size and 0<=gy<grid_size:
                ok, msg = grid.place_ship(gx, gy, ship_sizes[idx], direction, ship_names[idx][0])
                if ok:
                    idx += 1; grid.message = ''
                else:
                    grid.message = msg
            else:
                grid.message = "Click out of grid."
    stdscr.clear(); grid.draw(stdscr, f"{name}'s Fleet Deployed!")
    stdscr.addstr(3+grid_size+1, 0, "Press any key to continue.")
    stdscr.refresh(); stdscr.getch()

# battle phase with Q&A lock and turn stays on hit
def battle_phase(stdscr, p1, p2, g1, g2, qs):
    turn = 1
    pool = list(range(len(qs)))
    skipped = []
    total = sum(ship_sizes)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    left_x, right_x = 0, grid_size*3+10

    while True:
        stdscr.clear()
        # Draw boards and stats
        g1.draw(stdscr, p1, offset_x=left_x, show_ships=False)
        h1, m1 = g1.stats()
        stdscr.addstr(3+grid_size+1, left_x, f"Hits:{h1} Misses:{m1}")
        g2.draw(stdscr, p2, offset_x=right_x, show_ships=False)
        h2, m2 = g2.stats()
        stdscr.addstr(3+grid_size+1, right_x, f"Hits:{h2} Misses:{m2}")

        # Turn info below stats
        turn_row = 4 + grid_size + 1
        stdscr.addstr(turn_row, 0, f"Turn: {p1 if turn % 2 == 1 else p2}")
        stdscr.refresh()

        # Check win condition
        if h1 >= total or h2 >= total:
            winner = p2 if h1 >= total else p1
            #stdscr.addstr(turn_row+2, 0, f"{winner} wins!")
            tkinter.messagebox.showinfo("alert", f"{winner} Wins!")
            #stdscr.addstr(turn_row+3, 0, "Press any key to exit.")
            stdscr.refresh() #; stdscr.getch()
            #continue
            #break

        #moved out of the whiletrue
        if not pool:
            pool = list(range(len(qs)))
            skipped.clear()
        q_idx = random.choice(pool)
        q, ans_list = qs[q_idx]
        
        # Q&A loop: must answer correctly or skip (skip triggers reshuffle when pool empty)
        while True:
            # Ensure pool has questions, refill from full if empty
            stdscr.refresh()
            #if not pool:
            #    pool = list(range(len(qs)))
            #    skipped.clear()
            #q_idx = random.choice(pool)
            #q, ans_list = qs[q_idx]
            # 🔧 Clear and reprint question every time
            stdscr.move(turn_row+1, 0); stdscr.clrtoeol()
            stdscr.addstr(turn_row+1, 0, f"Q: {q}", curses.color_pair(4) | curses.A_BOLD)
            # 🔧 Clear and redraw input prompt
            stdscr.move(turn_row+9, 0); stdscr.clrtoeol()
            stdscr.addstr(turn_row+9, 0, "Answer (or 's' to skip): ")
            stdscr.refresh(); curses.echo()
            ans = stdscr.getstr(turn_row+9, len("Answer (or 's' to skip): "), 20).decode().strip()
            curses.noecho()

            if ans.lower() == 's':
                # skip: move question to skipped list, then if pool empty, reshuffle
                pool.remove(q_idx)
                skipped.append(q_idx)
                if not pool:
                    pool = list(range(len(qs)))
                    skipped.clear()
                # clear Q&A lines
                stdscr.move(turn_row+1, 0); stdscr.clrtoeol()
                stdscr.move(turn_row+2, 0); stdscr.clrtoeol()
                continue

            # Check answer against acceptable list
            if any(ans.lower() == a.lower() for a in ans_list):
                pool.remove(q_idx)
                # clear Q&A lines
                for r in range(turn_row+1, turn_row+7): stdscr.move(r, 0); stdscr.clrtoeol()
                stdscr.refresh()
                break
            else:
                stdscr.addstr(turn_row+8, 0, "Wrong! Try again.")
                stdscr.refresh(); curses.napms(1000)
                stdscr.move(turn_row+8, 0); stdscr.clrtoeol()
                continue

        # Attack loop: must click valid cell
        while True:
            key = stdscr.getch()
            if key == curses.KEY_MOUSE:
                _, mx, my, _, _ = curses.getmouse()
                if turn % 2 == 1:
                    gx, gy = my-2, (mx - right_x - 4)//3
                    if 0 <= gx < grid_size and 0 <= gy < grid_size:
                        ok, res = g2.attack(gx, gy)
                        if ok:
                            g2.message = res
                            if res == 'Miss.':
                                turn += 1
                            break
                else:
                    gx, gy = my-2, (mx - 4)//3
                    if 0 <= gx < grid_size and 0 <= gy < grid_size:
                        ok, res = g1.attack(gx, gy)
                        if ok:
                            g1.message = res
                            if res == 'Miss.':
                                turn += 1
                            break

# main

def main(stdscr):
    curses.curs_set(0)
    curses.start_color(); curses.use_default_colors()
    curses.init_pair(1,curses.COLOR_CYAN,-1); curses.init_pair(2,curses.COLOR_RED,-1); curses.init_pair(3,curses.COLOR_BLUE,-1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    p1 = get_name(stdscr,1); g1 = BattleshipGrid(); deploy_phase(stdscr,p1,g1)
    p2 = get_name(stdscr,2); g2 = BattleshipGrid(); deploy_phase(stdscr,p2,g2)
    battle_phase(stdscr,p1,p2,g1,g2,tasks)

if __name__=='__main__':
    curses.wrapper(main)
