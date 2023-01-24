import pygame
import uuid

FRICTION = 0.1
Number = int | float  # A type alias for a number


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x: Number, y: Number, width: int, height: int, color: tuple[int, int, int]):
        """
        A generic obstacle object that the player can collide with.

        ---
        :param x: The starting x-coordinate of the obstacle (top-left)
        :param y: The starting y-coordinate of the obstacle (top-left)
        :param width: The width of the obstacle
        :param height: The height of the obstacle
        :param color: The color of the obstacle (RGB)
        """
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.id = uuid.uuid4()
        self.color = color


class Player(pygame.sprite.Sprite):
    def __init__(self, id: uuid.UUID, x: Number, y: Number, color: tuple[int, int, int]) -> None:
        """
        Initializes a player object with a UUID and movement-vectors.

        ---
        :param id: The UUID of the player
        :param x: The starting x-coordinate of the player (top-left)
        :param y: The starting y-coordinate of the player (top-left)
        :param color: The color of the player (RGB)

        ---
        :return: None
        """
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.id = id
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.color = color

    def update(self, actions: list[str]) -> None:
        """
        Updates the player's position and velocity, and checks for collisions.

        ---
        :param actions: A list of actions the player is doing

        ---
        :return: None
        """
        # The axis are:
        # X: -->
        # Y: |
        #    v
        # To add gravity, change this to (0, 1)
        self.acc = pygame.math.Vector2(0, 0)
        force = pygame.math.Vector2(0, 0)
        if "LEFT" in actions:
            force.x += -1
        if "RIGHT" in actions:
            force.x += 1
        if "UP" in actions:
            force.y += -1
        if "DOWN" in actions:
            force.y += 1

        # Following the formula: ΣF = m * a
        self.acc += force + -(self.vel * FRICTION)
        self.vel += self.acc

        # This very much does not work
        '''
        collision, collision_point, side_hit = check_collision(self, obstacles)
        if collision:
            self.pos = pygame.math.Vector2(collision_point)
            if side_hit == 0:  # right
                self.vel.x = 0
                self.pos.x += 1
            elif side_hit == 1:  # left
                self.vel.x = 0
                self.pos.x -= 1
            elif side_hit == 2:  # bottom
                self.vel.y = 0
                self.pos.y -= 1
            elif side_hit == 3:  # top
                self.vel.y = 0
                self.pos.y += 1
        '''

        self.pos += self.vel

        self.rect.topleft = (self.pos.x, self.pos.y)

    def setPos(self, x: Number, y: Number):
        self.pos = pygame.math.Vector2(x, y)
        self.rect.topleft = (x, y)


def check_collision(player: Player, obstacles: pygame.sprite.Group) -> tuple[bool, tuple[Number, Number], Number]:
    """
    Checks if a player collides with any of the obstacles in the group so the player can be moved accordingly.

    ---
    :param player: The player object
    :param obstacles: A group of obstacles the player can collide with
    ---

    :return: A tuple of (bool, tuple, tuple)
        1 - bool: Whether or not the line segment intersects with the bounding box
        2 - tuple: The point of intersection
        3 - tuple: The side that the intersection is on
        (0 for right, 1 for left, 2 for bottom, 3 for top)
    """
    start = player.rect.center
    end = (player.rect.centerx + player.vel.x,
           player.rect.centery + player.vel.y)
    for obstacle in obstacles:
        padded_rect = obstacle.rect.inflate(player.rect.width,
                                            player.rect.height)
        collides, collision_point, side_hit = segment_check(start,
                                                            end,
                                                            padded_rect)
        if collides:
            if side_hit == -1:
                collides, collision_point, side_hit = static_body_check(player.rect,
                                                                        obstacle.rect)
                return collides, collision_point, side_hit
            else:
                # The collision is the center of the player, so we'll change it to the topleft corner
                # since that's what the player's pos is
                collision_point = (collision_point[0] - player.rect.width / 2,
                                   collision_point[1] - player.rect.height / 2)
                return True, collision_point, side_hit

    return False, (0, 0), 0


def segment_check(start: tuple[Number, Number], end: tuple[Number, Number], box: pygame.Rect) -> tuple[bool, tuple[Number, Number], Number]:
    """
    Checks if a line segment intersects with a bounding box.

    ---
    :param start: The start of the line segment
    :param end: The end of the line segment
    :param box: The bounding box
    ---
    :return: A tuple of (bool, tuple, tuple)
        1 - bool: Whether or not the line segment intersects with the bounding box
        2 - tuple: The point of intersection
        3 - tuple: The side that the intersection is on
        (0 for right, 1 for left, 2 for bottom, 3 for top, -1 for static-body-check)
    """
    # This is a helper function for collision()
    # This function checks if a vector intersects with a bounding box.
    # This is implemented using the Liang-Barsky algorithm.
    # https://en.wikipedia.org/wiki/Liang%E2%80%93Barsky_algorithm
    # or https://www.skytopia.com/project/articles/compsci/clipping.html
    # Another good find is https://www.youtube.com/watch?v=3dIiTo7mlnU and his next video

    deltaX = end[0] - start[0]
    deltaY = end[1] - start[1]

    p = [-deltaX,
         deltaX,
         -deltaY,
         deltaY]
    q = [start[0] - box.left,
         box.right - start[0],
         start[1] - box.top,
         box.bottom - start[1]]

    t0 = 0
    t1 = 1

    side_hit = -1  # 0 for right, 1 for left, 2 for bottom, 3 for top

    for i in range(4):  # For each side of the box
        if p[i] == 0:
            if q[i] < 0:
                return False, (0, 0), -1

        elif p[i] < 0:
            r = q[i] / p[i]

            if r > t1:
                return False, (0, 0), -1

            elif r > t0:
                side_hit = i
                t0 = r

        elif p[i] > 0:
            r = q[i] / p[i]

            if r < t0:
                return False, (0, 0), -1

            elif r < t1:
                t1 = r

    intersectionX = start[0] + t0 * deltaX
    intersectionY = start[1] + t0 * deltaY

    return True, (intersectionX, intersectionY), side_hit


def static_body_check(box1: pygame.Rect, box2: pygame.Rect) -> tuple[bool, tuple[Number, Number], Number]:
    delta_x = box2.centerx - box1.centerx
    gap_x = abs(delta_x) - box1.width / 2 - box2.width / 2
    delta_y = box2.centery - box1.centery
    gap_y = abs(delta_y) - box1.height / 2 - box2.height / 2

    if abs(gap_x) > abs(gap_y):
        if delta_y < 0:
            return True, (box1.left, box2.bottom), 2
        else:
            return True, (box1.left, box2.top - box1.height - 1), 3
    else:
        if delta_x < 0:
            return True, (box1.right, box1.top), 0
        else:
            return True, (box2.left - box1.width, box1.top), 1
