import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Game window dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Parking Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
PINK = (255, 105, 180)

# Parking spot settings
parking_spot = pygame.Rect(600, 200, int(
    150 // 3 * 2 / 1.5), int(100 // 3 * 2 / 1.5))

# Barrier settings
barrier_thickness = int(10 // 3 * 2 / 1.5)
barriers = [
    pygame.Rect(0, 0, WIDTH, barrier_thickness),  # Top barrier
    pygame.Rect(0, 0, barrier_thickness, HEIGHT),  # Left barrier
    pygame.Rect(
        0,
        HEIGHT -
        barrier_thickness,
        WIDTH,
        barrier_thickness),
    # Bottom barrier
    pygame.Rect(
        WIDTH -
        barrier_thickness,
        0,
        barrier_thickness,
        HEIGHT)  # Right barrier
]

# Car settings
car_size = 50 // 5
car_img = pygame.Surface((car_size, car_size))
car_img.fill(BLUE)
car_pos_x = 100.0
car_pos_y = 300.0
car_rect = car_img.get_rect(center=(car_pos_x, car_pos_y))
car_speed = 0
rotation = 0

# Rectangle settings
rectangle_width = car_size * 2 * 1.5 // 2 * 2
rectangle_height = car_size * 3 * 1.5 // 2 * 2
rectangle_surf = pygame.Surface(
    (rectangle_width, rectangle_height), pygame.SRCALPHA)
rectangle_surf.fill(RED)

# Rotate the rectangle by 90 degrees clockwise initially
rectangle_surf = pygame.transform.rotate(rectangle_surf, 90)

# Rectangle collision settings
rectangle_collision_rect = pygame.Rect(0, 0, rectangle_width, rectangle_height)

# Game loop flag
clock = pygame.time.Clock()
running = True

# Font for text rendering
font = pygame.font.Font(None, 36)

# Minimum speed for turning
MIN_TURN_SPEED = 0.1

# Maximum speed limit (уменьшена в два раза)
MAX_SPEED = 5 / 2
MAX_SPEED_BACKWARD = MAX_SPEED / 2

# Acceleration settings
ACCELERATION = 0.05 / 2
DECELERATION = 0.05 / 2

# Collision counter
collision_counter = 0

# Time counter (в секундах)
time_elapsed = 0

# List to store custom pink rectangles
custom_rectangles = []

# Function to calculate the distance between two points


def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 +
                     (point1[1] - point2[1]) ** 2)

# Function to find the nearest point on a rectangle to a given point


def nearest_point_on_rect(rect, point):
    x, y = point
    nearest_x = max(rect.left, min(x, rect.right))
    nearest_y = max(rect.top, min(y, rect.bottom))
    return (nearest_x, nearest_y)

# Function to check if a point is inside a rectangle


def point_inside_rect(point, rect):
    x, y = point
    return rect.left <= x <= rect.right and rect.top <= y <= rect.bottom

# Function to calculate the distance along a ray


def ray_distance(start_point, angle, barriers, max_distance):
    x, y = start_point
    dx = math.cos(math.radians(angle))
    dy = math.sin(math.radians(angle))

    for i in range(int(max_distance)):
        x += dx
        y += dy
        for barrier in barriers:
            if point_inside_rect((x, y), barrier):
                return i
        if x < 0 or x > WIDTH or y < 0 or y > HEIGHT:
            return i

    return max_distance

# Function to find the intersection point of a ray with the rectangle's
# perimeter


def ray_intersection_with_rect(start_point, angle, rect):
    x, y = start_point
    dx = math.cos(math.radians(angle))
    dy = math.sin(math.radians(angle))

    # Check intersection with each side of the rectangle
    intersections = []
    sides = [
        ((rect.left, rect.top), (rect.right, rect.top)),  # Top side
        ((rect.right, rect.top), (rect.right, rect.bottom)),  # Right side
        ((rect.right, rect.bottom), (rect.left, rect.bottom)),  # Bottom side
        ((rect.left, rect.bottom), (rect.left, rect.top))  # Left side
    ]

    for side_start, side_end in sides:
        # Line-line intersection formula
        x1, y1 = side_start
        x2, y2 = side_end
        x3, y3 = x, y
        x4, y4 = x + dx * 1000, y + dy * 1000  # Extend the ray far enough

        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denominator == 0:
            continue  # Lines are parallel

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator

        if 0 <= t <= 1 and u >= 0:
            intersection_x = x1 + t * (x2 - x1)
            intersection_y = y1 + t * (y2 - y1)
            intersections.append((intersection_x, intersection_y))

    # Return the closest intersection
    if intersections:
        return min(intersections, key=lambda p: distance(start_point, p))
    return None

# Function to reset the game


def reset_game():
    global car_pos_x, car_pos_y, car_speed, rotation, collision_counter, time_elapsed
    car_pos_x = 100.0
    car_pos_y = 300.0
    car_speed = 0
    rotation = 0
    collision_counter = 0
    time_elapsed = 0  # Сброс времени


# Main game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Handle mouse click events
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            clicked_rect = None

            # Check if the click is on an existing custom rectangle
            for rect in custom_rectangles:
                if rect.collidepoint(mouse_pos):
                    clicked_rect = rect
                    break

            if event.button == 1:  # Left mouse button
                if clicked_rect:
                    # Remove the clicked rectangle
                    custom_rectangles.remove(clicked_rect)
                else:
                    # Create a new pink rectangle (vertical orientation, 1.5x
                    # size)
                    new_rect = pygame.Rect(
                        mouse_pos[0] - rectangle_width // 2 * 1.5,
                        mouse_pos[1] - rectangle_height // 2 * 1.5,
                        rectangle_width * 1.5,
                        rectangle_height * 1.5
                    )
                    custom_rectangles.append(new_rect)

            elif event.button == 3:  # Right mouse button
                if clicked_rect:
                    # Rotate the clicked rectangle by 90 degrees
                    new_rect = pygame.Rect(
                        clicked_rect.x,
                        clicked_rect.y,
                        clicked_rect.height,
                        clicked_rect.width
                    )
                    custom_rectangles.remove(clicked_rect)
                    custom_rectangles.append(new_rect)

        # Handle key press events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0:  # Reset the game on pressing '0'
                reset_game()

    # Handle key presses for movement, rotation, and stop
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        car_speed += ACCELERATION
    if keys[pygame.K_DOWN]:
        car_speed -= DECELERATION
    if keys[pygame.K_LEFT] and abs(car_speed) >= MIN_TURN_SPEED:
        rotation += 1
    if keys[pygame.K_RIGHT] and abs(car_speed) >= MIN_TURN_SPEED:
        rotation -= 1
    if keys[pygame.K_SPACE]:
        car_speed = 0
    rotation = (rotation + 360) % 360

    # Limit the maximum speed
    if car_speed > MAX_SPEED:
        car_speed = MAX_SPEED
    elif car_speed < -MAX_SPEED_BACKWARD:
        car_speed = -MAX_SPEED_BACKWARD

    # Calculate new car position
    new_car_pos_x = car_pos_x + car_speed * math.cos(math.radians(rotation))
    new_car_pos_y = car_pos_y + car_speed * math.sin(math.radians(rotation))

    # Create a temporary rect for collision detection
    temp_car_rect = car_rect.copy()
    temp_car_rect.centerx = new_car_pos_x
    temp_car_rect.centery = new_car_pos_y

    # Rotate the collision rectangle
    rotated_rectangle = pygame.transform.rotate(rectangle_surf, -rotation)
    rotated_rectangle_rect = rotated_rectangle.get_rect(
        center=temp_car_rect.center)

    # Update the collision rectangle to match the rotated rectangle
    rotated_collision_rect = rotated_rectangle_rect.copy()

    # Check for collisions with barriers and custom rectangles
    collision_detected = False
    for barrier in barriers:
        if rotated_collision_rect.colliderect(barrier):
            car_speed = 0
            collision_detected = True
            break

    for rect in custom_rectangles:
        if rotated_collision_rect.colliderect(rect):
            car_speed = 0
            collision_detected = True
            break

    # Check if the red rectangle touches the screen boundaries
    if (rotated_collision_rect.left < 0 or
        rotated_collision_rect.right > WIDTH or
        rotated_collision_rect.top < 0 or
            rotated_collision_rect.bottom > HEIGHT):
        car_speed = 0
        collision_detected = True

    # Update collision counter
    if collision_detected:
        collision_counter += 1

    # Update car position if no collision
    if car_speed != 0:
        car_pos_x = new_car_pos_x
        car_pos_y = new_car_pos_y

    # Update car_rect with integer positions
    car_rect.centerx = int(car_pos_x)
    car_rect.centery = int(car_pos_y)

    # Rotate the car image for display
    rotated_car = pygame.transform.rotozoom(car_img, rotation, 1)
    rotated_rect = rotated_car.get_rect(center=car_rect.center)

    # Calculate the distance from the center of the red rectangle to the
    # nearest point on the parking spot
    red_rect_center = rotated_collision_rect.center
    nearest_point = nearest_point_on_rect(parking_spot, red_rect_center)
    distance_to_parking = distance(red_rect_center, nearest_point)

    # Calculate distances along 8 rays
    ray_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    ray_distances = []
    for angle in ray_angles:
        # Calculate the starting point at the center of the car
        start_point = car_rect.center

        # Find the intersection point of the ray with the rectangle's perimeter
        intersection_point = ray_intersection_with_rect(
            start_point, angle + rotation, rotated_collision_rect)
        if intersection_point:
            # Calculate the distance from the center to the intersection point
            distance_to_intersection = distance(
                start_point, intersection_point)

            # Move the starting point of the ray in the direction of the ray by
            # the distance to the intersection
            start_x = start_point[0] + distance_to_intersection * \
                math.cos(math.radians(angle + rotation))
            start_y = start_point[1] + distance_to_intersection * \
                math.sin(math.radians(angle + rotation))

            # Calculate the ray distance to the barrier
            dist = ray_distance(
                (start_x,
                 start_y),
                angle + rotation,
                barriers + custom_rectangles,
                50 * 3)  # Увеличиваем длину луча в 3 раза

            # Subtract the distance to the intersection point
            adjusted_dist = dist
            # Округляем до целого числа
            ray_distances.append(round(adjusted_dist))
        else:
            ray_distances.append(0)

    # Calculate the average distance from the corners of the red rectangle to
    # the nearest point on the parking spot
    corners = [
        (rotated_collision_rect.left, rotated_collision_rect.top),
        (rotated_collision_rect.right, rotated_collision_rect.top),
        (rotated_collision_rect.right, rotated_collision_rect.bottom),
        (rotated_collision_rect.left, rotated_collision_rect.bottom)
    ]
    corner_distances = [
        distance(
            corner,
            nearest_point_on_rect(
                parking_spot,
                corner)) for corner in corners]
    average_distance = sum(corner_distances) / len(corner_distances)

    # Check if the car is within the parking spot
    if parking_spot.colliderect(rotated_rect):
        # Check if the car is fully within the parking spot
        if (rotated_rect.left >= parking_spot.left and
                rotated_rect.right <= parking_spot.right and
                rotated_rect.top >= parking_spot.top and
                rotated_rect.bottom <= parking_spot.bottom):
            # Success message
            success_text = font.render(
                "Parked Successfully!", True, (0, 255, 0))
            screen.blit(
                success_text,
                (WIDTH //
                 2 -
                 success_text.get_width() //
                 2,
                 50))

    # Clear the screen
    screen.fill(WHITE)

    # Draw the barriers
    for barrier in barriers:
        pygame.draw.rect(screen, BLACK, barrier)

    # Draw the parking spot
    pygame.draw.rect(screen, BLACK, parking_spot)

    # Draw the car
    screen.blit(rotated_car, rotated_rect)

    # Draw the rotated rectangle
    screen.blit(rotated_rectangle, rotated_rectangle_rect)

    # Draw the custom pink rectangles
    for rect in custom_rectangles:
        pygame.draw.rect(screen, PINK, rect)

    # Display the distance to the parking spot
    distance_text = font.render(
        f"Distance: {
            average_distance:.2f}", True, (0, 0, 0))
    screen.blit(distance_text, (10, 10))

    # Display the collision counter
    collision_text = font.render(
        f"Collisions: {collision_counter}", True, (0, 0, 0))
    screen.blit(collision_text, (10, 50))

    # Display the time elapsed
    time_text = font.render(f"Time: {time_elapsed:.2f}s", True, (0, 0, 0))
    screen.blit(time_text, (10, 90))

    # Display the ray distances
    ray_text = font.render(f"Rays: {ray_distances}", True, (0, 0, 0))
    screen.blit(
        ray_text,
        (WIDTH -
         ray_text.get_width() -
         10,
         HEIGHT -
         ray_text.get_height() -
         10))

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

    # Update time elapsed
    # Добавляем время, прошедшее с последнего кадра
    time_elapsed += clock.get_time() / 1000

# Quit the game
pygame.quit()
sys.exit()
