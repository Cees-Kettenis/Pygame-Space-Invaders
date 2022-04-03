import pygame, sys, os
import obstacle
from laser import Laser
from player import Player
from ailien import Alien, Extra
from random import choice, randint

class Game:
    def __init__(self):
        #Audio setup
        self.music = pygame.mixer.Sound('audio/music.wav')
        self.music.set_volume(0.2)
        self.music.play(loops=-1)

        self.lasers_shoot_sound = pygame.mixer.Sound('audio/laser.wav')
        self.lasers_shoot_sound.set_volume(0.1)
        self.explosion_sound = pygame.mixer.Sound('audio/explosion.wav')
        self.explosion_sound.set_volume(0.3)

        #player setup
        self.player_sprite = Player((screenWidth / 2,screenHeight), screenWidth, 5, self.lasers_shoot_sound)
        self.player =  pygame.sprite.GroupSingle(self.player_sprite)

        #health and score setup
        self.lives = 3
        self.lives_surf = pygame.image.load('graphics/player.png').convert_alpha()
        self.live_x_start_pos = screenWidth - (self.lives_surf.get_size()[0] * self.lives - 1 + 20)
        self.score = 0
        self.font = pygame.font.Font('font/Pixeled.ttf', 20)
        self.level = 0
        self.playing = True

        #obstacle setup
        self.shape = obstacle.shape
        self.block_size = 6
        self.blocks = pygame.sprite.Group()
        self.obstacle_amount = 4
        self.obstacle_x_positions = [num * (screenWidth / self.obstacle_amount) for num in range(self.obstacle_amount)]
        self.create_multiple_obstacle(*self.obstacle_x_positions, x_start = screenWidth / 15, y_start = 480)

        #Alien setup
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        self.alien_setup(rows = 6, cols = 8)
        self.alien_direction = 1
        
        #extra setup
        self.extra = pygame.sprite.GroupSingle()
        self.extra_spawn_time = randint(400, 800)

    def restart(self):
        #reset values to beginning
        self.lasers_shoot_sound.set_volume(0.1)
        self.music.set_volume(0.2)
        self.lives = 3
        self.score = 0
        self.level = 0
        
        #empty any sprites that might have been left over
        self.blocks = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        
        #create the new sprites
        self.create_multiple_obstacle(*self.obstacle_x_positions, x_start = screenWidth / 15, y_start = 480)
        self.alien_setup(rows = 6, cols = 8)
        self.alien_direction = 1
        self.player = pygame.sprite.GroupSingle(self.player_sprite)
        self.playing = True
    
    def create_obstacle(self, x_start, y_start, offset_x):
        for row_index, row in enumerate(self.shape):
            for column_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + column_index * self.block_size + offset_x
                    y = y_start + row_index * self.block_size
                    block = obstacle.Block(self.block_size, (241,79,80), x, y)
                    self.blocks.add(block)
    
    def create_multiple_obstacle(self, *offset, x_start, y_start):
        for offset_x in offset:
            self.create_obstacle(x_start, y_start, offset_x)

    def alien_setup(self, rows, cols, x_distance = 60, y_distance = 48, x_offset = 70, y_offset = 100):
        for row_index, row in enumerate(range(rows)):
            for col_index, col in enumerate(range(cols)):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset

                if row_index == 0:
                    alien_sprite = Alien('yellow', x, y)
                elif 1 <= row_index <= 2:
                    alien_sprite = Alien('green', x, y)
                else:
                    alien_sprite = Alien('red', x, y)

                self.aliens.add(alien_sprite)

    def alien_position_checker(self):
        all_aliens = self.aliens.sprites()
        for alien in all_aliens:
            if alien.rect.right >= screenWidth:
                self.alien_direction = -1
                self.alien_move_down(2 + self.level)
            elif alien.rect.left <= 0:
                self.alien_direction = 1
                self.alien_move_down(2 + self.level)                
    
    def alien_move_down(self, distance):
        if self.aliens:
            all_aliens = self.aliens.sprites()
            for alien in all_aliens:
                alien.rect.y += distance

    def alien_shoot(self):
        if self.aliens.sprites():
            random_alien = choice(self.aliens.sprites())
            laser_spirte = Laser(random_alien.rect.center,screenHeight, 6)
            self.alien_lasers.add(laser_spirte)
            self.lasers_shoot_sound.play()

    def extra_alien_timer(self):
        self.extra_spawn_time -= 1
        if self.extra_spawn_time <= 0:
            self.extra.add(Extra(choice(['right', 'left']), screenWidth))
            self.extra_spawn_time = randint(400, 800)

    def collision_check(self):
        #player lasers
        if self.player:
            if self.player.sprite.lasers:
                for laser in self.player.sprite.lasers:
                    #obstcle collision
                    if pygame.sprite.spritecollide(laser,self.blocks, True):
                        laser.kill()

                    #alien collision
                    aliens_hit = pygame.sprite.spritecollide(laser,self.aliens, True)
                    if aliens_hit:
                        laser.kill()
                        self.explosion_sound.play()
                        for alien in aliens_hit:
                            self.score += alien.value   
                    
                    #extra collision
                    if pygame.sprite.spritecollide(laser,self.extra, True):
                        self.score += 500
                        self.explosion_sound.play()
                        laser.kill()
        #alien lasers
        if self.alien_lasers:
            for laser in self.alien_lasers:
                #obstcle collision    
                if pygame.sprite.spritecollide(laser,self.blocks, True):
                    laser.kill()

                #player collision
                if pygame.sprite.spritecollide(laser,self.player, False):
                    laser.kill()
                    self.explosion_sound.play()
                    self.lives -= 1
                    if self.lives <= 0:
                        pygame.sprite.spritecollide(laser,self.player, True)
                        self.playing = False

        #aliens
        if self.aliens:
            for alien in self.aliens:
                pygame.sprite.spritecollide(alien,self.blocks, True)
                
                if pygame.sprite.spritecollide(alien,self.player, False):
                    pygame.sprite.spritecollide(alien, self.player, True)
                    self.playing = False

    def display_score(self, Text = 'SCORE', x_pos = 120, y_pos = 20, restart = False):
        ScoreLabel = self.font.render(f'{Text}: {self.score}', False, 'white')
        score_rect = ScoreLabel.get_rect(center = (x_pos, y_pos))
        screen.blit(ScoreLabel, score_rect)
        LevelLabel = self.font.render(f'LEVEL : {self.level + 1}', False, 'white')
        level_rect = LevelLabel.get_rect(center = (x_pos, y_pos + 40))
        screen.blit(LevelLabel, level_rect)
        if restart:
            LevelLabel = self.font.render('RESTART PRESS P', False, 'white')
            level_rect = LevelLabel.get_rect(center = (x_pos, y_pos + 80))
            screen.blit(LevelLabel, level_rect)

    def display_lives(self):
        for live in range(self.lives - 1):
            x = self.live_x_start_pos + (live * (self.lives_surf.get_size()[0] + 10))
            screen.blit(self.lives_surf, (x,8))

    def increase_level(self):
        if not self.aliens.sprites():
            self.alien_setup(rows = 6, cols = 8)
            self.lives += 1
            self.level += 1

    def run(self):
        #ONLY RUN THE GAME IF THE PLAYER IS PRESSENT
        if self.playing:
            if self.player:
                #update all sprite groups
                self.player.update()
                self.aliens.update(self.alien_direction)
                self.extra.update()
                self.alien_lasers.update()
                self.alien_position_checker()
                self.extra_alien_timer()

                #draw all sprite groups
                self.player.draw(screen)
                self.player.sprite.lasers.draw(screen)
                
                self.blocks.draw(screen)
                self.aliens.draw(screen)
                self.alien_lasers.draw(screen)
                self.extra.draw(screen)
                self.display_lives()
                self.display_score()

                self.collision_check()
                self.increase_level()
        else:
            self.lasers_shoot_sound.set_volume(0)
            self.music.set_volume(0)
            self.display_score('GAME OVER SCORE ',screenWidth//2, screenHeight//4, True)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_p]:
                self.restart()
  
class CRT:
    def __init__(self):
        self.tv = pygame.image.load('graphics/tv.png').convert_alpha()
        self.tv = pygame.transform.scale(self.tv, (screenWidth, screenHeight))
    
    def draw(self):
        self.tv.set_alpha(randint(75,90))
        self.create_crt_lines()
        screen.blit(self.tv, (0,0))

    def create_crt_lines(self):
        line_hight = 3
        line_amount = int(screenHeight / line_hight)
        for line in range(line_amount):
            y_pos = line * line_hight
            pygame.draw.line(self.tv, 'black', (0,y_pos), (screenWidth, y_pos), 1)

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Space Invaders!')
    screenWidth = 600
    screenHeight = 600
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    clock = pygame.time.Clock()
    backgroundColor = 30,30,30
    game = ''
    crt = CRT()
    
    ALIEN_LASER = pygame.USEREVENT + 1
    pygame.time.set_timer(ALIEN_LASER, 800)
    PLAYING = False

    def show_controls():
        font = pygame.font.Font('font/Pixeled.ttf', 30)
        font2 = pygame.font.Font('font/Pixeled.ttf', 20)
        controls_text = font.render("CONTROLS", False, 'white')
        controls_rect = controls_text.get_rect(center = (screenWidth/2, screenHeight/4))
        Instruction_text = font2.render("MOVE : LEFT + RIGHT ARROW KEYS", False, 'white')
        Instruction_rect = Instruction_text.get_rect(center = (screenWidth/2, screenHeight/4 + (controls_rect[1]/2 + 50)))
        Instruction_text2 = font2.render("SHOOT : SPACEBAR", False, 'white')
        Instruction_rect2 = Instruction_text2.get_rect(center = (screenWidth/2, screenHeight/4 + (controls_rect[1]/2 + 100)))
        Instruction_text3 = font2.render("START GAME : P KEY", False, 'white')
        Instruction_rect3 = Instruction_text3.get_rect(center = (screenWidth/2, screenHeight/4 + (controls_rect[1]/2 + 150)))
        screen.blit(controls_text, controls_rect)
        screen.blit(Instruction_text, Instruction_rect)
        screen.blit(Instruction_text2, Instruction_rect2)
        screen.blit(Instruction_text3, Instruction_rect3)

    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == ALIEN_LASER:
                if PLAYING:
                    game.alien_shoot()
        
        screen.fill((backgroundColor))

        if PLAYING:
            game.run()
        else:
            show_controls()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_p]:
                game = Game()
                PLAYING = True

        crt.draw()
        
        pygame.display.flip()
        clock.tick(60)
