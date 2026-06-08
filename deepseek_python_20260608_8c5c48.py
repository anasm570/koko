import pygame
import random
import math
import sys

# تهيئة pygame
pygame.init()
pygame.mixer.init()

# إعدادات الشاشة
WIDTH, HEIGHT = 1050, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("✨ Cosmic Collector | لعبة فضاء")

# الألوان
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 100, 0)
RED = (255, 50, 50)
GREEN = (0, 255, 100)
DARK_BLUE = (10, 20, 50)

# متغيرات اللعبة
clock = pygame.time.Clock()
FPS = 60
score = 0
health = 5
high_score = 0
game_active = True

# تحميل أفضل نتيجة من ملف (إن وجد)
try:
    with open("highscore.txt", "r") as f:
        high_score = int(f.read())
except:
    high_score = 0

# فئة السفينة
class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 26
        self.speed_x = 0
        self.max_speed = 7.5
        self.acceleration = 0.65
        self.friction = 0.96
        self.boost_active = False
        self.boost_remaining = 0
        self.boost_cooldown = 0

    def update(self, left, right, boost):
        # الحركة الأفقية
        if left:
            self.speed_x = max(-self.max_speed, self.speed_x - self.acceleration)
        if right:
            self.speed_x = min(self.max_speed, self.speed_x + self.acceleration)
        self.speed_x *= self.friction
        self.x += self.speed_x
        self.x = max(self.radius + 10, min(WIDTH - self.radius - 10, self.x))

        # الدفع المؤقت
        if boost and self.boost_cooldown == 0 and not self.boost_active:
            self.boost_active = True
            self.boost_remaining = 18
            self.boost_cooldown = 55
        if self.boost_active and self.boost_remaining > 0:
            self.speed_x += 2.4 if self.speed_x > 0 else -2.4
            self.speed_x = max(-self.max_speed - 3, min(self.max_speed + 3, self.speed_x))
            self.boost_remaining -= 1
            if self.boost_remaining <= 0:
                self.boost_active = False
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1

    def draw(self, screen):
        # تأثير الظل
        pygame.draw.circle(screen, (0, 200, 255), (int(self.x), int(self.y+5)), self.radius+2, 0)
        # جسم السفينة
        points = []
        nose = (self.x, self.y - 30)
        left_wing_top = (self.x - 22, self.y - 8)
        left_wing_bottom = (self.x - 26, self.y + 10)
        left_mid = (self.x - 12, self.y + 4)
        left_tail = (self.x - 12, self.y + 20)
        tail = (self.x, self.y + 32)
        right_tail = (self.x + 12, self.y + 20)
        right_mid = (self.x + 12, self.y + 4)
        right_wing_bottom = (self.x + 26, self.y + 10)
        right_wing_top = (self.x + 22, self.y - 8)
        points = [nose, left_wing_top, left_wing_bottom, left_mid, left_tail, tail, right_tail, right_mid, right_wing_bottom, right_wing_top]
        pygame.draw.polygon(screen, (100, 180, 255), points)
        pygame.draw.polygon(screen, (60, 120, 200), points, 2)
        # الأجنحة الخارجية
        left_wing = [(self.x - 22, self.y - 5), (self.x - 38, self.y + 2), (self.x - 28, self.y + 6)]
        right_wing = [(self.x + 22, self.y - 5), (self.x + 38, self.y + 2), (self.x + 28, self.y + 6)]
        pygame.draw.polygon(screen, (150, 200, 255), left_wing)
        pygame.draw.polygon(screen, (150, 200, 255), right_wing)
        # قمرة القيادة
        pygame.draw.ellipse(screen, (200, 230, 255), (self.x-10, self.y-18, 20, 14))
        pygame.draw.ellipse(screen, (0, 0, 40), (self.x-6, self.y-16, 12, 10))
        # عيون
        pygame.draw.circle(screen, WHITE, (int(self.x-4), int(self.y-14)), 3)
        pygame.draw.circle(screen, WHITE, (int(self.x+4), int(self.y-14)), 3)

        # تأثير الدفع
        if self.boost_active or self.boost_remaining > 0:
            for i in range(3):
                y_offset = 20 + i*5
                w = 8 - i*2
                h = 12 - i*3
                pygame.draw.ellipse(screen, (255, 120, 0), (self.x - w//2, self.y + y_offset, w, h))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

# فئة البلورة (طاقة)
class Crystal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.speed = random.uniform(2.5, 3.8)
        self.color = (60, 130, 250)
        self.glow = (0, 100, 200)

    def update(self):
        self.y += self.speed

    def draw(self, screen):
        # تأثير توهج
        for i in range(3):
            alpha = 50 - i*15
            pygame.draw.circle(screen, (self.glow[0], self.glow[1], self.glow[2], alpha), (int(self.x), int(self.y)), self.radius + i*2)
        # البلورة
        rect = pygame.Rect(self.x-9, self.y-9, 18, 18)
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, WHITE, (self.x-3, self.y-3, 6, 6))
        # رمز الطاقة
        font = pygame.font.SysFont("monospace", 16)
        text = font.render("✦", True, (255, 255, 200))
        screen.blit(text, (self.x-6, self.y-6))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

# فئة الكويكب
class Asteroid:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = random.uniform(2.0, 3.5)
        self.color1 = (180, 80, 30)
        self.color2 = (130, 50, 20)
        self.has_crater = random.choice([True, False])

    def update(self):
        self.y += self.speed

    def draw(self, screen):
        # تدرج شعاعي
        for i in range(3):
            r = self.radius - i*3
            if r < 2: break
            color = (self.color1[0] - i*20, self.color1[1] - i*15, self.color1[2] - i*5)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), r)
        # حفر
        if self.has_crater:
            pygame.draw.ellipse(screen, (70, 30, 10), (self.x-7, self.y-5, 10, 8))
            pygame.draw.ellipse(screen, (50, 20, 5), (self.x+4, self.y+2, 8, 7))
        # نتوءات
        for _ in range(3):
            ang = random.uniform(0, math.pi*2)
            dx = math.cos(ang) * (self.radius-3)
            dy = math.sin(ang) * (self.radius-3)
            pygame.draw.circle(screen, (100, 60, 20), (int(self.x+dx), int(self.y+dy)), 3)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

# فئة الجسيمات
class Particle:
    def __init__(self, x, y, vx, vy, color, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(4 * (self.life / self.max_life)))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

# دوال مساعدة
def add_particles(x, y, color, count):
    for _ in range(count):
        vx = random.uniform(-3, 3)
        vy = random.uniform(-2, 2)
        life = random.randint(15, 30)
        particles.append(Particle(x, y, vx, vy, color, life))

def spawn_crystal():
    x = random.randint(40, WIDTH-40)
    y = -20
    crystals.append(Crystal(x, y))

def spawn_asteroid():
    radius = random.randint(16, 28)
    x = random.randint(radius+10, WIDTH-radius-10)
    y = -radius
    asteroids.append(Asteroid(x, y, radius))

# إنشاء كائنات اللعبة
ship = Ship(WIDTH//2, HEIGHT - 90)
crystals = []
asteroids = []
particles = []

# مؤقتات التكاثر
crystal_timer = 0
asteroid_timer = 0
base_crystal_delay = 30
base_asteroid_delay = 40

# نجوم الخلفية (ثلاث طبقات)
stars = []
for _ in range(200):
    stars.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "radius": random.uniform(1, 2.5),
        "speed": random.uniform(0.3, 1.2),
        "alpha": random.uniform(0.3, 0.8)
    })

# دوال الرسم الأساسية
def draw_stars():
    for s in stars:
        pygame.draw.circle(screen, (255, 255, 200), (int(s["x"]), int(s["y"])), int(s["radius"]))
        s["y"] += s["speed"]
        if s["y"] > HEIGHT:
            s["y"] = 0
            s["x"] = random.randint(0, WIDTH)

def draw_text(text, size, x, y, color=CYAN):
    font = pygame.font.SysFont("Arial", size)
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# حلقة اللعبة الرئيسية
running = True
while running:
    # معالجة الأحداث (دعم اللمس عبر أحداث الماوس)
    left_pressed = False
    right_pressed = False
    boost_pressed = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # أحداث اللمس / الماوس
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if x < WIDTH // 3:
                left_pressed = True
            elif x > 2 * WIDTH // 3:
                right_pressed = True
            else:
                boost_pressed = True
        # أحداث لوحة المفاتيح
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                left_pressed = True
            elif event.key == pygame.K_RIGHT:
                right_pressed = True
            elif event.key == pygame.K_UP:
                boost_pressed = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                left_pressed = False
            elif event.key == pygame.K_RIGHT:
                right_pressed = False

    # تحديث السفينة (تمرير الأزرار المضغوطة)
    ship.update(left_pressed, right_pressed, boost_pressed)

    # تحديث النجوم
    draw_stars()

    # تحديث الجسيمات
    for p in particles[:]:
        p.update()
        if p.life <= 0:
            particles.remove(p)

    # توليد العناصر
    if crystal_timer <= 0:
        spawn_crystal()
        crystal_timer = max(18, base_crystal_delay - score // 150)
    else:
        crystal_timer -= 1

    if asteroid_timer <= 0:
        spawn_asteroid()
        asteroid_timer = max(22, base_asteroid_delay - score // 120)
    else:
        asteroid_timer -= 1

    # تحديث البلورات والتصادم
    for c in crystals[:]:
        c.update()
        if c.y + c.radius > HEIGHT + 50:
            crystals.remove(c)
            continue
        if ship.get_rect().colliderect(c.get_rect()):
            score += 1
            add_particles(c.x, c.y, (50, 150, 250), 10)
            crystals.remove(c)

    # تحديث الكويكبات والتصادم
    for a in asteroids[:]:
        a.update()
        if a.y + a.radius > HEIGHT + 100:
            asteroids.remove(a)
            continue
        if ship.get_rect().colliderect(a.get_rect()):
            health -= 1
            add_particles(a.x, a.y, (255, 80, 80), 15)
            asteroids.remove(a)
            if health <= 0:
                game_active = False

    # رسم كل شيء
    screen.fill(DARK_BLUE)
    draw_stars()

    for a in asteroids:
        a.draw(screen)
    for c in crystals:
        c.draw(screen)
    ship.draw(screen)
    for p in particles:
        p.draw(screen)

    # عرض النصوص
    draw_text(f"الطاقة: {score}", 30, 20, 20, CYAN)
    draw_text(f"الصحة: {health}", 30, 20, 60, (255, 100, 100))
    draw_text(f"أفضل: {high_score}", 30, WIDTH-150, 20, (255, 200, 100))
    if ship.boost_cooldown > 0:
        draw_text("إعادة شحن الدفع", ship.x-50, ship.y-45, (255, 150, 0))

    # نهاية اللعبة
    if not game_active:
        # رسم طبقة شفافة
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        draw_text("GAME OVER", 60, WIDTH//2-120, HEIGHT//2-40, (255, 80, 80))
        draw_text(f"نتيجتك: {score}", 40, WIDTH//2-80, HEIGHT//2+20, WHITE)
        draw_text("اضغط أي زر أو المس الشاشة لإعادة التشغيل", 25, WIDTH//2-200, HEIGHT//2+80, CYAN)
        pygame.display.flip()

        # انتظار إعادة التشغيل
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    # إعادة تعيين اللعبة
                    score = 0
                    health = 5
                    game_active = True
                    crystals.clear()
                    asteroids.clear()
                    particles.clear()
                    ship = Ship(WIDTH//2, HEIGHT - 90)
                    crystal_timer = 5
                    asteroid_timer = 10
                    waiting = False
                    break
        continue

    # تحديث أفضل نتيجة
    if score > high_score:
        high_score = score
        with open("highscore.txt", "w") as f:
            f.write(str(high_score))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()