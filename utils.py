from enums import Colour
import numpy as np
from config import *
# from goSim import GoEnv
from copy import copy, deepcopy



# util_simulator = GoEnv()
# goenv = GoEnv(player_color=PLAYER_COLOR, observation_type='image3c', illegal_move_mode="raise", board_size=BOARD_SIZE, komi=KOMI_VALUE)

# Observation is of the form (3 x 13 x 13)
# State is of the form (2* timesteps + 1) x 13 x 13

# def simulatorNextObservation(obs, action, player_colour):
#     i, j = getCoordinatesFromActions(action)
#     if(obs[player_colour][i][j] == 0):
#         obs[player_colour][i][j] = 1
#         assert(obs[2][i][j] == 1)
#         obs[2][i][j] = 0

#     else:
#         return False
    



def stateToObs(state):
    upperTwo = state[:2, :, :]
    player_colour = state[16, 0, 0] # TODO: CHECK
    obs = np.zeros((3, upperTwo.shape[1], upperTwo.shape[2]))
    if(player_colour == Colour.WHITE.value):
        obs[0, :, :] = upperTwo[1, :, :]
        obs[1, :, :] = upperTwo[0, :, :]
    else:
        obs[0:2, :,  :] = upperTwo[0:2,:, : ]
    obs[2, :, :] = np.logical_not(np.logical_or(obs[0, :, :], obs[1, :, :]))
    return obs   

# Observation is of the form (3 x 13 x 13)
# Prev State is of the form (2* timesteps + 1) x 13 x 13
def obsToState(obs, prev_state):
    new_state = np.zeros(prev_state.shape)
    new_state[0:2, :, :] = obs[0:2, :, :]
    new_state[2:16, :, :] = prev_state[:14, :, :] 
    new_state[16,  :, :] = prev_state[16,  :, :] # color is changed
    return new_state

def invertObs(obs):
    new_obs = deepcopy(obs)
    new_obs[0, :, :] = obs[1, :, :]
    new_obs[1, :, :] = obs[0, :, :]
    return new_obs   

def obsToString(obs):
    game = ""
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if(obs[0][i][j] == 1):
                game += "X"
            elif(obs[1][i][j] == 1):
                game += "O"
            else:
                game += "."
        game += "\n"
    return game


def initState():
    state = np.zeros((NUM_FEATURES, BOARD_SIZE, BOARD_SIZE))
    state[NUM_FEATURES - 1, :, :] = 1
    return state

def copySimulator(sim):
    new_sim = copy(sim)
    new_sim.state = copy(sim.state)
    return new_sim

def getNextState(state, obs):
    new_state = np.array(state)
    for i in range(0, 13, 2):
        new_state[i+2, :, :] = state[i+1, :, :]
        new_state[i+3, :, :] = state[i, :, :]
    new_state[16, :, :] = 3 - state[16, :, :]
    player_color = new_state[16, 0, 0]

    if(player_color == Colour.BLACK.value):
        new_state[0:2, :, :] = obs[0:2, :, :]
    else:
        new_state[0, :, :] = obs[1, :, :]
        new_state[1, :, :] = obs[0, :, :]

    return new_state

def getValidMoves(obs, player_colour):
    """
    Input:
        board: current board
        player: current player
    Returns:
        validMoves: a binary vector of length self.getActionSize(), 1 for
                    moves that are valid from the current board and player,
                    0 for invalid moves
    """
    validActions = np.zeros(NUM_ACTIONS)
    for action in range(NUM_ACTIONS):
        is_legal_action = util_simulator.is_legal_Action(obs, action, player_colour)
        if(is_legal_action):
            validActions[action] = 1
    
    return validActions       

def getCoordinatesFromActions(action):
    return action / BOARD_SIZE, action % BOARD_SIZE

def getActionFromCoordinates(i, j):
    return i * BOARD_SIZE + j

def transformAction(action):
    i, j = getCoordinatesFromActions(action)
    orig_i = i
    orig_j = j
    
    actions = []
    for i in range(3):
        j1 = i
        i1 = BOARD_SIZE - 1 - j
        i = i1
        j = j1
        act = getActionFromCoordinates(i, j)
        actions.append(act)
    actions.append(getActionFromCoordinates(BOARD_SIZE - 1 - orig_i, orig_j))
    actions.append(getActionFromCoordinates(orig_i, BOARD_SIZE - 1 - orig_j))
    return actions
    
    
'''
    Inputs:
        mat: A 2-D square matrix
        N: Size of matrix
    Returns:
        mat: Rotated matrix by 90 degrees anti-clockwise
'''
def rotateMatrix(mat): 
    mat = deepcopy(mat)
    N = BOARD_SIZE
    for x in range(0, int(N/2)): 
        for y in range(x, N-x-1): 
            temp = mat[x][y] 
            mat[x][y] = mat[y][N-1-x] 
            mat[y][N-1-x] = mat[N-1-x][N-1-y] 
            mat[N-1-x][N-1-y] = mat[N-1-y][x] 
            mat[N-1-y][x] = temp
    return mat 

def get2DSymmetries(obs):
    flippedMat1 = getAllFlipped2D(obs[0, :, :])
    flippedMat2 = getAllFlipped2D(obs[1, :, :])
    flippedMat3 = getAllFlipped2D(obs[2, :, :])
    allNewObs = []
    for mat1, mat2, mat3 in zip(flippedMat1, flippedMat2, flippedMat3):
        newObs = np.zeros(obs.shape)
        newObs[0, :, :] = mat1
        newObs[1, :, :] = mat2
        newObs[2, :, :] = mat3
        allNewObs.append(newObs)
    return np.asarray(allNewObs)

def getAllSymmetries(frame):
    rot1 = rotateMatrix(frame)
    rot2 = rotateMatrix(rot1)
    rot3 = rotateMatrix(rot2)
    flip1 = np.flip(frame, axis=0)
    flip2 = np.flip(frame, axis=1)
    return np.asarray([rot1, rot2, rot3, flip1, flip2]).reshape((5, BOARD_SIZE, BOARD_SIZE))

# Returns (5 x 17 x 13 x 13)
def getSymmetries(state):
    allSymmetries = []
    for frame in state:
        symmetries = getAllSymmetries(frame)
        allSymmetries.append(symmetries)
    allSymmetries = np.asarray(allSymmetries).reshape((NUM_CHANNELS, 5, BOARD_SIZE, BOARD_SIZE))
    np.transpose(allSymmetries, (1, 0, 2, 3))
    return allSymmetries

