import pygame 
import sys 
import math 
import random 
 
# 常量 
MAX_BOUNCES = 5 
RAY_PULSE_SPEED = 300 
MIRROR_HANDLE_SIZE = 15 
 
# 颜色定义 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 165, 0)
SILVER = (192, 192, 192)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
 
# 窗口尺寸 
WIDTH, HEIGHT = 1200, 800 
 
class OpticalDevice:
    """光学器材基类"""
    def __init__(self, x, y):
        self.x = x 
        self.y = y 
        self.is_dragging     = False 
        self.angle     = 0 
        self.needs_update     = True 
        self.color     = SILVER 
        self.length     = 100 
 
    def move(self, x, y):
        if self.x != x or self.y != y:
            self.x = x 
            self.y = y 
            self.needs_update     = True 
 
class Mirror(OpticalDevice):
    """平面镜"""
    def __init__(self, x, y, length=100):
        super().__init__(x, y)
        self.length    = length 
        self.last_update    = 0 
 
    def move(self, x, y):
        super().move(x, y)
        self.last_update    = pygame.time.get_ticks()   
    
    def draw(self, surface):
        start, end = self.get_end_points()   
        pygame.draw.line(surface,    self.color,    start, end, 5)
        pygame.draw.circle(surface,    BLUE, (int(start[0]), int(start[1])), MIRROR_HANDLE_SIZE)
        pygame.draw.circle(surface,    RED, (int(end[0]), int(end[1])), MIRROR_HANDLE_SIZE)
 
    def get_end_points(self):
        dx = self.length/2    * math.cos(math.radians(self.angle))    
        dy = self.length/2    * math.sin(math.radians(self.angle))    
        return (
            (self.x - dx, self.y - dy), 
            (self.x + dx, self.y + dy)
        )
 
class Target:
    """目标靶区域"""
    def __init__(self, x, y, radius=30):
        self.x = x 
        self.y = y 
        self.radius    = radius 
        self.hit    = False 
        self.moved    = False 
 
    def draw(self, surface):
        color = GREEN if self.hit    else RED 
        pygame.draw.circle(surface,    color, (self.x, self.y), self.radius)    
        pygame.draw.circle(surface,    BLACK, (self.x, self.y), self.radius,    2)
 
class MovingTarget(Target):
    """水平移动目标"""
    def __init__(self, x, y, min_x, max_x):
        super().__init__(x, y)
        self.min_x    = min_x 
        self.max_x    = max_x 
        self.speed    = 2 
        self.direction    = 1 
        
    def update(self):
        prev_x = self.x 
        self.x += self.speed    * self.direction    
        self.moved    = (self.x != prev_x)
        if self.x >= self.max_x    or self.x <= self.min_x:    
            self.direction    *= -1 
 
class VerticalMovingTarget(Target):
    """垂直移动目标"""
    def __init__(self, x, y, min_y, max_y):
        super().__init__(x, y)
        self.min_y    = min_y 
        self.max_y    = max_y 
        self.speed    = 2 
        self.direction    = 1 
        
    def update(self):
        prev_y = self.y 
        self.y += self.speed    * self.direction    
        self.moved    = (self.y != prev_y)
        if self.y >= self.max_y    or self.y <= self.min_y:    
            self.direction    *= -1 
 
class EightShapeTarget(Target):
    """8字形移动靶"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.timer   = 0 
        self.speed   = 0.05 
        
    def update(self):
        self.timer   += self.speed   
        self.x = 800 + 200 * math.sin(self.timer   * 2)
        self.y = 400 + 100 * math.sin(self.timer)  
        self.moved   = True 
 
class Obstacle:
    """障碍物"""
    def __init__(self, x, y, width, height):
        self.rect   = pygame.Rect(x, y, width, height)
        
    def draw(self, surface):
        pygame.draw.rect(surface,   BLACK, self.rect)  
 
class LightSource:
    """点光源"""
    def __init__(self, x, y):
        self.x = x 
        self.y = y 
        self.rays    = []
        self.num_rays    = 3 
        self.spread    = 30 
        self.prev_rays    = None 
        self.radius    = 10 
        self.last_draw    = 0 
 
    def draw(self, surface):
        now = pygame.time.get_ticks()   
        if now - self.last_draw   < 50:  # 50ms间隔 
            return 
        self.last_draw   = now 
        for ray in self.rays:   
            if len(ray) >= 2:
                width = 3 + math.sin(now/300)   * 1 
                alpha = 200 + math.sin(now/400)   * 55 
                color = (255, min(255, alpha), 0)
                int_points = [(int(x),int(y)) for x,y in ray]
                pygame.draw.lines(surface,   color, False, int_points, int(width))
 
    def update_rays(self, devices, targets):
        active_devices = [d for d in devices if abs(d.x - self.x) < WIDTH/2]
        targets_moved = any(isinstance(t, (MovingTarget, EightShapeTarget)) and t.moved   for t in targets)
        needs_update = any(device.needs_update   for device in devices) or targets_moved 
        
        if not needs_update and self.prev_rays   is not None:
            self.rays   = self.prev_rays    
            return 
            
        for device in devices:
            device.needs_update   = False 
 
        for target in targets:
            target.hit   = False 
 
        self.rays   = []
        for i in range(self.num_rays):   
            angle = self.spread/2   - i*(self.spread/(self.num_rays-1   or 1))
            ray_path = self.trace_ray((self.x,   self.y), math.radians(angle),   devices, targets)
            self.rays.append(ray_path)   
        
        self.prev_rays   = self.rays.copy()  
 
    def trace_ray(self, start, angle, devices, targets, max_bounces=5):
        path = [start]
        current_pos = start 
        direction = (math.cos(angle),   math.sin(angle))   
        
        for _ in range(max_bounces):
            closest_t = float('inf')
            closest_device = None 
            intersect_point = None 
            closest_target = None 
            normal = None 
 
            # 先检测目标碰撞 
            for target in targets:
                result = self.target_intersection(current_pos,   direction, target)
                if result and result['t'] < closest_t:
                    closest_t = result['t']
                    closest_target = target 
                    intersect_point = result['point']
 
            # 再检测设备碰撞 
            for device in devices:
                if isinstance(device, Mirror):
                    result = self.mirror_intersection(current_pos,   direction, device)
                    if result and result['t'] < closest_t:
                        closest_t = result['t']
                        closest_device = device 
                        intersect_point = result['point']
                        normal = result['normal']
 
            # 优先处理目标命中 
            if closest_target:
                closest_target.hit   = True 
                path.append(intersect_point)  
                break 
 
            if not closest_device:
                end_x = current_pos[0] + direction[0] * 1000 
                end_y = current_pos[1] + direction[1] * 1000 
                path.append((end_x,   end_y))
                break 
 
            if intersect_point:
                path.append(intersect_point)   
                current_pos = intersect_point 
                direction = self.reflect(direction,   normal)
            
        valid_path = [p for p in path if all(not math.isnan(c)   for c in p)]
        return [p for p in valid_path if 0 <= p[0] <= WIDTH and 0 <= p[1] <= HEIGHT]
 
    def mirror_intersection(self, origin, direction, mirror):
        start, end = mirror.get_end_points()   
        x1, y1 = start 
        x2, y2 = end 
        x3, y3 = origin 
        dx, dy = direction 
 
        denominator = (y2-y1)*dx - (x2-x1)*dy 
        if abs(denominator) < 1e-6:
            return None 
 
        t = ((x1-x3)*(y2-y1) - (y1-y3)*(x2-x1)) / denominator 
        u = ((x1-x3)*dy - (y1-y3)*dx) / denominator 
        
        if t < 0 or u < 0 or u > 1:
            return None 
 
        px = x3 + t*dx 
        py = y3 + t*dy 
        
        mirror_dir = (x2 - x1, y2 - y1)
        normal = (-mirror_dir[1], mirror_dir[0])
        length = math.hypot(*normal)   
        normal = (normal[0]/length, normal[1]/length)
        
        return {'t': t, 'point': (px, py), 'normal': normal}
 
    def target_intersection(self, origin, direction, target):
        x1, y1 = origin 
        dx, dy = direction 
        x2, y2 = target.x, target.y 
        r = target.radius    
        
        a = dx*dx + dy*dy 
        b = 2*(dx*(x1 - x2) + dy*(y1 - y2))
        c = (x1 - x2)**2 + (y1 - y2)**2 - r*r 
        
        discriminant = b*b - 4*a*c 
        if discriminant < 0:
            return None 
            
        t1 = (-b + math.sqrt(discriminant))   / (2*a)
        t2 = (-b - math.sqrt(discriminant))   / (2*a)
        
        t = min(t1, t2) if min(t1, t2) > 0 else max(t1, t2)
        if t < 0:
            return None 
            
        px = x1 + t*dx 
        py = y1 + t*dy 
        
        return {'t': t, 'point': (px, py)}
 
    def reflect(self, direction, normal):
        dot = direction[0]*normal[0] + direction[1]*normal[1]
        return (direction[0] - 2*dot*normal[0],
                direction[1] - 2*dot*normal[1])
 
class GameLevel:
    """游戏关卡"""
    def __init__(self, level_num):
        self.level_num    = level_num 
        self.targets    = []
        self.obstacles   = []
        self.mirror_limit    = 99 
        self.time_limit    = 0 
        self.completed    = False 
        self.score    = 0 
        self.setup_level()    
        
    def setup_level(self):
        if self.level_num    == 1:
            # 关卡1: 精准反射挑战 
            self.targets.extend([  
                Target(1000, 200),
                Target(1000, 400), 
                Target(1000, 600)
            ])
            self.mirror_limit    = 1 
            self.time_limit    = 60 
 
        elif self.level_num    == 2:
            # 关卡2: 移动迷宫 
            self.targets.extend([  
                MovingTarget(800, 300, 800, 1000),
                VerticalMovingTarget(900, 200, 200, 400)
            ])
            self.mirror_limit    = 3 
            self.time_limit    = 45 
 
        elif self.level_num    == 3:
            # 关卡3: 光线分束 
            self.targets.extend([  
                Target(100, 100),
                Target(1000, 100),
                Target(500, 700)
            ])
            self.mirror_limit    = 4 
            self.time_limit    = 75 
 
        elif self.level_num    == 4:
            # 关卡4: 障碍物挑战 
            self.targets.append(Target(1100,   400))
            self.obstacles.append(Obstacle(500,   300, 200, 200))
            self.mirror_limit    = 5 
            self.time_limit    = 90 
 
        elif self.level_num    == 5:
            # 关卡5: 终极反射大师 
            self.targets.append(EightShapeTarget(800,   400))
            self.mirror_limit    = 6 
            self.time_limit    = 120  
            
    def check_completion(self):
        self.completed   = all(t.hit   for t in self.targets)   
        return self.completed    
        
    def calculate_score(self, mirrors_used, time_remaining):
        base_score = self.level_num   * 100 
        mirror_bonus = (self.mirror_limit   - mirrors_used) * 20 
        time_bonus = int(time_remaining) * 2 if self.time_limit   > 0 else 0 
        self.score   = base_score + mirror_bonus + time_bonus 
        return self.score    
 
def main():
    pygame.init()   
    screen = pygame.display.set_mode((WIDTH,   HEIGHT))
    pygame.display.set_caption(" 光学实验室大冒险 - 完整版")
    clock = pygame.time.Clock()   
    font = pygame.font.SysFont('SimHei',   26)
    small_font = pygame.font.SysFont('Microsoft  YaHei', 18)
    
    current_level = 1 
    level = GameLevel(current_level)
    devices = []
    light = LightSource(200, 400)
    selected_device = None 
    drag_offset = (0, 0)
    
    start_time = pygame.time.get_ticks()   
    time_left = level.time_limit    
    total_score = 0 
    
    toolbar_width = 150 
    mirror_btn = pygame.Rect(20, 120, 110, 40)
    level_btn = pygame.Rect(20, 180, 110, 40)
    reset_btn = pygame.Rect(20, 240, 110, 40)
    
    running = True 
    while running:
        if level.time_limit   > 0:
            elapsed = (pygame.time.get_ticks()   - start_time) / 1000 
            time_left = max(0, level.time_limit   - elapsed)
            if time_left <= 0 and not level.completed:   
                current_level = max(1, current_level - 1)
                level = GameLevel(current_level)
                devices = []
                start_time = pygame.time.get_ticks()   
        
        for target in level.targets:   
            if isinstance(target, (MovingTarget, VerticalMovingTarget, EightShapeTarget)):
                target.update()   
                light.update_rays(devices,   level.targets)   
        
        screen.fill(WHITE)   
        
        for event in pygame.event.get():   
            if event.type   == pygame.QUIT:
                running = False 
 
            elif event.type   == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos    
                if x < toolbar_width:
                    if mirror_btn.collidepoint(x,   y) and len(devices) < level.mirror_limit:   
                        new_mirror = Mirror(WIDTH//2, HEIGHT//2)
                        devices.append(new_mirror)   
                        selected_device = new_mirror 
                        drag_offset = (new_mirror.x - x, new_mirror.y - y)
                        new_mirror.needs_update   = True 
                    elif level_btn.collidepoint(x,   y):
                        current_level = current_level % 5 + 1 
                        level = GameLevel(current_level)
                        devices = []
                        start_time = pygame.time.get_ticks()   
                    elif reset_btn.collidepoint(x,   y):
                        devices = []
                        start_time = pygame.time.get_ticks()   
                else:
                    for device in devices:
                        start, end = device.get_end_points()   
                        if math.hypot(start[0]   - x, start[1] - y) < 10:
                            device.angle   += 15 
                            device.needs_update   = True 
                            break 
                        elif math.hypot(end[0]   - x, end[1] - y) < 10:
                            device.angle   -= 15 
                            device.needs_update   = True 
                            break 
                        elif math.hypot(device.x   - x, device.y - y) < 20:
                            selected_device = device 
                            drag_offset = (device.x - x, device.y - y)
                            break 
 
            elif event.type   == pygame.MOUSEMOTION and selected_device:
                x, y = event.pos    
                selected_device.move(x   + drag_offset[0], y + drag_offset[1])
 
            elif event.type   == pygame.MOUSEBUTTONUP:
                selected_device = None 
                if level.check_completion():   
                    score = level.calculate_score(len(devices),   time_left)
                    total_score += score 
                    current_level = current_level % 5 + 1 
                    level = GameLevel(current_level)
                    devices = []
                    start_time = pygame.time.get_ticks()   
 
            elif event.type   == pygame.KEYDOWN:
                if event.key   == pygame.K_UP and light.num_rays   < 10:
                    light.num_rays   += 1 
                    for device in devices:
                        device.needs_update   = True 
                elif event.key   == pygame.K_DOWN and light.num_rays   > 1:
                    light.num_rays   -= 1 
                    for device in devices:
                        device.needs_update   = True 
                elif event.key   == pygame.K_RIGHT and light.spread   < 90:
                    light.spread   += 5 
                    for device in devices:
                        device.needs_update   = True 
                elif event.key   == pygame.K_LEFT and light.spread   > 5:
                    light.spread   -= 5 
                    for device in devices:
                        device.needs_update   = True 
                elif event.key   == pygame.K_d and selected_device:
                    devices.remove(selected_device)   
                    selected_device = None 
                elif event.key   == pygame.K_c and selected_device and len(devices) < level.mirror_limit:   
                    new_mirror = Mirror(selected_device.x + 20, selected_device.y + 20)
                    new_mirror.angle   = selected_device.angle    
                    devices.append(new_mirror)   
                elif event.key   == pygame.K_SPACE:
                    devices = []
                elif event.key   == pygame.K_n:
                    current_level = current_level % 5 + 1 
                    level = GameLevel(current_level)
                    devices = []
                    start_time = pygame.time.get_ticks()   
                elif event.key   == pygame.K_r:
                    devices = []
                    start_time = pygame.time.get_ticks()   
 
        light.update_rays(devices,   level.targets)   
 
        pygame.draw.rect(screen,   (240, 240, 240), (0, 0, toolbar_width, HEIGHT))
        pygame.draw.rect(screen,   BLACK, (0, 0, toolbar_width, HEIGHT), 2)
        
        pygame.draw.rect(screen,   SILVER, mirror_btn)
        pygame.draw.rect(screen,   BLACK, mirror_btn, 2)
        mirror_text = small_font.render(" 添加镜子", True, BLACK)
        screen.blit(mirror_text,   (mirror_btn.x + 10, mirror_btn.y + 10))
        
        pygame.draw.rect(screen,   BLUE, level_btn)
        pygame.draw.rect(screen,   BLACK, level_btn, 2)
        level_text = small_font.render(f" 关卡 {current_level}/5", True, WHITE)
        screen.blit(level_text,   (level_btn.x + 10, level_btn.y + 10))
        
        pygame.draw.rect(screen,   RED, reset_btn)
        pygame.draw.rect(screen,   BLACK, reset_btn, 2)
        reset_text = small_font.render(" 重置关卡", True, WHITE)
        screen.blit(reset_text,   (reset_btn.x + 10, reset_btn.y + 10))
        
        mirror_text = small_font.render(f" 镜子: {len(devices)}/{level.mirror_limit}",   True, BLACK)
        screen.blit(mirror_text,   (20, 80))
        
        if level.time_limit   > 0:
            time_text = font.render(f" 时间: {int(time_left)}秒", True, BLACK)
            screen.blit(time_text,   (WIDTH - 200, 20))
        
        score_text = font.render(f" 总分: {total_score}", True, BLACK)
        screen.blit(score_text,   (WIDTH - 200, 60))
        
        for obstacle in level.obstacles: 
            obstacle.draw(screen) 
            
        for target in level.targets:   
            target.draw(screen)   
 
        for device in devices:
            if isinstance(device, Mirror):
                device.draw(screen)   
 
        light.draw(screen)   
        
        hints = [
            "操作提示:",
            "↑/↓: 增减光线数量",
            "←/→: 调整光线角度",
            "点击镜子端点: 旋转",
            "拖动镜子: 移动位置",
            "D: 删除镜子",
            "C: 复制镜子",
            "空格: 重置",
            "N: 下一关",
            "R: 重试当前关" 
        ]
        
        for i, hint in enumerate(hints):
            hint_text = small_font.render(hint,   True, PURPLE)
            screen.blit(hint_text,   (WIDTH - 300, HEIGHT - 250 + i * 20))
        
        pygame.display.flip() 
        clock.tick(60) 
 
if __name__ == "__main__":
    main()
