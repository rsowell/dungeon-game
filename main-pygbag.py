import asyncio
from pathlib import Path
import pygame

WIDTH, HEIGHT = 900, 600
BASE_DIR = Path(__file__).parent
ASSET_DIR = BASE_DIR / "assets"
TEXT_DIR = BASE_DIR / "text"

def story(filename):
    """Read writer-owned prose from a UTF-8 file packaged with the game."""
    return (TEXT_DIR / filename).read_text(encoding="utf-8").strip()

class Monster:
    def __init__(self, name, armor, description):
        self.name = name
        self.armor = armor
        self.description = description

class Treasure:
    def __init__(self, name, value, description):
        self.name = name
        self.value = value
        self.description = description

class Weapon:
    def __init__(self, name, damage, description):
        self.name = name
        self.damage = damage
        self.description = description

class Room:
    def __init__(self, name, description, enter_sound=None):
        self.name = name
        self.description = description
        self.enter_sound = enter_sound
        self.neighbors = {}
        self.monster = None
        self.treasure = None
        self.weapon = None

    def add_neighbor(self, direction, room):
        self.neighbors[direction] = room

    def get_neighbor(self, direction):
        return self.neighbors.get(direction)

    def list_exits(self):
        return ", ".join(self.neighbors.keys())

class TextAdventure:
    def __init__(self):
        self.messages = []
        self.current_input = ""
        self.score = 0
        self.best_weapon_damage = 3
        self.game_over = False

        self.sounds = {
            "move": pygame.mixer.Sound(ASSET_DIR / "move.ogg"),
            "pickup": pygame.mixer.Sound(ASSET_DIR / "pickup.ogg"),
            "danger": pygame.mixer.Sound(ASSET_DIR / "danger.ogg"),
            "win": pygame.mixer.Sound(ASSET_DIR / "win.ogg"),
        }

        entrance = Room("entrance", story("entrance.txt"))
        hall = Room("hall", story("hall.txt"))
        armory = Room("armory", story("armory.txt"))
        lair = Room("lair", story("lair.txt"), "danger")

        entrance.add_neighbor("north", hall)
        hall.add_neighbor("south", entrance)
        hall.add_neighbor("west", armory)
        hall.add_neighbor("east", lair)
        armory.add_neighbor("east", hall)
        lair.add_neighbor("west", hall)

        hall.monster = Monster("wolf", 2, story("wolf.txt"))
        lair.monster = Monster("dragon", 4, story("dragon.txt"))
        hall.treasure = Treasure("diamond", 10, story("diamond.txt"))
        lair.treasure = Treasure("chalice", 90, story("chalice.txt"))
        armory.weapon = Weapon("axe", 5, story("axe.txt"))

        self.current_room = entrance
        self.say("Welcome to the dungeon!")
        self.say("Try: look, go north, take diamond, attack wolf")
        self.announce_room()

    def say(self, message):
        self.messages.append(message)

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def announce_room(self):
        self.say(f"You are in the {self.current_room.name}.")

    def look(self):
        self.say(f"You are in {self.current_room.description}.")
        if self.current_room.monster is not None:
            self.say(f"There is {self.current_room.monster.description} here.")
        if self.current_room.weapon is not None:
            self.say(f"There is {self.current_room.weapon.description} here.")
        if self.current_room.treasure is not None:
            self.say(f"There is {self.current_room.treasure.description} here.")
        self.say(f"Exits: {self.current_room.list_exits()}")

    def go(self, direction):
        destination = self.current_room.get_neighbor(direction)
        if destination is None:
            self.say("You can't go that way from here.")
            return
        self.current_room = destination
        self.play_sound("move")
        if self.current_room.enter_sound is not None:
            self.play_sound(self.current_room.enter_sound)
        self.announce_room()

    def attack(self, name):
        monster = self.current_room.monster
        if monster is not None and monster.name == name:
            if self.best_weapon_damage > monster.armor:
                self.say("You strike it dead!")
                self.current_room.monster = None
            else:
                self.say("Your blow bounces off harmlessly.")
                self.say(f"The {monster.name} eats your head!")
                self.say("GAME OVER")
                self.play_sound("danger")
                self.game_over = True
        else:
            self.say(f"There is no {name} here.")

    def take(self, name):
        treasure = self.current_room.treasure
        weapon = self.current_room.weapon
        if treasure is not None and treasure.name == name:
            self.current_room.treasure = None
            self.score += treasure.value
            self.play_sound("pickup")
            self.say(f"Your score is now {self.score} out of 100.")
            if self.score == 100:
                self.say("YOU WIN!")
                self.play_sound("win")
                self.game_over = True
        elif weapon is not None and weapon.name == name:
            self.current_room.weapon = None
            self.play_sound("pickup")
            if weapon.damage > self.best_weapon_damage:
                self.best_weapon_damage = weapon.damage
                self.say("You'll be a more effective fighter with this!")
        else:
            self.say(f"There is no {name} here.")

    def handle_command(self, line):
        self.say(f"> {line}")
        words = line.lower().split()

        if not words:
            return

        command = words[0]

        if self.current_room.monster is not None and command not in ["attack", "look"]:
            self.say("You can't do that with unfriendlies about.")
            return

        if command == "look":
            self.look()
        elif command == "go" and len(words) > 1:
            self.go(words[1])
        elif command == "attack" and len(words) > 1:
            self.attack(words[1])
        elif command == "take" and len(words) > 1:
            self.take(words[1])
        elif command == "help":
            self.say("Commands: look, go DIRECTION, take OBJECT, attack MONSTER")
        else:
            self.say("I don't understand that.")

def wrap_text(text, font, max_width):
    if not text:
        return [""]
    # Preserve paragraph breaks from the story files on screen.
    if "\n" in text:
        lines = []
        for paragraph in text.splitlines():
            lines.extend(wrap_text(paragraph, font, max_width))
        return lines
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = word if not current else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_game(screen, font, small_font, game):
    screen.fill((24, 24, 28))
    screen.blit(font.render("Tiny Text Adventure", True, (235, 235, 240)), (30, 20))

    lines = []
    for message in game.messages:
        lines.extend(wrap_text(message, small_font, WIDTH - 60))
    lines = lines[-20:]

    y = 70
    for line in lines:
        screen.blit(small_font.render(line, True, (220, 220, 225)), (30, y))
        y += 23

    pygame.draw.line(screen, (100, 100, 110), (30, HEIGHT - 70), (WIDTH - 30, HEIGHT - 70), 2)
    screen.blit(small_font.render("> " + game.current_input, True, (255, 255, 255)), (30, HEIGHT - 50))

async def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tiny Text Adventure")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 22)

    game = TextAdventure()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    if not game.game_over:
                        command = game.current_input.strip()
                        game.current_input = ""
                        game.handle_command(command)
                elif event.key == pygame.K_BACKSPACE:
                    game.current_input = game.current_input[:-1]
                elif event.unicode and event.unicode.isprintable():
                    game.current_input += event.unicode

        draw_game(screen, font, small_font, game)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())
