"""Main module."""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1101
import os

import multiprocessing
import time
import itertools
import names
import config

from env.server import Server
from env.player import Player
from ai.oracle import start_ai

schedule = {}
ai_processes = {}
server_threads = {}
player_processes = {}
ai_version = os.listdir('/data/gobang/aipath')
ai_version = ['Perez-0005']
for (ai1, ai2) in itertools.combinations_with_replacement(ai_version, 2):
    schedule[(ai1, ai2)] = 0

# reduce self-AI play
for ai in ai_version:
    schedule[(ai, ai)] = config.NUMPARALELL * 2

for ai in ai_version:
    ai_processes[ai] = multiprocessing.Process(target=start_ai, args=(ai, ))
    ai_processes[ai].start()

time.sleep(4)

for match in schedule:
    for num in range(schedule[match]):
        server_id = '%s_%s_%d' % (match[0], match[1], num)
        player1_id = '%s_%s' % (names.get_first_name(), match[0])
        while player1_id in player_processes:
            player1_id = '%s_%s' % (names.get_first_name(), match[0])
        player2_id = '%s_%s' % (names.get_first_name(), match[1])
        while player2_id in player_processes:
            player2_id = '%s_%s' % (names.get_first_name(), match[1])
        print(server_id, player1_id, player2_id, sep='\t')
        server_threads[server_id] = Server(server_id, player1_id, player2_id)
        server_threads[server_id].start()
        player_processes[player1_id] = Player(server_id, player1_id, num == 0)
        player_processes[player1_id].start()
        player_processes[player2_id] = Player(server_id, player2_id, num == 0)
        player_processes[player2_id].start()
