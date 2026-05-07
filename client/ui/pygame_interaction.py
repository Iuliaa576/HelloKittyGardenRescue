"""
PyGame graphical interface for Hello Kitty Garden Rescue.

This module implements the graphical client of the distributed game using
the PyGame library.

It contains:
- The lobby interface for player name and character selection
- The graphical game board rendering
- Keyboard input handling
- Real-time game state visualization
- Waiting and end-game overlays

The interface communicates with the remote game server through the
GameClientStub abstraction layer and renders the synchronized shared game
state received from the server.

Run:
    python -m client.ui.pygame_interaction --host <server_ip>
"""

import argparse
import os

import pygame

from client.network.game_client_stub import GameClientStub
from shared.constants import DEFAULT_SERVER_ADDRESS


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


class LobbyScreen:
    WIDTH = 900
    HEIGHT = 600

    CHARACTERS = [
        ("hello_kitty", "Hello Kitty"),
        ("kuromi", "Kuromi"),
        ("cinnamoroll", "Cinnamoroll"),
        ("my_melody", "My Melody"),
    ]

    COLORS = {
        "background": (250, 230, 245),
        "panel": (255, 250, 255),
        "text": (45, 35, 50),
        "muted": (120, 105, 125),
        "selected": (255, 120, 180),
        "button": (255, 160, 200),
        "button_hover": (255, 135, 185),
        "button_text": (255, 255, 255),
        "border": (210, 170, 210),
        "white": (255, 255, 255),
    }

    def __init__(self):
        """Initialize the lobby screen and load interface resources."""
        pygame.display.set_caption("Hello Kitty Garden Rescue - Lobby")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font = pygame.font.SysFont("arial", 24)
        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_big = pygame.font.SysFont("arial", 32, bold=True)

        self.player_name = ""
        self.selected_character = "hello_kitty"
        self.images = self._load_images()

    def _load_images(self):
        """Load character images used in the lobby."""
        def load(path, size):
            try:
                image = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(image, size)
            except Exception:
                return None

        return {
            "hello_kitty": load(
                os.path.join(ASSETS_DIR, "characters", "hello_kitty.png"),
                (95, 95),
            ),
            "kuromi": load(
                os.path.join(ASSETS_DIR, "characters", "kuromi.png"),
                (95, 95),
            ),
            "cinnamoroll": load(
                os.path.join(ASSETS_DIR, "characters", "cinnamoroll.png"),
                (95, 95),
            ),
            "my_melody": load(
                os.path.join(ASSETS_DIR, "characters", "my_melody.png"),
                (95, 95),
            ),
        }

    def run(self):
        """Run the lobby loop until the player starts or quits."""
        while True:
            result = self._handle_events()

            if result == "start":
                name = self.player_name.strip() or "Player"
                return name, self.selected_character

            if result == "quit":
                return None, None

            self._draw()
            self.clock.tick(60)

    def _handle_events(self):
        """Handle keyboard and mouse input in the lobby."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"

                if event.key == pygame.K_RETURN:
                    return "start"

                if event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]

                elif event.key == pygame.K_TAB:
                    self._select_next_character()

                elif event.unicode and event.unicode.isprintable():
                    if len(self.player_name) < 16:
                        self.player_name += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                for character_id, _, rect in self._character_rects():
                    if rect.collidepoint(mouse_pos):
                        self.selected_character = character_id

                if self._start_button_rect().collidepoint(mouse_pos):
                    return "start"

        return None

    def _select_next_character(self):
        """Select the next available character."""
        ids = [character_id for character_id, _ in self.CHARACTERS]
        index = ids.index(self.selected_character)
        self.selected_character = ids[(index + 1) % len(ids)]

    def _draw(self):
        """Render all lobby screen components."""
        self.screen.fill(self.COLORS["background"])

        title = self.font_title.render(
            "Hello Kitty Garden Rescue",
            True,
            self.COLORS["text"],
        )
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 70)))

        subtitle = self.font.render(
            "Enter your name and choose your character",
            True,
            self.COLORS["muted"],
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.WIDTH // 2, 115)))

        self._draw_name_input()
        self._draw_characters()
        self._draw_start_button()

        hint = self.font_small.render(
            "Enter: start    Tab: change character    Esc: quit",
            True,
            self.COLORS["muted"],
        )
        self.screen.blit(hint, hint.get_rect(center=(self.WIDTH // 2, 560)))

        pygame.display.flip()

    def _draw_name_input(self):
        """Draw the player name input field."""
        label = self.font.render("Player name:", True, self.COLORS["text"])
        self.screen.blit(label, (260, 160))

        rect = pygame.Rect(260, 195, 380, 50)
        pygame.draw.rect(self.screen, self.COLORS["panel"], rect, border_radius=12)
        pygame.draw.rect(self.screen, self.COLORS["border"], rect, 2, border_radius=12)

        text = self.player_name if self.player_name else "Type your name..."
        color = self.COLORS["text"] if self.player_name else self.COLORS["muted"]

        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (rect.x + 15, rect.y + 12))

    def _draw_characters(self):
        """Draw the selectable character cards."""
        label = self.font.render("Choose character:", True, self.COLORS["text"])
        self.screen.blit(label, (260, 275))

        for character_id, character_name, rect in self._character_rects():
            selected = character_id == self.selected_character
            color = self.COLORS["selected"] if selected else self.COLORS["panel"]

            pygame.draw.rect(self.screen, color, rect, border_radius=18)
            pygame.draw.rect(
                self.screen,
                self.COLORS["border"],
                rect,
                3,
                border_radius=18,
            )

            image = self.images.get(character_id)
            if image:
                image_rect = image.get_rect(center=(rect.centerx, rect.y + 62))
                self.screen.blit(image, image_rect)
            else:
                fallback = self.font_big.render("?", True, self.COLORS["text"])
                self.screen.blit(fallback, fallback.get_rect(center=(rect.centerx, rect.y + 62)))

            name_surface = self.font_small.render(
                character_name,
                True,
                self.COLORS["button_text"] if selected else self.COLORS["text"],
            )
            self.screen.blit(
                name_surface,
                name_surface.get_rect(center=(rect.centerx, rect.bottom - 25)),
            )

    def _draw_start_button(self):
        """Draw the start game button."""
        rect = self._start_button_rect()
        mouse_pos = pygame.mouse.get_pos()
        color = self.COLORS["button_hover"] if rect.collidepoint(mouse_pos) else self.COLORS["button"]

        pygame.draw.rect(self.screen, color, rect, border_radius=18)

        text = self.font_big.render("Start Game", True, self.COLORS["button_text"])
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _character_rects(self):
        """Return the clickable rectangles for character selection."""
        rects = []
        start_x = 120
        y = 330
        width = 155
        height = 150
        gap = 30

        for index, (character_id, character_name) in enumerate(self.CHARACTERS):
            rect = pygame.Rect(start_x + index * (width + gap), y, width, height)
            rects.append((character_id, character_name, rect))

        return rects

    def _start_button_rect(self):
        """Return the rectangle representing the start button."""
        return pygame.Rect(350, 500, 200, 48)


class GardenRescuePygameUI:
    TILE_SIZE = 56
    MARGIN = 20
    SIDE_PANEL_WIDTH = 480
    FPS = 60

    COLORS = {
        "background": (245, 235, 245),
        "grid": (195, 160, 195),
        "tile": (218, 245, 180),
        "tile_alt": (205, 238, 165),
        "text": (45, 35, 50),
        "panel": (255, 245, 255),
        "white": (255, 255, 255),
        "danger": (190, 45, 70),
        "muted": (120, 105, 125),
        "success": (55, 145, 75),
        "flower": (255, 105, 180),
        "flower_center": (255, 230, 90),
        "garden": (110, 190, 120),
        "planted": (55, 145, 75),
        "obstacle": (95, 85, 105),
    }

    CHARACTER_COLORS = {
        "hello_kitty": (255, 145, 175),
        "kuromi": (115, 85, 135),
        "cinnamoroll": (125, 185, 255),
        "my_melody": (255, 160, 205),
    }

    def __init__(self, client, player_name):
        """Initialize the PyGame game interface."""
        self.client = client
        self.player_name = player_name
        self.running = True

        pygame.display.set_caption("Hello Kitty Garden Rescue")

        grid_pixels = self.TILE_SIZE * 6
        width = max(1150, self.MARGIN * 3 + grid_pixels + self.SIDE_PANEL_WIDTH)
        height = max(700, self.MARGIN * 2 + grid_pixels)

        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("arial", 30, bold=True)
        self.font = pygame.font.SysFont("arial", 20)
        self.font_small = pygame.font.SysFont("arial", 16)
        self.font_big = pygame.font.SysFont("arial", 34, bold=True)

        self.images = self._load_images()

    def _load_images(self):
        """Load character and tile textures used during gameplay."""
        def load(path, size):
            try:
                image = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(image, size)
            except Exception:
                return None

        character_size = (55, 55)
        tile_size = (48, 48)

        return {
            "characters": {
                "hello_kitty": load(
                    os.path.join(ASSETS_DIR, "characters", "hello_kitty.png"),
                    character_size,
                ),
                "kuromi": load(
                    os.path.join(ASSETS_DIR, "characters", "kuromi.png"),
                    character_size,
                ),
                "cinnamoroll": load(
                    os.path.join(ASSETS_DIR, "characters", "cinnamoroll.png"),
                    character_size,
                ),
                "my_melody": load(
                    os.path.join(ASSETS_DIR, "characters", "my_melody.png"),
                    character_size,
                ),
            },
            "tiles": {
                "grass": load(
                    os.path.join(ASSETS_DIR, "tiles", "grass.png"),
                    (self.TILE_SIZE, self.TILE_SIZE),
                ),
                "flower": load(
                    os.path.join(ASSETS_DIR, "tiles", "flower.png"),
                    tile_size,
                ),
                "garden_empty": load(
                    os.path.join(ASSETS_DIR, "tiles", "garden_empty.png"),
                    tile_size,
                ),
                "garden_full": load(
                    os.path.join(ASSETS_DIR, "tiles", "garden_full.png"),
                    tile_size,
                ),
                "obstacle": load(
                    os.path.join(ASSETS_DIR, "tiles", "obstacle.png"),
                    tile_size,
                ),
            },
        }

    def run(self):
        """Run the main graphical game loop."""
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(self.FPS)

        self.client.disconnect()
        pygame.quit()

    def _handle_events(self):
        """Process player keyboard and window events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.client.move("up")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.client.move("down")
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.client.move("left")
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.client.move("right")
                elif event.key == pygame.K_p:
                    self.client.pick()
                elif event.key == pygame.K_l:
                    self.client.plant()
                elif event.key == pygame.K_SPACE:
                    self.client.state()

    def _draw_end_game_popup(self, winner):
        """Display the victory or defeat popup overlay."""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        popup_width = 520
        popup_height = 260

        popup_rect = pygame.Rect(
            0,
            0,
            popup_width,
            popup_height,
        )
        popup_rect.center = self.screen.get_rect().center

        pygame.draw.rect(
            self.screen,
            (255, 245, 255),
            popup_rect,
            border_radius=24,
        )
        pygame.draw.rect(
            self.screen,
            (210, 150, 210),
            popup_rect,
            width=4,
            border_radius=24,
        )

        if winner == "players":
            title = "You Win!"
            subtitle = "All flowers were planted!"
            color = self.COLORS["success"]
        else:
            title = "Time Expired!"
            subtitle = "The garden was not completed."
            color = self.COLORS["danger"]

        title_surface = self.font_big.render(title, True, color)
        subtitle_surface = self.font.render(subtitle, True, self.COLORS["text"])
        hint_surface = self.font_small.render(
            "Press Q or Esc to exit",
            True,
            self.COLORS["muted"],
        )

        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(popup_rect.centerx, popup_rect.y + 80)),
        )
        self.screen.blit(
            subtitle_surface,
            subtitle_surface.get_rect(center=(popup_rect.centerx, popup_rect.y + 135)),
        )
        self.screen.blit(
            hint_surface,
            hint_surface.get_rect(center=(popup_rect.centerx, popup_rect.y + 195)),
        )

    def _draw_waiting_for_players_overlay(self, state):
        """Display the waiting overlay before the game starts."""
        connected_players = state.get("connected_players", 0)
        min_players = state.get("min_players_to_start", 2)

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((255, 240, 250, 150))
        self.screen.blit(overlay, (0, 0))

        popup_width = 560
        popup_height = 230

        popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
        popup_rect.center = self.screen.get_rect().center

        pygame.draw.rect(
            self.screen,
            (255, 250, 255),
            popup_rect,
            border_radius=24,
        )
        pygame.draw.rect(
            self.screen,
            (210, 150, 210),
            popup_rect,
            width=4,
            border_radius=24,
        )

        title_surface = self.font_big.render(
            "Waiting for players...",
            True,
            self.COLORS["text"],
        )

        count_surface = self.font.render(
            f"{connected_players} / {min_players} players connected",
            True,
            self.COLORS["danger"],
        )

        hint_surface = self.font_small.render(
            "The game starts automatically when enough players join.",
            True,
            self.COLORS["muted"],
        )

        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(popup_rect.centerx, popup_rect.y + 70)),
        )
        self.screen.blit(
            count_surface,
            count_surface.get_rect(center=(popup_rect.centerx, popup_rect.y + 125)),
        )
        self.screen.blit(
            hint_surface,
            hint_surface.get_rect(center=(popup_rect.centerx, popup_rect.y + 175)),
        )

    def _draw(self):
        """Render the complete game frame."""
        snapshot = self.client.game_state.snapshot()
        state = snapshot["state"]

        self.screen.fill(self.COLORS["background"])
        self._draw_board(state)
        self._draw_panel(snapshot)

        if not state.get("game_started", False):
            self._draw_waiting_for_players_overlay(state)

        if state.get("winner"):
            self._draw_end_game_popup(state.get("winner"))

        pygame.display.flip()

    def _draw_board(self, state):
        """Draw the game map and all game objects."""
        grid_width, grid_height = state.get("grid_size", [10, 10])

        for y in range(grid_height):
            for x in range(grid_width):
                self._draw_grass_tile(x, y)

        for x, y in state.get("obstacles", []):
            self._draw_obstacle(x, y)

        for spot in state.get("garden_spots", []):
            x, y = spot["position"]
            self._draw_garden(x, y, spot.get("occupied", False))

        for x, y in state.get("flowers", []):
            self._draw_flower(x, y)

        for pid, player in state.get("players", {}).items():
            x, y = player["position"]
            self._draw_player(
                x,
                y,
                pid,
                player.get("has_flower", False),
                player.get("character", "hello_kitty"),
            )

    def _draw_grass_tile(self, x, y):
        """Draw a grass tile at the specified coordinates."""
        rect = self._tile_rect(x, y)
        grass = self.images["tiles"].get("grass")

        if grass:
            self.screen.blit(grass, rect)
        else:
            color = self.COLORS["tile"] if (x + y) % 2 == 0 else self.COLORS["tile_alt"]
            pygame.draw.rect(self.screen, color, rect, border_radius=10)

        pygame.draw.rect(self.screen, self.COLORS["grid"], rect, width=1, border_radius=10)

    def _draw_panel(self, snapshot):
        """Draw the right-side information panel."""
        state = snapshot["state"]
        player_id = snapshot["player_id"]
        last_message = snapshot["last_message"]
        connected = snapshot["connected"]

        grid_pixels = self.TILE_SIZE * 10
        panel_x = self.MARGIN * 2 + grid_pixels

        panel_rect = pygame.Rect(
            panel_x,
            self.MARGIN,
            self.SIDE_PANEL_WIDTH,
            self.screen.get_height() - self.MARGIN * 2,
        )

        pygame.draw.rect(self.screen, self.COLORS["panel"], panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.COLORS["grid"], panel_rect, width=2, border_radius=16)

        x = panel_x + 18
        y = self.MARGIN + 18

        self._blit("Hello Kitty", self.font_title, x, y)
        y += 32
        self._blit("Garden Rescue", self.font_title, x, y)
        y += 50

        self._blit(f"Player: {self.player_name}", self.font, x, y)
        y += 26
        self._blit(f"ID: {player_id or '-'}", self.font, x, y)
        y += 26

        connection_text = "online" if connected else "offline"
        connection_color = self.COLORS["success"] if connected else self.COLORS["danger"]
        self._blit(f"Connection: {connection_text}", self.font, x, y, connection_color)
        y += 34

        time_left = state.get("time_remaining_seconds")
        winner = state.get("winner")

        carrying = False
        character = "-"

        if player_id in state.get("players", {}):
            current_player = state["players"][player_id]
            carrying = current_player.get("has_flower", False)
            character = current_player.get("character", "-")

        self._blit(
            f"Time: {time_left if time_left is not None else '-'}s",
            self.font_big,
            x,
            y,
        )
        y += 42

        self._blit(f"Character: {self._character_display_name(character)}", self.font, x, y)
        y += 28

        self._blit(f"Carrying flower: {'yes' if carrying else 'no'}", self.font, x, y)
        y += 24

        if winner:
            if winner == "players":
                message = "Players win!"
                color = self.COLORS["success"]
            else:
                message = "Time expired!"
                color = self.COLORS["danger"]

            self._blit(message, self.font_big, x, y, color)
            y += 48

        self._blit("Controls", self.font_title, x, y)
        y += 28

        controls = [
            "Arrow keys / WASD: move",
            "P: pick flower",
            "L: plant flower",
            "Space: request state",
            "Q / Esc: quit",
        ]

        for line in controls:
            self._blit(line, self.font_small, x, y)
            y += 20

        y += 14
        self._blit("Last message", self.font_title, x, y)
        y += 34

        for line in self._wrap_text(last_message, 42):
            self._blit(line, self.font_small, x, y)
            y += 22

        y += 12
        self._blit("Recent events", self.font_title, x, y)
        y += 32

        for event in state.get("recent_events", [])[-3:]:
            text = event.get("message", "")
            for line in self._wrap_text(text, 31):
                self._blit(line, self.font_small, x, y, self.COLORS["muted"])
                y += 16
            y += 3

    def _tile_rect(self, x, y):
        """Return the screen rectangle for a grid tile."""
        return pygame.Rect(
            self.MARGIN + x * self.TILE_SIZE,
            self.MARGIN + y * self.TILE_SIZE,
            self.TILE_SIZE,
            self.TILE_SIZE,
        )

    def _draw_obstacle(self, x, y):
        """Draw an obstacle tile."""
        rect = self._tile_rect(x, y)
        image = self.images["tiles"].get("obstacle")

        if image:
            image_rect = image.get_rect(center=rect.center)
            self.screen.blit(image, image_rect)
            return

        inner = rect.inflate(-18, -18)
        pygame.draw.rect(self.screen, self.COLORS["obstacle"], inner, border_radius=10)
        self._center_text("#", self.font_big, inner, self.COLORS["white"])

    def _draw_garden(self, x, y, occupied):
        """Draw a garden spot tile."""
        rect = self._tile_rect(x, y)
        key = "garden_full" if occupied else "garden_empty"
        image = self.images["tiles"].get(key)

        if image:
            image_rect = image.get_rect(center=rect.center)
            self.screen.blit(image, image_rect)
            return

        inner = rect.inflate(-16, -16)
        color = self.COLORS["planted"] if occupied else self.COLORS["garden"]
        pygame.draw.ellipse(self.screen, color, inner)
        self._center_text(
            "✓" if occupied else "G",
            self.font_big,
            inner,
            self.COLORS["white"],
        )

    def _draw_flower(self, x, y):
        """Draw a flower tile."""
        rect = self._tile_rect(x, y)
        image = self.images["tiles"].get("flower")

        if image:
            image_rect = image.get_rect(center=rect.center)
            self.screen.blit(image, image_rect)
            return

        cx, cy = rect.center

        for dx, dy in [(0, -14), (14, 0), (0, 14), (-14, 0)]:
            pygame.draw.circle(self.screen, self.COLORS["flower"], (cx + dx, cy + dy), 13)

        pygame.draw.circle(self.screen, self.COLORS["flower_center"], (cx, cy), 12)

    def _draw_player(self, x, y, pid, has_flower, character):
        """Draw a player character on the board."""
        rect = self._tile_rect(x, y).inflate(-8, -8)

        image = self.images["characters"].get(character)

        if image:
            image_rect = image.get_rect(center=rect.center)
            self.screen.blit(image, image_rect)
        else:
            color = self.CHARACTER_COLORS.get(character, (255, 145, 175))
            pygame.draw.ellipse(self.screen, color, rect)
            label = self._character_short_name(character)
            self._center_text(label, self.font_small, rect, self.COLORS["text"])

        id_surface = self.font_small.render(pid, True, self.COLORS["text"])
        self.screen.blit(id_surface, (rect.left + 2, rect.bottom - 14))

        if has_flower:
            flower = self.images["tiles"].get("flower")

            if flower:
                small_flower = pygame.transform.smoothscale(flower, (30, 30))
                self.screen.blit(small_flower, (rect.right - 24, rect.top - 4))
            else:
                pygame.draw.circle(
                    self.screen,
                    self.COLORS["flower"],
                    (rect.right - 5, rect.top + 5),
                    10,
                )

    def _character_short_name(self, character):
        """Return the short label for a character."""
        names = {
            "hello_kitty": "HK",
            "kuromi": "K",
            "cinnamoroll": "C",
            "my_melody": "MM",
        }
        return names.get(character, "?")

    def _character_display_name(self, character):
        """Return the display name for a character."""
        names = {
            "hello_kitty": "Hello Kitty",
            "kuromi": "Kuromi",
            "cinnamoroll": "Cinnamoroll",
            "my_melody": "My Melody",
        }
        return names.get(character, character)

    def _center_text(self, text, font, rect, color):
        """Draw centered text inside a rectangle."""
        surface = font.render(str(text), True, color)
        pos = surface.get_rect(center=rect.center)
        self.screen.blit(surface, pos)

    def _blit(self, text, font, x, y, color=None):
        """Render and display text at a screen position."""
        surface = font.render(str(text), True, color or self.COLORS["text"])
        self.screen.blit(surface, (x, y))

    def _wrap_text(self, text, max_chars):
        """Split long text into multiple lines."""
        words = str(text).split()
        lines = []
        current = ""

        for word in words:
            if len(current) + len(word) + 1 <= max_chars:
                current = f"{current} {word}".strip()
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines or [""]


def main():
    """Start the PyGame client application."""
    parser = argparse.ArgumentParser(
        description="Hello Kitty Garden Rescue PyGame client"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_SERVER_ADDRESS,
        help="Server address/IP",
    )

    args = parser.parse_args()

    pygame.init()

    lobby = LobbyScreen()
    player_name, character = lobby.run()

    if not player_name:
        pygame.quit()
        return

    client = GameClientStub(
        server_address=args.host,
        print_broadcast=False,
    )
    client.connect(player_name, character)

    ui = GardenRescuePygameUI(client, player_name)
    ui.run()


if __name__ == "__main__":
    main()