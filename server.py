import socket
import threading
import uuid
import json
import pygame
import select

import protocol
import objects

FRAME_RATE = 60

EVENT_PLAYER_JOINED = pygame.event.custom_type()


def strToRGB(string: str) -> tuple[int, int, int]:
    """
    Takes a string and returns a tuple of 3 representing an RGB color.

    ---
    :param string: the string to convert

    ---
    :return: a tuple of 3 representing an RGB color
    """
    hexa = hex(hash(string))
    # r, g, b will be the last 6 digits of the hash
    r = int(hexa[-2:], 16)
    g = int(hexa[-4:-2], 16)
    b = int(hexa[-6:-4], 16)
    return r, g, b


def receive_clients(server_socket: socket.socket, client_dict: dict[uuid.UUID, tuple[socket.socket, objects.Player]]) -> None:
    """
    Listens for new clients, initializes them and adds them to the client dictionary.

    It runs in the background and is constantly listening for new clients.
    ---
    :param server_socket: the socket that clients connect to
    :param client_dict: the dictionary that stores the clients

    ---
    :return: None
    """
    while True:
        # Accept a new connection
        server_socket.listen()
        client_socket, client_address = server_socket.accept()

        # ! I might put the initialization of the client in a separate function via sending a event through pygame

        # Generate a unique ID using UUID for the client and send it to the client
        client_id = uuid.uuid4()
        message = {"ID": str(client_id)}
        protocol.send_message(client_socket,
                              json.dumps(message))

        client_dict[client_id] = (client_socket,
                                  objects.Player(client_id, 0, 0, strToRGB(str(client_id))))

        pygame.event.post(pygame.event.Event(EVENT_PLAYER_JOINED,
                                             client_id=client_id))

        print(f"{client_id} connected to the server!")
        print(f"Active clients {len(client_dict)}: {list(client_dict.keys())}")


def send_state(level_objects: pygame.sprite.Group, client_dict: dict[uuid.UUID, tuple[socket.socket, objects.Player]]) -> None:
    """
    Sends the state of the game to all the clients so they can stay synced.

    ---
    :param level_objects: all objects in the level (players AND obstacles)
    :param client_dict: the dictionary that stores the clients

    ---
    :return: None
    """
    full_state = {
        "LEVEL_LAYOUT": {},
        "PLAYERS": {}
    }

    for obj in level_objects:
        if isinstance(obj, objects.Obstacle):
            message = {
                "X": obj.rect.x,
                "Y": obj.rect.y,
                "WIDTH": obj.rect.width,
                "HEIGHT": obj.rect.height,
                "COLOR": obj.color
            }
            full_state["LEVEL_LAYOUT"][str(obj.id)] = message

        elif isinstance(obj, objects.Player):
            message = {
                "X": obj.pos.x,
                "Y": obj.pos.y,
                "COLOR": obj.color
            }
            full_state["PLAYERS"][str(obj.id)] = message

    for _, (client_socket, _) in client_dict.items():
        protocol.send_message(client_socket,
                              json.dumps(full_state))


def get_input(client_dict: dict[uuid.UUID, tuple[socket.socket, objects.Player]]) -> dict[uuid.UUID, list[str]]:
    """
    Goes through all the clients and checks if they have sent any data (actions)

    this also handles the disconnection of clients
    ---
    :param client_dict: the dictionary that stores the clients

    ---
    :return: a dictionary with each client's id and the actions they have sent
    """
    inputs: dict[uuid.UUID, list[str]] = {}
    for client_id, (client_socket, _) in list(client_dict.items()):
        # Check if the client has sent any data
        ready_to_read, _, _ = select.select([client_socket], [], [], 0)

        if ready_to_read:
            message = protocol.receive_message(client_socket)
            message = json.loads(message)

            if "QUIT" in message:
                protocol.send_message(client_socket, "QUIT")
                client_socket.close()
                del client_dict[client_id]
                print(f"{client_id} disconnected from the server!")
                print(
                    f"Active clients {len(client_dict)}: {list(client_dict.keys())}")
                continue

            inputs[client_id] = message

        else:
            # if the client didn't send any data, then he didn't do any actions
            inputs[client_id] = []

    return inputs


def init_level() -> pygame.sprite.Group:
    """
    Creates the beginning layout of the level

    ---
    :return: a group of all the objects in the level
    """
    group = pygame.sprite.Group()
    # Floor
    floor = objects.Obstacle(0, 500, 800, 100, (0, 60, 0))
    group.add(floor)

    # Walls
    wall1 = objects.Obstacle(0, 0, 100, 600, (0, 60, 0))
    wall2 = objects.Obstacle(700, 0, 100, 600, (0, 60, 0))
    group.add(wall1, wall2)

    # Obstacles
    obstacle1 = objects.Obstacle(200, 200, 100, 100, (0, 60, 0))
    obstacle2 = objects.Obstacle(400, 200, 100, 100, (0, 60, 0))
    group.add(obstacle1, obstacle2)

    return group


def main():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8820))

    # Create a dictionary to store the client's id and (socket object, player object)
    client_dict: dict[uuid.UUID, tuple[socket.socket, objects.Player]] = {}

    # Create a new thread to handle the client
    thread = threading.Thread(target=receive_clients,
                              args=(server_socket, client_dict))
    thread.start()

    # No need for a display since we're not rendering anything on the server
    # window = pygame.display.set_mode((800, 600))
    # pygame.display.set_caption("Synced Pygame - Server")
    pygame.display.init()

    clock = pygame.time.Clock()

    sprites = pygame.sprite.Group()
    level_obstacles = init_level()
    sprites.add(level_obstacles)
    players = pygame.sprite.Group()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == EVENT_PLAYER_JOINED:
                client_id = event.client_id
                _, player = client_dict[client_id]
                sprites.add(player)
                players.add(player)

                player.setPos(130, 100)

        actions = get_input(client_dict)
        for client_id, action in actions.items():
            client_dict[client_id][1].update(action)
            # client_dict[client_id][1].update(action, level_obstacles)

        send_state(sprites, client_dict)

        clock.tick(FRAME_RATE)


if __name__ == '__main__':
    main()
