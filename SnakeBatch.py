#!/usr/bin/env python
# coding: utf-8

# # Setup

# In[1]:


import itertools
sqs = [''.join(s) for s in list(itertools.product(*[['0','1']] * 4))]
widths = ['0','1','NA']
heights = ['2','3','NA']

states = {}
for i in widths:
	for j in heights:
		for k in sqs:
			states[str((i,j,k))] = [0,0,0,0]


# # Learner

# In[2]:


import random
import dataclasses
import sys

# Redirect stdout and stderr to a file
sys.stdout = open('output.log', 'w')
sys.stderr = sys.stdout

@dataclasses.dataclass
class GameState:
    distance: tuple
    position: tuple
    surroundings: str
    food: tuple

class Learner:
    def __init__(self, display_width, display_height, block_size):
        # Game parameters
        self.display_width = display_width
        self.display_height = display_height
        self.block_size = block_size

        # Learning parameters
        self.epsilon = 0.1
        self.lr = 0.7
        self.discount = 0.5

        # State/Action history
        self.history = []

        # Action space
        self.actions = {
            0: 'left',
            1: 'right',
            2: 'up',
            3: 'down'
        }

        # In-memory Q-values
        self.qvalues = self.initialize_qvalues()

    def initialize_qvalues(self):
        sqs = [''.join(s) for s in list(itertools.product(*[['0', '1']] * 4))]
        widths = ['0', '1', 'NA']
        heights = ['2', '3', 'NA']

        states = {}
        for i in widths:
            for j in heights:
                for k in sqs:
                    states[str((i, j, k))] = [0, 0, 0, 0]

        return states

    def Reset(self):
        self.history = []

    def LoadQvalues(self, qvalues):
        self.qvalues = qvalues

    def SaveQvalues(self):
        return self.qvalues

    def act(self, snake, food):
        state = self._GetState(snake, food)
        # Epsilon greedy
        rand = random.uniform(0, 1)
        if rand < self.epsilon:
            action_key = random.choices(list(self.actions.keys()))[0]
        else:
            state_scores = self.qvalues[self._GetStateStr(state)]
            action_key = state_scores.index(max(state_scores))
        action_val = self.actions[action_key]

        # Remember the actions it took at each state
        self.history.append({
            'state': state,
            'action': action_key
        })
        return action_val

    def UpdateQValues(self, reason):
        history = self.history[::-1]
        for i, h in enumerate(history[:-1]):
            if reason:
                sN = history[0]['state']
                aN = history[0]['action']
                state_str = self._GetStateStr(sN)
                reward = -1
                self.qvalues[state_str][aN] = (1 - self.lr) * self.qvalues[state_str][aN] + self.lr * reward
                reason = None
            else:
                s1 = h['state']
                s0 = history[i + 1]['state']
                a0 = history[i + 1]['action']
                x1 = s0.distance[0]
                y1 = s0.distance[1]
                x2 = s1.distance[0]
                y2 = s1.distance[1]
                if s0.food != s1.food:
                    reward = 1
                elif (abs(x1) > abs(x2) or abs(y1) > abs(y2)):
                    reward = 0.5
                else:
                    reward = -0.5
                state_str = self._GetStateStr(s0)
                new_state_str = self._GetStateStr(s1)
                self.qvalues[state_str][a0] = (1 - self.lr) * (self.qvalues[state_str][a0]) + self.lr * (
                            reward + self.discount * max(self.qvalues[new_state_str]))

    def _GetState(self, snake, food):
        snake_head = snake[-1]
        dist_x = food[0] - snake_head[0]
        dist_y = food[1] - snake_head[1]
        if dist_x > 0:
            pos_x = '1'
        elif dist_x < 0:
            pos_x = '0'
        else:
            pos_x = 'NA'
        if dist_y > 0:
            pos_y = '3'
        elif dist_y < 0:
            pos_y = '2'
        else:
            pos_y = 'NA'
        sqs = [
            (snake_head[0] - self.block_size, snake_head[1]),
            (snake_head[0] + self.block_size, snake_head[1]),
            (snake_head[0], snake_head[1] - self.block_size),
            (snake_head[0], snake_head[1] + self.block_size),
        ]
        surrounding_list = []
        for sq in sqs:
            if sq[0] < 0 or sq[1] < 0:
                surrounding_list.append('1')
            elif sq[0] >= self.display_width or sq[1] >= self.display_height:
                surrounding_list.append('1')
            elif sq in snake[:-1]:
                surrounding_list.append('1')
            else:
                surrounding_list.append('0')
        surroundings = ''.join(surrounding_list)
        return GameState((dist_x, dist_y), (pos_x, pos_y), surroundings, food)

    def _GetStateStr(self, state):
        return str((state.position[0], state.position[1], state.surroundings))


# CONSTANTS
BLOCK_SIZE = 10
DIS_WIDTH = 600
DIS_HEIGHT = 400

QVALUES_N = 100
FRAMESPEED = 500000

# Game
def GameLoop():
    x1 = DIS_WIDTH / 2
    y1 = DIS_HEIGHT / 2
    x1_change = 0
    y1_change = 0
    snake_list = [(x1, y1)]
    length_of_snake = 1

    foodx = round(random.randrange(0, DIS_WIDTH - BLOCK_SIZE) / 10.0) * 10.0
    foody = round(random.randrange(0, DIS_HEIGHT - BLOCK_SIZE) / 10.0) * 10.0

    dead = False
    reason = None
    while not dead:
        action = learner.act(snake_list, (foodx, foody))
        if action == "left":
            x1_change = -BLOCK_SIZE
            y1_change = 0
        elif action == "right":
            x1_change = BLOCK_SIZE
            y1_change = 0
        elif action == "up":
            y1_change = -BLOCK_SIZE
            x1_change = 0
        elif action == "down":
            y1_change = BLOCK_SIZE
            x1_change = 0

        x1 += x1_change
        y1 += y1_change
        snake_head = (x1, y1)
        snake_list.append(snake_head)

        if x1 >= DIS_WIDTH or x1 < 0 or y1 >= DIS_HEIGHT or y1 < 0:
            reason = 'Screen'
            dead = True

        if snake_head in snake_list[:-1]:
            reason = 'Tail'
            dead = True

        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, DIS_WIDTH - BLOCK_SIZE) / 10.0) * 10.0
            foody = round(random.randrange(0, DIS_HEIGHT - BLOCK_SIZE) / 10.0) * 10.0
            length_of_snake += 1

        if len(snake_list) > length_of_snake:
            del snake_list[0]

        learner.UpdateQValues(reason)

    return length_of_snake - 1, reason

# Usage
game_count = 1

learner = Learner(DIS_WIDTH, DIS_HEIGHT, BLOCK_SIZE)

while True:
    learner.Reset()
    if game_count > 100:
        learner.epsilon = 0
    else:
        learner.epsilon = 0.1
    score, reason = GameLoop()
    print(f"Games: {game_count}; Score: {score}; Reason: {reason}")

    if game_count % QVALUES_N == 0:
        saved_qvalues = learner.SaveQvalues()
        learner.LoadQvalues(saved_qvalues)
    game_count += 1


# In[ ]:




