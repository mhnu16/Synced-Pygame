import pygame
import socket
import threading
import json

import protocol


def handle_input() -> list[str]:
    """
    Checks for user input and returns a list of actions.

    The actions are:
    - QUIT, UP, DOWN, LEFT, RIGHT

    ---
    :return: A list of actions
    """
    actions = []

    keys_pressed = pygame.key.get_pressed()
    if keys_pressed[pygame.K_ESCAPE]:
        actions.append("QUIT")
        return actions

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append("QUIT")
            return actions

    if keys_pressed[pygame.K_w]:
        actions.append("UP")
    if keys_pressed[pygame.K_s]:
        actions.append("DOWN")
    if keys_pressed[pygame.K_a]:
        actions.append("LEFT")
    if keys_pressed[pygame.K_d]:
        actions.append("RIGHT")

    return actions


def receive_state(client_socket: socket.socket, state: dict[str, dict[str, int]]):
    """
    Receives the state from the server and updates the state dictionary the client has.

    ---
    :param client_socket: the socket that receives the state
    :param state: the state dictionary

    ---
    :return: None
    """
    while True:
        data = protocol.receive_message(client_socket)
        if data == "QUIT":
            return

        state.update(json.loads(data))


def draw_state(screen: pygame.Surface, state: dict[str, dict[str, dict]]):
    """
    Draws the state on the screen.

    ---
    :param screen: the screen to draw on
    :param state: the state dictionary

    ---
    :return: None
    """
    for catalog, content in state.items():
        if catalog == "PLAYERS":
            for player_id, player in content.items():
                pygame.draw.rect(screen,
                                 player["COLOR"],
                                 (player["X"], player["Y"],
                                  50, 50))

        if catalog == "LEVEL_LAYOUT":
            for obstacle_id, obstacle in content.items():
                pygame.draw.rect(screen,
                                 obstacle["COLOR"],
                                 (obstacle["X"], obstacle["Y"],
                                  obstacle["WIDTH"], obstacle["HEIGHT"]))


def main():
    # Create a socket object
    client_socket = socket.socket()

    # Connect to the server
    client_socket.connect(('127.0.0.1', 8820))

    # Receive the client ID from the server
    data = protocol.receive_message(client_socket)
    json_data = json.loads(data)
    client_id = json_data["ID"]

    print(f"Connected to the server as {client_id}")

    # Create a window
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Synced Pygame - Client")
    # Create a clock
    clock = pygame.time.Clock()

    state = {}

    # Create a new thread to receive the state from the server
    thread = threading.Thread(target=receive_state,
                              args=(client_socket, state))
    thread.start()

    # Create a game loop
    while True:
        # Handle the user actions
        requests = handle_input()

        # Check if the user wants to quit
        if "QUIT" in requests:
            protocol.send_message(client_socket, json.dumps(["QUIT"]))
            thread.join(0)
            pygame.quit()
            exit()

        if requests:
            # Send the user actions to the server
            protocol.send_message(client_socket, json.dumps(requests))

        # Draw the screen
        screen.fill((0, 0, 0))

        # Draw the state
        draw_state(screen, state)
        for catalog, content in state.items():
            if catalog == "PLAYERS":
                for player_id, player in content.items():
                    pygame.draw.rect(screen,
                                     player["COLOR"],
                                     (player["X"], player["Y"],
                                      50, 50))

            if catalog == "LEVEL_LAYOUT":
                for obstacle_id, obstacle in content.items():
                    pygame.draw.rect(screen,
                                     obstacle["COLOR"],
                                     (obstacle["X"], obstacle["Y"],
                                      obstacle["WIDTH"], obstacle["HEIGHT"]))

        # Update the screen
        pygame.display.update()

        # Set the frame rate
        clock.tick(60)


if __name__ == '__main__':
    main()
