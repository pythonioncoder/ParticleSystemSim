import pygame
import random
import math
import threading


class Particle():
    particles = []
    densities = []
    smoothingRadius = 100

    def __init__(self, pos, velocity, radius, color, mass=1):
        self.index = len(Particle.particles)
        self.pos = pos
        self.velocity = velocity
        self.radius = radius
        self.color = color
        self.mass = mass
        self.density = 0
        self.max_speed = 12000
        Particle.particles.append(self)
        Particle.densities.append(self.density)

    def update(self, screen, net_ext_force, dt):
        self.update_densities()

        self.velocity.x += net_ext_force.x / self.mass * dt
        self.velocity.y += net_ext_force.y / self.mass * dt
        self.velocity += (self.calculate_pressure_force(self.index) / self.density) * dt

        self.resolve_collisions(screen)

        self.pos.x += self.velocity.x * dt
        self.pos.y += self.velocity.y * dt
        self.set_color()


    def set_color(self):
        v = self.velocity.magnitude()
        v = min(max(v, 0.0), self.max_speed)

        t = v / self.max_speed  # normalize to [0, 1]

        # Define color anchors
        c0 = (23, 157, 170)  # 0 m/s
        c1 = (53, 187, 200) #(198, 241, 83)  # mid
        c2 = (255, 255, 255) #(252, 70, 4)  # max

        if t <= 0.5:
            # interpolate between c0 and c1
            u = t / 0.5
            r = int(c0[0] + (c1[0] - c0[0]) * u)
            g = int(c0[1] + (c1[1] - c0[1]) * u)
            b = int(c0[2] + (c1[2] - c0[2]) * u)
        else:
            # interpolate between c1 and c2
            u = (t - 0.5) / 0.5
            r = int(c1[0] + (c2[0] - c1[0]) * u)
            g = int(c1[1] + (c2[1] - c1[1]) * u)
            b = int(c1[2] + (c2[2] - c1[2]) * u)

        self.color = pygame.Color(r, g, b)


    @staticmethod
    def smoothing_kernal(radius, dst):
        if dst >= radius:
            return 0

        volume = math.pi * radius**4 / 6
        value = (radius - dst)**2
        return value / volume

    @staticmethod
    def smoothing_kernal_derivative(radius, dst):
        if dst >= radius:
            return 0

        scale = 12 / (radius**4 * math.pi)
        value = dst - radius
        return value * scale


    def calculate_density(self, samplePoint):
        rho = 0

        for particle in Particle.particles:
            dst = (samplePoint - particle.pos).magnitude()
            influence = Particle.smoothing_kernal(Particle.smoothingRadius, dst)
            rho += influence * self.mass

        self.density = rho
        return rho

    def update_densities(self):
        for i in range(len(Particle.particles)):
            Particle.densities[i] = self.calculate_density(Particle.particles[i].pos)


    def calculate_pressure_force(self, particle_index):
        pressure_gradient = pygame.Vector2(0, 0)

        for i in range(len(Particle.particles)):
            if i == particle_index:
                continue

            offset = Particle.particles[i].pos - Particle.particles[particle_index].pos
            dst = offset.magnitude()
            dir = offset / dst if dst > 0 else pygame.Vector2(1, 0)
            slope = Particle.smoothing_kernal_derivative(Particle.smoothingRadius, dst)
            density = Particle.densities[i]
            shared_pressure = Particle.calculate_shared_pressure(Particle.particles[i].density, Particle.particles[particle_index].density)
            pressure_gradient += -shared_pressure * dir * slope * self.mass / density

        return pressure_gradient


    @staticmethod
    def convert_density_to_pressure(density):
        targetDensity = 50
        pressureMultiplier = 2.5 * (Particle.particles[0].radius**2)

        densityError = density - targetDensity
        pressure = densityError * pressureMultiplier
        return pressure


    @staticmethod
    def calculate_shared_pressure(densityA, densityB):
        return (Particle.convert_density_to_pressure(densityA) + Particle.convert_density_to_pressure(densityB)) / 2


    def resolve_collisions(self, screen):
        collided = False

        # Wall Collision Detection
        if self.pos.x + self.radius > screen.get_width():
            self.velocity.x *= -1
            self.pos.x = screen.get_width() - self.radius
            collided = True
        elif self.pos.x - self.radius < 0:
            self.velocity.x *= -1
            self.pos.x = self.radius
            collided = True
        if self.pos.y + self.radius > screen.get_height():
            self.velocity.y *= -1
            self.pos.y = screen.get_height() - self.radius
            collided = True
        elif self.pos.y - self.radius < 0:
            self.velocity.y *= -1
            self.pos.y = self.radius
            collided = True

        # Kinetic Energy Loss
        if collided:
            self.velocity /= math.sqrt(2)

        if self.velocity.magnitude() < 1E-9:
            self.velocity *= 0




def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE, pygame.SRCALPHA)
    clock = pygame.time.Clock()
    running = True
    dt = 1
    r = 10
    translucence = 255
    overlay_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay_surface.fill((0, 0, 0, translucence))
    ptcl_color = "WHITE"
    num_particles = 30
    font = pygame.font.SysFont("Arial", 20)
    forces = [pygame.Vector2(0, 9.8*30)]
    net_ext_force = pygame.Vector2(0, 0)

    for i in range(num_particles):
        Particle(pygame.Vector2(random.randint(r, screen.get_width()-r),
                                                 random.randint(r, screen.get_height()-r)),
                 pygame.Vector2(0, 0), r, ptcl_color)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    forces[0] = pygame.Vector2(0, -9.8*60)
                elif event.key == pygame.K_DOWN:
                    forces[0] = pygame.Vector2(0, 9.8*60)
                elif event.key == pygame.K_LEFT:
                    forces[0] = pygame.Vector2(-9.8*60, 0)
                elif event.key == pygame.K_RIGHT:
                    forces[0] = pygame.Vector2(9.8*60, 0)
                elif event.key == pygame.K_w:
                    translucence += 15 if translucence < 255 else 0
                elif event.key == pygame.K_s:
                    translucence -= 15 if translucence > 0 else 0

        net_ext_force = forces[0]

        dt = clock.tick(60) / 1000
        
        overlay_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay_surface.fill((0, 0, 0, translucence))
        screen.blit(overlay_surface, (0, 0))

        for particle in Particle.particles:
            t1 = threading.Thread(target=particle.update, args=(screen, net_ext_force, dt))
            t1.start()
            t1.join()

        for particle in Particle.particles:
            pygame.draw.circle(screen, particle.color, particle.pos, particle.radius)

        text_surface = font.render(f"FPS: {(1 / dt):.0f}  T {translucence}", True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
