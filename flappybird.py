import time
import random
import yaml
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# load the config
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

pygame.font.init()
pygame.mixer.init()

# set shape of window
WIN_WIDTH = 500
WIN_HEIGHT = 800

# load images
# pygame.transform.scale2x scales the image to be 2 times bigger
BIRD_IMG = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
COUNTDOWN_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "countdown.png")))
GAMEOVER_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "game_over.png")))
MODES_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "modes.png")))

if cfg["screen"]["ranked_confetti"]:
    RANKED_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "ranked.png")))
elif not cfg["screen"]["ranked_confetti"]:
    RANKED_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "ranked2.png")))

if cfg["screen"]["credits"]:
    HOME_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "home.png")))
elif not cfg["screen"]["credits"]:
    HOME_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "home2.png")))


# load music and sounds
pygame.mixer.music.load((os.path.join("sounds", "FlappyBirdThemeSong.mp3")))

if cfg["sounds"]["music"]:
    pygame.mixer.music.play(-1)

JUMP_SOUND = pygame.mixer.Sound((os.path.join("sounds", "jump.mp3")))
DEAD_SOUND = pygame.mixer.Sound((os.path.join("sounds", "dead.mp3")))
SCORE_SOUND = pygame.mixer.Sound((os.path.join("sounds", "point.mp3")))

# initialise text font and size
STAT_FONT = pygame.font.SysFont("comfortaa", 50)
COUNT_FONT = pygame.font.SysFont("comfortaa", 100)
INPUT_FONT = pygame.font.SysFont("comfortaa", 50)
RANKED_FONT = pygame.font.SysFont("comfortaa", 50)

class Bird:
    IMGS = BIRD_IMG
    ROTATION = 25  # in degrees
    ROT_VEL = 20  # how fast is it going to rotate
    ANIMATION_TIME = 5  # how long do we want to show a move of the bird

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0  # when was the last jump in ticks
        self.vel = 0
        self.height = self.y
        self.img_count = 0  # to know what picture should be shown
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2  # equation to know how high we jump ==> 2:20 min, https://www.youtube.com/watch?v=ps55secj7iU&list=PLzMcBGfZo4-lwGZWXz5Qgta_YNX3_vLS2&index=2

        if d >= 16:  # kind of a terminal velocity (it cant go further after 16)
            d = 16

        if d < 0:  # for jumping nicely
            d -= 2

        self.y = self.y + d / 2

        # TILTING DOESNT WORK YET
        """
        if d < 0 or self.y < self.height + 50:  # only start falling after you reached your maximum height (used for tilts)
            if self.tilt < self.ROTATION:
                self.tilt = self.ROTATION

            else: 
                if self.tilt > -90:
                    self.tilt -= self.ROT_VEL"""

    def draw(self, win):
        self.img_count += 1

        # animate the bird (this is for flapping the wings)
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # don't flap its wings when it's tilted down
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # rotate the bird, so it looks tilted when in an angle
        # HAVE TO FIX
        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_img, new_rect.topleft)  # blit = draw

    # collisions
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = cfg["game"]["pipe_gap"]
    VEL = cfg["game"]["pipe_vel"]  # bird doesn't move only the pipes do

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False  # has the bird passed a pipe
        self.set_height()

    def set_height(self):
        # random value for how high top pipe should be
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL  # for every frame bring the pipe VEl steps closer to the bird

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # calculate offset ==> how far are the pixels apart
        top_offset = (self.x - round(bird.x), self.top - round(bird.y))
        bottom_offset = (self.x - round(bird.x), self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point is not None:
            return True

        return False


class BgAndBase:
    VEL = cfg["game"]["pipe_vel"]  # Needs to be the same as the VEl of pipes otherwise they don't move at the same speed
    F_WIDTH = BASE_IMG.get_width()
    F_IMG = BASE_IMG
    B_WIDTH = BG_IMG.get_width()
    B_IMG = BG_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.F_WIDTH

        self.y2 = 0
        self.x3 = 0
        self.x4 = self.B_WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # using 2 images to make it look like one and so to move the ground
        if self.x1 + self.F_WIDTH < 0:
            self.x1 = self.x2 + self.F_WIDTH

        if self.x2 + self.F_WIDTH < 0:
            self.x2 = self.x1 + self.F_WIDTH

        self.x3 -= self.VEL
        self.x4 -= self.VEL

        # using 2 images to make it look like one and so to move the ground
        if self.x3 + self.B_WIDTH < 0:
            self.x3 = self.x4 + self.B_WIDTH

        if self.x4 + self.B_WIDTH < 0:
            self.x4 = self.x3 + self.B_WIDTH

    def draw(self, win):
        win.blit(self.B_IMG, (self.x3, self.y2))
        win.blit(self.B_IMG, (self.x4, self.y2))
        win.blit(self.B_IMG, (self.x3, self.y2))
        win.blit(self.B_IMG, (self.x4, self.y2))

        win.blit(self.F_IMG, (self.x1, self.y))
        win.blit(self.F_IMG, (self.x2, self.y))
        win.blit(self.F_IMG, (self.x1, self.y))
        win.blit(self.F_IMG, (self.x2, self.y))

class Button:
    def __init__(self, text, x_pos, y_pos, width, height, enabled):
        self.text = text
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.width = width
        self.height = height
        self.enabled = enabled
        self.draw()

    def draw(self):
        text = STAT_FONT.render(self.text, True, "black")
        button_rect = pygame.rect.Rect((self.x_pos, self.y_pos), (self.width, self.height))
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.draw.rect(win, "white", button_rect, 0, 5)

        win.blit(text, (self.x_pos, self.y_pos))

    def click(self):
        mouse_pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()[0]
        button_rect = pygame.rect.Rect((self.x_pos, self.y_pos), (self.width, self.height))

        if left_click and button_rect.collidepoint(mouse_pos) and self.enabled:
            return True
        else:
            return False

def draw_window(win, bird, pipes, base, score):
    base.draw(win)

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render(f"Score: {score}", 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    bird.draw(win)
    pygame.display.update()

class GameState:
    def __init__(self):
        self.highscore = None
        self.sorted_scores = None
        self.scores = []

    def home_menu(self):
        # get highscore from highscore file
        with open("highscores.txt", "r") as f:
            for line in f.readlines():
                score, name = list(line.split(","))
                name = name.strip()
                self.scores.append([int(score), name])

        self.sorted_scores = sorted(self.scores, key=lambda x: x[0], reverse=True)
        self.highscore = self.sorted_scores[0][0]
        
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

        start_button = Button("START", 104, 550, 298, 66, True)
        ranked_button = Button("RANKED", 176, 448, 148, 76, True)

        run = True
        while run:
            # keeps track of anything happening (clicking mouse, keyboard, etc.)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            if start_button.click():
                return "play"

            if ranked_button.click():
                return "ranked"

            win.blit(HOME_IMG, (0, 0))
            pygame.display.update()

    def ranked(self):
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        back_button = Button("BACK", 156, 696, 200, 66, True)

        if len(self.sorted_scores) >= 3:

            first_place = self.sorted_scores[0][1]
            second_place = self.sorted_scores[1][1]
            third_place = self.sorted_scores[2][1]

            first_place_score = self.sorted_scores[0][0]
            second_place_score = self.sorted_scores[1][0]
            third_place_score = self.sorted_scores[2][0]

        else:
            first_place = "N/A"
            second_place = "N/A"
            third_place = "N/A"

            first_place_score = "N/A"
            second_place_score = "N/A"
            third_place_score = "N/A"

        run = True
        while run:
            # keeps track of anything happening (clicking mouse, keyboard, etc.)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                if back_button.click():
                    run = False

            first_place_text = RANKED_FONT.render(first_place, True, "black")
            second_place_text = RANKED_FONT.render(second_place, True, "black")
            third_place_text = RANKED_FONT.render(third_place, True, "black")

            first_place_score_text = RANKED_FONT.render(str(first_place_score), True, "white")
            second_place_score_text = RANKED_FONT.render(str(second_place_score), True, "white")
            third_place_score_text = RANKED_FONT.render(str(third_place_score), True, "white")

            win.blit(RANKED_IMG, (0, 0))

            win.blit(first_place_text, (165, 375))
            win.blit(second_place_text, (345, 440))
            win.blit(third_place_text, (25, 460))

            win.blit(first_place_score_text, (225, 340))
            win.blit(second_place_score_text, (390, 405))
            win.blit(third_place_score_text, (70, 425))

            pygame.display.update()

    def mode_selection(self):
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

        back_button = Button("BACK", 156, 696, 200, 66, True)
        easy_button = Button("BACK", 156, 280, 200, 66, True)
        normal_button = Button("BACK", 156, 380, 200, 66, True)
        impossible_button = Button("BACK", 156, 470, 200, 66, True)

        nicht_verfuegbar = STAT_FONT.render("Nicht Verfügbar", True, "red")

        clock = pygame.time.Clock()

        self.username = ""
        username_rect = pygame.Rect(126, 64, 200, 66)
        active = False

        run = True
        while run:
            # running on 30 fps
            clock.tick(30)

            # keeps track of anything happening (clicking mouse, keyboard, etc.)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                if back_button.click():
                    return "back"

                if easy_button.click() and cfg["difficulties"]["easy_mode_on"]:
                    return "easy"
                elif easy_button.click() and not cfg["difficulties"]["easy_mode_on"]:
                    win.blit(nicht_verfuegbar, (135, 225))
                    pygame.display.update()
                    time.sleep(1)

                if normal_button.click() and cfg["difficulties"]["normal_mode_on"]:
                    return "normal"
                elif normal_button.click() and not cfg["difficulties"]["normal_mode_on"]:
                    win.blit(nicht_verfuegbar, (135, 225))
                    pygame.display.update()
                    time.sleep(1)

                if impossible_button.click() and cfg["difficulties"]["impossible_mode_on"]:
                    return "impossible"
                elif impossible_button.click() and not cfg["difficulties"]["impossible_mode_on"]:
                    win.blit(nicht_verfuegbar, (135, 225))
                    pygame.display.update()
                    time.sleep(1)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if username_rect.collidepoint(event.pos):
                        active = True
                    else:
                        active = False

                if event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_BACKSPACE or len(self.username) > 10:
                            self.username = self.username[:-1]
                        else:
                            self.username += event.unicode

            pygame.draw.rect(win, "white", username_rect, 1)
            username_text = INPUT_FONT.render(self.username, True, "black")

            win.blit(MODES_IMG, (0, 0))
            win.blit(username_text, (username_rect.x + 15, username_rect.y + 15))
            pygame.display.update()

    def countdown(self):
        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

        clock = pygame.time.Clock()

        run = True
        while run:
            # running on 30 fps
            clock.tick(30)

            # keeps track of anything happening (clicking mouse, keyboard, etc.)
            for i in range(3):
                text = COUNT_FONT.render(f"{3 - i}", True, "white")
                win.blit(COUNTDOWN_IMG, (0, 0))
                win.blit(text, (225, 200))
                pygame.display.update()
                time.sleep(1)

            run = False

            win.blit(COUNTDOWN_IMG, (0, 0))
            pygame.display.update()

    def main_game(self, FPS, difficulty):
        bird = Bird(230, 350)
        pipes = [Pipe(700)]
        base = BgAndBase(730)

        win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        clock = pygame.time.Clock()
        self.score = 0

        # main game loop
        run = True
        while run:
            # running on 30 fps
            if difficulty == "easy":
                # disables mouse motion but somehow stil counts when going in circles with the mouse
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                clock.tick(FPS)
            elif difficulty == "normal":
                # disables mouse motion but somehow stil counts when going in circles with the mouse
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                cfg["game"]["pipe_vel"] = 25
            elif difficulty == "impossible":
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                cfg["game"]["pipe_vel"] = 25
                cfg["game"]["pipe_gap"] = 100

            # keeps track of anything happening (clicking mouse, keyboard, etc.)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if pygame.K_SPACE:
                    if cfg["sounds"]["sounds"]:
                        JUMP_SOUND.play()
                    bird.jump()

            bird.move()
            add_pipe = False
            rem = []
            for pipe in pipes:
                if pipe.collide(bird):
                    run = False

                # pipe is off-screen
                if pipe.x + pipe.PIPE_TOP.get_height() < 0:
                    rem.append(pipe)

                if not pipe.passed and pipe.x < bird.x:
                    if cfg["sounds"]["sounds"]:
                        SCORE_SOUND.play()
                    pipe.passed = True
                    add_pipe = True

                pipe.move()

            if add_pipe:
                self.score += cfg["game"]["score_per_pipe"]
                pipes.append(Pipe(700))

            for r in rem:
                pipes.remove(r)

            if bird.y + bird.img.get_height() >= 730:
                run = False

            # GET FASTERRRRRR
            if self.score % 5 == 0 and self.score != 0 and FPS != 0 and pipe.passed:
                # every 10 points make the game a little bit faster
                FPS += cfg["game"]["fps_increase"]

            base.move()
            draw_window(win, bird, pipes, base, self.score)

            pygame.display.update()

        if cfg["sounds"]["sounds"]:
            DEAD_SOUND.play()

        win.blit(GAMEOVER_IMG, (20, 200))

        # if a highscore is detected then write it down in the highscore file
        if self.score > self.highscore:
            with open("highscores.txt", "a") as f:
                if self.username == "":
                    f.write(str(f"\n{self.score}, Anonym"))
                else:
                    f.write(str(f"\n{self.score}, {self.username}"))

            final_score = STAT_FONT.render(f"New Highscore: {self.score}", True, "white")
            win.blit(final_score, (100, 300))

        else:
            final_score = STAT_FONT.render(f"Score: {self.score}", True, "white")
            win.blit(final_score, (175, 300))

        pygame.display.update()
        time.sleep(3)


def game_loop():
    game = GameState()
    while True:
        next_window = game.home_menu()
        if next_window == "play":
            selection = game.mode_selection()

            if selection == "easy":
                if cfg["screen"]["countdown_enabled"]:
                    game.countdown()
                game.main_game(cfg["game"]["fps"], "easy")

            elif selection == "normal":
                if cfg["screen"]["countdown_enabled"]:
                    game.countdown()
                game.main_game(cfg["game"]["fps"], "normal")

            elif selection == "impossible":
                if cfg["screen"]["countdown_enabled"]:
                    game.countdown()
                game.main_game(cfg["game"]["fps"], "impossible")

            elif selection == "back":
                break

        elif next_window == "ranked":
            game.ranked()
            break


while True:
    game_loop()
