#!/usr/bin/env python3
"""SUNSAIL — neon thermal-pennon arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/SUNSAIL_ElbowOS.mp4")
TITLE, HANDLE = "SUNSAIL", "x.com/ElbowOS"

NAVY = (8, 10, 36)
INK = (6, 8, 28)
TEAL = (20, 170, 190)
PEACH = (255, 150, 92)
GOLD = (255, 204, 64)
MAG = (255, 64, 148)
CYAN = (70, 240, 255)
WHITE = (250, 246, 255)
STORM = (90, 40, 180)
LIME = (160, 255, 90)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 58, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 36, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 24)
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.t = self.score = self.combo = self.flash = self.banner = 0
        self.banner_txt = ""
        self.x, self.y = W * 0.5, H * 0.62
        self.vx = self.vy = 0.0
        self.tilt = 0.0
        self.wind = 0.0
        self.gust_t = 0
        self.trail, self.sparks, self.motes, self.streaks = [], [], [], []
        self.hoops, self.storms = [], []
        self.passed = set()
        for i in range(8):
            self.spawn_hoop(-180 - i * 280)
        for i in range(5):
            self.spawn_storm(-400 - i * 420)
        for _ in range(90):
            self.streaks.append([
                random.randrange(W), random.randrange(H),
                random.uniform(4, 14), random.choice((CYAN, TEAL, PEACH, WHITE)),
            ])
        for _ in range(40):
            self.motes.append([
                random.randrange(80, W - 80), random.randrange(H),
                random.uniform(1.2, 3.0), random.choice((GOLD, PEACH, CYAN)),
            ])

    def spawn_hoop(self, y):
        self.hoops.append({
            "x": random.randint(220, W - 220),
            "y": y,
            "r": random.choice((78, 88, 98)),
            "col": random.choice((MAG, CYAN, GOLD, PEACH)),
            "id": random.random(),
        })

    def spawn_storm(self, y):
        self.storms.append({
            "x": random.randint(140, W - 140),
            "y": y,
            "r": random.randint(26, 42),
            "spin": random.uniform(0, 6.28),
        })

    def burst(self, x, y, col, n=14):
        for _ in range(n):
            a = random.uniform(0, 6.2832)
            sp = random.uniform(2, 11)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 16, col])

    def steer(self, ax):
        self.vx += ax * 1.15
        self.tilt += ax * 0.08

    def autoplay(self):
        nxt = None
        for h in self.hoops:
            if h["y"] < self.y - 20 and h["id"] not in self.passed:
                if nxt is None or h["y"] > nxt["y"]:
                    nxt = h
        target = nxt["x"] if nxt else W * 0.5
        target -= self.wind * 18
        dx = target - self.x
        if abs(dx) > 8:
            self.steer(1 if dx > 0 else -1)
        else:
            self.steer(-self.vx * 0.08)
        for s in self.storms:
            if abs(s["y"] - self.y) < 160 and abs(s["x"] - self.x) < 90:
                self.steer(-1 if s["x"] > self.x else 1)

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.banner = max(0, self.banner - 1)
        self.gust_t -= 1
        if self.gust_t <= 0:
            self.wind = random.uniform(-1.6, 1.6)
            self.gust_t = random.randint(28, 55)
        self.vx += self.wind * 0.18
        self.vx *= 0.92
        self.tilt = self.tilt * 0.86 + self.vx * 0.04
        self.x = max(70, min(W - 70, self.x + self.vx))
        self.y = H * 0.62 + math.sin(self.t * 0.07) * 18
        scroll = 11 + min(6, self.score / 400)
        self.trail.append((self.x, self.y + 28, self.t))
        self.trail = [p for p in self.trail if self.t - p[2] < 18]
        for st in self.streaks:
            st[1] += st[2] + scroll * 0.35
            if st[1] > H + 20:
                st[0], st[1] = random.randrange(W), -20
        for m in self.motes:
            m[1] += m[2] + scroll * 0.5
            if m[1] > H + 10:
                m[0], m[1] = random.randrange(80, W - 80), -16
            if abs(m[0] - self.x) < 36 and abs(m[1] - self.y) < 36:
                self.score += 12
                self.burst(m[0], m[1], m[3], 6)
                m[1] = -40
                m[0] = random.randrange(80, W - 80)
        for h in self.hoops:
            h["y"] += scroll
        for s in self.storms:
            s["y"] += scroll * 0.95
            s["spin"] += 0.12
            s["x"] += math.sin(s["spin"]) * 1.4
        self.hoops = [h for h in self.hoops if h["y"] < H + 120]
        self.storms = [s for s in self.storms if s["y"] < H + 80]
        while len(self.hoops) < 8:
            top = min(h["y"] for h in self.hoops) if self.hoops else 0
            self.spawn_hoop(top - random.randint(240, 320))
        while len(self.storms) < 5:
            top = min(s["y"] for s in self.storms) if self.storms else 0
            self.spawn_storm(top - random.randint(300, 480))
        for h in self.hoops:
            if h["id"] in self.passed:
                continue
            if abs(h["y"] - self.y) < 22:
                dist = abs(h["x"] - self.x)
                if dist < h["r"] - 8:
                    self.combo += 1
                    self.score += 80 + self.combo * 20
                    self.banner, self.banner_txt = 16, ("THREAD", "THERMAL", "SUNSHOT", "PENNON")[min(self.combo, 4) - 1]
                    self.flash = 7
                    self.burst(h["x"], h["y"], h["col"], 20)
                    self.passed.add(h["id"])
                else:
                    self.combo = 0
                    self.score = max(0, self.score - 15)
                    self.passed.add(h["id"])
        for s in self.storms:
            if (self.x - s["x"]) ** 2 + (self.y - s["y"]) ** 2 < (s["r"] + 22) ** 2:
                self.combo = 0
                self.vx += 8 if self.x > s["x"] else -8
                self.burst(self.x, self.y, STORM, 10)
                self.score = max(0, self.score - 25)
                s["y"] = H + 200
        for sp in self.sparks:
            sp[0] += sp[2]
            sp[1] += sp[3] + scroll * 0.2
            sp[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]

    def draw_bg(self, surf):
        for i in range(24):
            t = i / 23
            r = int(8 + 70 * t)
            g = int(10 + 40 * t)
            b = int(40 + 20 * (1 - t))
            pygame.draw.rect(surf, (r, g, b), (0, int(i * H / 24), W, H // 24 + 2))
        pygame.draw.circle(surf, (255, 120, 50), (W // 2, 210), 92)
        pygame.draw.circle(surf, GOLD, (W // 2, 210), 62)
        pygame.draw.circle(surf, WHITE, (W // 2 - 16, 196), 14)
        for st in self.streaks:
            pygame.draw.line(surf, st[3], (st[0], st[1]), (st[0], st[1] + st[2] * 2.2), 2)
        wx = int(W * 0.5 + self.wind * 90)
        pygame.draw.polygon(surf, PEACH, [(W // 2, 320), (wx, 348), (W // 2, 360)])

    def draw_hoop(self, surf, h):
        col = h["col"]
        y = int(h["y"])
        x = int(h["x"])
        pygame.draw.ellipse(surf, col, (x - h["r"], y - 18, h["r"] * 2, 36), 8)
        pygame.draw.ellipse(surf, WHITE, (x - h["r"] + 10, y - 10, h["r"] * 2 - 20, 20), 2)
        glow = pygame.Surface((h["r"] * 2 + 20, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*col, 40), glow.get_rect())
        surf.blit(glow, (x - h["r"] - 10, y - 25))

    def draw_sail(self, surf):
        ang = self.tilt
        ca, sa = math.cos(ang), math.sin(ang)
        def rot(px, py):
            return (self.x + px * ca - py * sa, self.y + px * sa + py * ca)
        nose = rot(0, -56)
        left = rot(-34, 38)
        right = rot(34, 38)
        keel = rot(0, 52)
        for i, (tx, ty, age) in enumerate(self.trail):
            pygame.draw.circle(surf, (255, int(160 + i * 4), 70), (int(tx), int(ty)), max(3, 10 - i // 3))
        pygame.draw.polygon(surf, GOLD, [nose, left, keel, right])
        pygame.draw.polygon(surf, PEACH, [nose, rot(-12, 8), rot(12, 8)])
        pygame.draw.polygon(surf, WHITE, [nose, left, right], 2)
        pygame.draw.circle(surf, MAG, (int(self.x), int(self.y + 8)), 7)

    def draw(self, surf):
        self.draw_bg(surf)
        for m in self.motes:
            pygame.draw.circle(surf, m[3], (int(m[0]), int(m[1])), 5)
        for s in self.storms:
            pygame.draw.circle(surf, STORM, (int(s["x"]), int(s["y"])), s["r"])
            pygame.draw.circle(surf, MAG, (int(s["x"]), int(s["y"])), max(6, s["r"] // 3), 2)
            arm = s["r"] + 8
            pygame.draw.line(surf, (180, 90, 255),
                             (s["x"] + math.cos(s["spin"]) * arm, s["y"] + math.sin(s["spin"]) * arm),
                             (s["x"] - math.cos(s["spin"]) * arm, s["y"] - math.sin(s["spin"]) * arm), 3)
        for h in sorted(self.hoops, key=lambda z: z["y"]):
            if h["y"] < self.y + 40:
                self.draw_hoop(surf, h)
        self.draw_sail(surf)
        for h in self.hoops:
            if h["y"] >= self.y + 40:
                self.draw_hoop(surf, h)
        for sp in self.sparks:
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(2, sp[4] // 3))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 180, 60, 28))
            surf.blit(ov, (0, 0))
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 58)))
        sub = self.font_sm.render(HANDLE, True, CYAN)
        surf.blit(sub, sub.get_rect(center=(W // 2, 112)))
        if self.banner:
            lab = self.font.render(self.banner_txt, True, MAG)
            surf.blit(lab, lab.get_rect(center=(W // 2, 168)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"COMBO  x{self.combo}    GUST  {self.wind:+.1f}", True, LIME)
        hint = self.font_sm.render("A/D bank the pennon   thread the hoops", True, PEACH)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 118)))
        surf.blit(cb, cb.get_rect(center=(W // 2, H - 72)))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 32)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.steer(-1)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.steer(1)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
