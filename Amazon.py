import tkinter as tk
from tkinter import messagebox, filedialog
import random
import json
import os
import sys
import math
import time

class AmazonChess:
    def __init__(self):
        self.board_size = 10
        self.board = []
        self.current_player = 'H'  # 'H' for human, 'A' for AI
        self.selected_piece = None
        self.game_over = False
        self.move_phase = 0  # 0: select piece, 1: move to position, 2: place obstacle
        self.from_pos = None
        self.valid_moves = []  # 存储当前选中棋子的可移动位置
        self.valid_obstacles = []  # 存储可放置障碍的位置
        self.move_history = []  # 存储移动历史用于悔棋
        self.winner = None  # 存储获胜者
        self.ai_difficulty = 1  # 默认简单AI
        self.search_nodes = 0  # 记录搜索节点数（用于调试）
        self.init_board()
        
    def init_board(self):
        """初始化棋盘 - 标准亚马逊棋布局"""
        self.board = [['.' for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # 标准亚马逊棋初始位置 (10x10棋盘)
        # 人类棋子: H (白色)
        # AI棋子: A (黑色)
        
        # 人类棋子初始位置
        self.board[0][3] = 'H'
        self.board[0][6] = 'H'
        self.board[3][0] = 'H'
        self.board[3][9] = 'H'
        
        # AI棋子初始位置
        self.board[9][3] = 'A'
        self.board[9][6] = 'A'
        self.board[6][0] = 'A'
        self.board[6][9] = 'A'
    
    def get_valid_moves_from_position(self, pos):
        """获取从给定位置的所有合法移动位置"""
        valid_positions = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),  # 左上，上，右上
            (0, -1),           (0, 1),   # 左，右
            (1, -1),  (1, 0),  (1, 1)    # 左下，下，右下
        ]
        
        for dx, dy in directions:
            x, y = pos[0] + dx, pos[1] + dy
            while 0 <= x < self.board_size and 0 <= y < self.board_size:
                if self.board[x][y] == '.':
                    valid_positions.append((x, y))
                    x += dx
                    y += dy
                else:
                    break
                    
        return valid_positions
    
    def get_valid_obstacles_from_position(self, pos, from_pos=None):
        """获取从给定位置的所有合法障碍放置位置"""
        valid_positions = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),  # 左上，上，右上
            (0, -1),           (0, 1),   # 左，右
            (1, -1),  (1, 0),  (1, 1)    # 左下，下，右下
        ]
        
        # 首先，棋子移动前的位置肯定是合法的障碍位置
        if from_pos and from_pos != pos:
            if self.is_valid_obstacle(from_pos, from_pos, pos):
                if from_pos not in valid_positions:
                    valid_positions.append(from_pos)
        
        # 然后，从移动后的位置向8个方向射线搜索
        for dx, dy in directions:
            x, y = pos[0] + dx, pos[1] + dy
            while 0 <= x < self.board_size and 0 <= y < self.board_size:
                # 位置必须是空的
                if self.board[x][y] == '.':
                    # 不能放在棋子当前的位置
                    if (x, y) != pos and self.is_valid_obstacle((x, y), from_pos, pos):
                        valid_positions.append((x, y))
                    x += dx
                    y += dy
                else:
                    # 遇到非空位置，停止这个方向
                    break
        
        # 检查移动前位置所在的那条直线路径上的所有空位
        if from_pos and from_pos != pos:
            # 确定移动方向
            if from_pos[0] == pos[0]:  # 同一行，水平移动
                # 检查移动前位置左边的所有空位
                for j in range(from_pos[1]-1, -1, -1):
                    if self.board[from_pos[0]][j] == '.':
                        if (from_pos[0], j) not in valid_positions and self.is_valid_obstacle((from_pos[0], j), from_pos, pos):
                            valid_positions.append((from_pos[0], j))
                    else:
                        break
                # 检查移动前位置右边的所有空位
                for j in range(from_pos[1]+1, self.board_size):
                    if self.board[from_pos[0]][j] == '.':
                        if (from_pos[0], j) not in valid_positions and self.is_valid_obstacle((from_pos[0], j), from_pos, pos):
                            valid_positions.append((from_pos[0], j))
                    else:
                        break
            
            elif from_pos[1] == pos[1]:  # 同一列，垂直移动
                # 检查移动前位置上方的所有空位
                for i in range(from_pos[0]-1, -1, -1):
                    if self.board[i][from_pos[1]] == '.':
                        if (i, from_pos[1]) not in valid_positions and self.is_valid_obstacle((i, from_pos[1]), from_pos, pos):
                            valid_positions.append((i, from_pos[1]))
                    else:
                        break
                # 检查移动前位置下方的所有空位
                for i in range(from_pos[0]+1, self.board_size):
                    if self.board[i][from_pos[1]] == '.':
                        if (i, from_pos[1]) not in valid_positions and self.is_valid_obstacle((i, from_pos[1]), from_pos, pos):
                            valid_positions.append((i, from_pos[1]))
                    else:
                        break
            
            else:  # 对角线移动
                # 检查移动前位置对角线上的所有空位
                dx_dir = 1 if pos[0] > from_pos[0] else -1
                dy_dir = 1 if pos[1] > from_pos[1] else -1
                
                # 检查移动前位置反方向的所有空位
                x, y = from_pos[0] - dx_dir, from_pos[1] - dy_dir
                while 0 <= x < self.board_size and 0 <= y < self.board_size:
                    if self.board[x][y] == '.':
                        if (x, y) not in valid_positions and self.is_valid_obstacle((x, y), from_pos, pos):
                            valid_positions.append((x, y))
                        x -= dx_dir
                        y -= dy_dir
                    else:
                        break
        
        # 移除可能的重复项
        return list(set(valid_positions))
    
    def is_valid_move(self, from_pos, to_pos):
        """检查移动是否合法"""
        if not (0 <= to_pos[0] < self.board_size and 0 <= to_pos[1] < self.board_size):
            return False
            
        if self.board[to_pos[0]][to_pos[1]] != '.':
            return False
            
        # 检查是否在同一行、列或对角线
        if from_pos[0] != to_pos[0] and from_pos[1] != to_pos[1] and \
           abs(from_pos[0] - to_pos[0]) != abs(from_pos[1] - to_pos[1]):
            return False
            
        # 检查路径上是否有障碍
        dx = 0 if from_pos[0] == to_pos[0] else (1 if to_pos[0] > from_pos[0] else -1)
        dy = 0 if from_pos[1] == to_pos[1] else (1 if to_pos[1] > from_pos[1] else -1)
        
        x, y = from_pos[0] + dx, from_pos[1] + dy
        while (x, y) != to_pos:
            if self.board[x][y] != '.':
                return False
            x += dx
            y += dy
            
        return True
    
    def is_valid_obstacle(self, pos, from_pos, selected_piece):
        """检查障碍位置是否合法"""
        if not (0 <= pos[0] < self.board_size and 0 <= pos[1] < self.board_size):
            return False

        # 不能放在棋子当前的位置
        if pos == selected_piece:
            return False

        # 位置必须是空的
        if self.board[pos[0]][pos[1]] != '.':
            return False

        return True
    
    def has_legal_moves(self, player):
        """检查玩家是否有合法移动"""
        # 检查该玩家的每个棋子是否有合法移动
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == player:
                    # 检查这个棋子能否移动
                    moves = self.get_valid_moves_from_position((i, j))
                    if moves:  # 如果有可移动的位置
                        # 还需要检查移动后是否能放置障碍
                        for move in moves:
                            obstacles = self.get_valid_obstacles_from_position(move, (i, j))
                            if obstacles:
                                return True
        return False
    
    def check_game_over(self):
        """检查游戏是否结束"""
        # 检查当前玩家是否有合法移动
        if not self.has_legal_moves(self.current_player):
            self.game_over = True
            # 对方获胜
            self.winner = 'H' if self.current_player == 'A' else 'A'
            return True
        return False
    
    def make_move(self, from_pos, to_pos, obstacle_pos):
        """执行移动"""
        # 保存当前状态到历史记录
        board_copy = [row[:] for row in self.board]
        self.move_history.append({
            'board': board_copy,
            'current_player': self.current_player,
            'from_pos': from_pos,
            'to_pos': to_pos,
            'obstacle_pos': obstacle_pos,
            'game_over': self.game_over,
            'winner': self.winner
        })
        
        player = self.board[from_pos[0]][from_pos[1]]
        self.board[from_pos[0]][from_pos[1]] = '.'  # 移动前的位置变空
        self.board[to_pos[0]][to_pos[1]] = player
        self.board[obstacle_pos[0]][obstacle_pos[1]] = 'X'
        
        # 切换玩家
        self.current_player = 'A' if self.current_player == 'H' else 'H'
        
        # 检查游戏是否结束
        if self.check_game_over():
            return self.winner  # 返回获胜者
        
        return None  # 游戏继续
    
    def undo_move(self):
        """悔棋"""
        if len(self.move_history) == 0:
            return False
            
        last_move = self.move_history.pop()
        self.board = last_move['board']
        self.current_player = last_move['current_player']
        self.game_over = last_move['game_over']
        self.winner = last_move['winner']
        
        # 重置选择状态
        self.selected_piece = None
        self.from_pos = None
        self.move_phase = 0
        self.valid_moves = []
        self.valid_obstacles = []
        
        return True
    
    def get_all_possible_moves(self, player):
        """获取玩家所有可能的移动"""
        moves = []
        
        # 收集玩家的所有棋子
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == player:
                    piece = (i, j)
                    valid_moves = self.get_valid_moves_from_position(piece)
                    
                    for move in valid_moves:
                        # 对于每个移动位置，生成所有可能的障碍放置
                        valid_obstacles = self.get_valid_obstacles_from_position(move, piece)
                        
                        for obstacle in valid_obstacles:
                            moves.append((piece, move, obstacle))
        
        return moves
    
    def get_ai_move_simple_random(self):
        """简单的AI：随机选择一个合法移动"""
        # 收集AI的所有棋子
        ai_pieces = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 'A':
                    ai_pieces.append((i, j))
        
        # 随机尝试移动
        random.shuffle(ai_pieces)
        for piece in ai_pieces:
            # 获取所有可能的移动位置
            valid_moves = self.get_valid_moves_from_position(piece)
            random.shuffle(valid_moves)
            
            for move in valid_moves:
                # 获取所有可能的障碍位置
                valid_obstacles = self.get_valid_obstacles_from_position(move, piece)
                if valid_obstacles:
                    # 随机选择一个障碍位置
                    obstacle = random.choice(valid_obstacles)
                    return piece, move, obstacle
        
        # 如果没有找到合法移动，返回None
        return None
    
    def get_ai_move_smart_random(self):
        """聪明一点的随机AI：优先移动到中心区域"""
        # 收集AI的所有棋子
        ai_pieces = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 'A':
                    ai_pieces.append((i, j))
        
        # 计算中心点
        center = (self.board_size // 2, self.board_size // 2)
        
        # 为每个可能的移动打分
        best_move = None
        best_score = -1
        
        for piece in ai_pieces:
            valid_moves = self.get_valid_moves_from_position(piece)
            
            for move in valid_moves:
                valid_obstacles = self.get_valid_obstacles_from_position(move, piece)
                if valid_obstacles:
                    # 选择最好的障碍位置
                    for obstacle in valid_obstacles:
                        # 计算分数：移动位置离中心越近越好
                        move_dist = abs(move[0] - center[0]) + abs(move[1] - center[1])
                        score = 100 - move_dist
                        
                        # 障碍位置离对方棋子越近越好
                        min_human_dist = float('inf')
                        for i in range(self.board_size):
                            for j in range(self.board_size):
                                if self.board[i][j] == 'H':
                                    dist = abs(obstacle[0] - i) + abs(obstacle[1] - j)
                                    if dist < min_human_dist:
                                        min_human_dist = dist
                        
                        if min_human_dist < float('inf'):
                            score += (10 - min_human_dist) * 5
                        
                        if score > best_score:
                            best_score = score
                            best_move = (piece, move, obstacle)
        
        if best_move:
            return best_move
        
        # 如果没有找到移动，回退到简单随机
        return self.get_ai_move_simple_random()
    
    def evaluate_board_state(self, board=None):
        """评估当前棋盘状态（启发式评估函数）"""
        if board is None:
            board = self.board
            
        # 如果游戏结束，返回极端值
        if hasattr(self, 'game_over_temp') and self.game_over_temp:
            winner = self.winner_temp
            if winner == 'A':
                return 10000  # AI获胜
            elif winner == 'H':
                return -10000  # 人类获胜
        
        score = 0
        board_size = len(board)
        
        # 1. 移动自由度（权重40%）
        ai_mobility = 0
        human_mobility = 0
        
        for i in range(board_size):
            for j in range(board_size):
                if board[i][j] == 'A':
                    # 计算AI棋子的移动自由度
                    moves = self.get_valid_moves_from_position_on_board((i, j), board)
                    ai_mobility += len(moves)
                elif board[i][j] == 'H':
                    # 计算人类棋子的移动自由度
                    moves = self.get_valid_moves_from_position_on_board((i, j), board)
                    human_mobility += len(moves)
        
        # AI的移动自由度加分，人类的移动自由度减分
        mobility_score = (ai_mobility - human_mobility) * 10
        
        # 2. 战略控制（权重30%）
        center_control = 0
        # 中心区域（4x4的中心区域）
        center_start = board_size // 2 - 2
        center_end = board_size // 2 + 2
        
        for i in range(max(0, center_start), min(board_size, center_end)):
            for j in range(max(0, center_start), min(board_size, center_end)):
                if board[i][j] == 'A':
                    # 离中心越近，价值越高
                    dist_to_center = abs(i - board_size//2) + abs(j - board_size//2)
                    center_control += (8 - dist_to_center) * 3
                elif board[i][j] == 'H':
                    dist_to_center = abs(i - board_size//2) + abs(j - board_size//2)
                    center_control -= (8 - dist_to_center) * 3
        
        # 3. 威胁与安全（权重20%）
        threat_score = 0
        
        # 检查人类棋子是否被限制
        for i in range(board_size):
            for j in range(board_size):
                if board[i][j] == 'H':
                    moves = self.get_valid_moves_from_position_on_board((i, j), board)
                    mobility = len(moves)
                    # 如果移动能力很低，说明被限制了
                    if mobility <= 3:
                        threat_score += (4 - mobility) * 20
        
        # 检查AI棋子是否被威胁
        for i in range(board_size):
            for j in range(board_size):
                if board[i][j] == 'A':
                    moves = self.get_valid_moves_from_position_on_board((i, j), board)
                    mobility = len(moves)
                    # 如果移动能力很低，说明被威胁了
                    if mobility <= 3:
                        threat_score -= (4 - mobility) * 20
        
        # 4. 发展潜力（权重10%）
        potential_score = 0
        
        # 评估棋子的未来发展空间
        for i in range(board_size):
            for j in range(board_size):
                if board[i][j] == 'A':
                    # 检查周围8个方向是否有障碍或边界
                    open_directions = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            x, y = i + dx, j + dy
                            if 0 <= x < board_size and 0 <= y < board_size:
                                if board[x][y] == '.':
                                    open_directions += 1
                    potential_score += open_directions * 2
                elif board[i][j] == 'H':
                    open_directions = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            x, y = i + dx, j + dy
                            if 0 <= x < board_size and 0 <= y < board_size:
                                if board[x][y] == '.':
                                    open_directions += 1
                    potential_score -= open_directions * 2
        
        # 综合评分（应用权重）
        score = (mobility_score * 0.4) + (center_control * 0.3) + (threat_score * 0.2) + (potential_score * 0.1)
        
        return score
    
    def get_valid_moves_from_position_on_board(self, pos, board):
        """在指定棋盘上获取从给定位置的所有合法移动位置"""
        valid_positions = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        board_size = len(board)
        
        for dx, dy in directions:
            x, y = pos[0] + dx, pos[1] + dy
            while 0 <= x < board_size and 0 <= y < board_size:
                if board[x][y] == '.':
                    valid_positions.append((x, y))
                    x += dx
                    y += dy
                else:
                    break
                    
        return valid_positions
    
    def get_valid_obstacles_from_position_on_board(self, pos, board, from_pos=None):
        """在指定棋盘上获取从给定位置的所有合法障碍放置位置"""
        valid_positions = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        board_size = len(board)
        
        # 首先，棋子移动前的位置肯定是合法的障碍位置
        if from_pos and from_pos != pos:
            # 检查移动前位置是否为空
            if board[from_pos[0]][from_pos[1]] == '.':
                if from_pos not in valid_positions:
                    valid_positions.append(from_pos)
        
        # 然后，从移动后的位置向8个方向射线搜索
        for dx, dy in directions:
            x, y = pos[0] + dx, pos[1] + dy
            while 0 <= x < board_size and 0 <= y < board_size:
                # 位置必须是空的
                if board[x][y] == '.':
                    # 不能放在棋子当前的位置
                    if (x, y) != pos:
                        valid_positions.append((x, y))
                    x += dx
                    y += dy
                else:
                    # 遇到非空位置，停止这个方向
                    break
        
        # 检查移动前位置所在的那条直线路径上的所有空位
        if from_pos and from_pos != pos:
            # 确定移动方向
            if from_pos[0] == pos[0]:  # 同一行，水平移动
                # 检查移动前位置左边的所有空位
                for j in range(from_pos[1]-1, -1, -1):
                    if board[from_pos[0]][j] == '.':
                        if (from_pos[0], j) not in valid_positions:
                            valid_positions.append((from_pos[0], j))
                    else:
                        break
                # 检查移动前位置右边的所有空位
                for j in range(from_pos[1]+1, board_size):
                    if board[from_pos[0]][j] == '.':
                        if (from_pos[0], j) not in valid_positions:
                            valid_positions.append((from_pos[0], j))
                    else:
                        break
            
            elif from_pos[1] == pos[1]:  # 同一列，垂直移动
                # 检查移动前位置上方的所有空位
                for i in range(from_pos[0]-1, -1, -1):
                    if board[i][from_pos[1]] == '.':
                        if (i, from_pos[1]) not in valid_positions:
                            valid_positions.append((i, from_pos[1]))
                    else:
                        break
                # 检查移动前位置下方的所有空位
                for i in range(from_pos[0]+1, board_size):
                    if board[i][from_pos[1]] == '.':
                        if (i, from_pos[1]) not in valid_positions:
                            valid_positions.append((i, from_pos[1]))
                    else:
                        break
            
            else:  # 对角线移动
                # 检查移动前位置对角线上的所有空位
                dx_dir = 1 if pos[0] > from_pos[0] else -1
                dy_dir = 1 if pos[1] > from_pos[1] else -1
                
                # 检查移动前位置反方向的所有空位
                x, y = from_pos[0] - dx_dir, from_pos[1] - dy_dir
                while 0 <= x < board_size and 0 <= y < board_size:
                    if board[x][y] == '.':
                        if (x, y) not in valid_positions:
                            valid_positions.append((x, y))
                        x -= dx_dir
                        y -= dy_dir
                    else:
                        break
        
        # 移除可能的重复项
        return list(set(valid_positions))
    
    def get_all_possible_moves_on_board(self, board, player):
        """在指定棋盘上获取玩家所有可能的移动"""
        moves = []
        board_size = len(board)
        
        # 收集玩家的所有棋子
        for i in range(board_size):
            for j in range(board_size):
                if board[i][j] == player:
                    piece = (i, j)
                    valid_moves = self.get_valid_moves_from_position_on_board(piece, board)
                    
                    for move in valid_moves:
                        # 对于每个移动位置，生成所有可能的障碍放置
                        valid_obstacles = self.get_valid_obstacles_from_position_on_board(move, board, piece)
                        
                        for obstacle in valid_obstacles:
                            moves.append((piece, move, obstacle))
        
        return moves
    
    def make_move_on_board(self, board, move):
        """在指定棋盘上执行移动"""
        from_pos, to_pos, obstacle_pos = move
        
        # 保存原始棋子
        player = board[from_pos[0]][from_pos[1]]
        
        # 执行移动
        board[from_pos[0]][from_pos[1]] = '.'
        board[to_pos[0]][to_pos[1]] = player
        board[obstacle_pos[0]][obstacle_pos[1]] = 'X'
        
        return board
    
    def minimax(self, board, depth, alpha, beta, maximizing_player, max_depth, start_time, max_time):
        """Minimax算法，带有Alpha-Beta剪枝和迭代深化"""
        self.search_nodes += 1
        
        # 检查时间限制
        if time.time() - start_time > max_time:
            return self.evaluate_board_state(board), None
        
        # 检查深度限制
        if depth >= max_depth:
            return self.evaluate_board_state(board), None
        
        # 获取当前玩家
        current_player = 'A' if maximizing_player else 'H'
        
        # 获取所有可能移动
        moves = self.get_all_possible_moves_on_board(board, current_player)
        
        # 如果没有合法移动，游戏结束
        if not moves:
            # 检查游戏是否结束
            game_over = False
            winner = None
            
            # 检查当前玩家是否有合法移动
            has_moves = False
            for i in range(len(board)):
                for j in range(len(board)):
                    if board[i][j] == current_player:
                        moves_check = self.get_valid_moves_from_position_on_board((i, j), board)
                        if moves_check:
                            for move in moves_check:
                                obstacles = self.get_valid_obstacles_from_position_on_board(move, board, (i, j))
                                if obstacles:
                                    has_moves = True
                                    break
                        if has_moves:
                            break
                if has_moves:
                    break
            
            if not has_moves:
                game_over = True
                winner = 'H' if current_player == 'A' else 'A'
                
                # 如果是AI的回合且无法移动，人类获胜
                if maximizing_player:
                    return -10000 + depth, None  # 人类获胜，AI应该避免这种情况
                else:
                    return 10000 - depth, None  # AI获胜，AI应该追求这种情况
        
        # 对移动进行排序（启发式排序，提高Alpha-Beta剪枝效率）
        if maximizing_player:
            # AI的回合：按评估分数降序排序
            scored_moves = []
            for move in moves:
                temp_board = [row[:] for row in board]
                temp_board = self.make_move_on_board(temp_board, move)
                score = self.evaluate_board_state(temp_board)
                scored_moves.append((score, move))
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            moves = [move for score, move in scored_moves]
        else:
            # 人类的回合：按评估分数升序排序（人类会选择对AI最不利的走法）
            scored_moves = []
            for move in moves:
                temp_board = [row[:] for row in board]
                temp_board = self.make_move_on_board(temp_board, move)
                score = self.evaluate_board_state(temp_board)
                scored_moves.append((score, move))
            scored_moves.sort(key=lambda x: x[0])
            moves = [move for score, move in scored_moves]
        
        # 限制分支因子（只考虑前N个最好的移动）
        max_branching = 20 if depth == 0 else 15
        moves = moves[:max_branching]
        
        if maximizing_player:  # AI走棋（最大化玩家）
            max_eval = float('-inf')
            best_move = None
            
            for move in moves:
                # 创建棋盘副本
                new_board = [row[:] for row in board]
                new_board = self.make_move_on_board(new_board, move)
                
                # 递归评估
                eval_score, _ = self.minimax(new_board, depth + 1, alpha, beta, False, max_depth, start_time, max_time)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta剪枝
            
            return max_eval, best_move
            
        else:  # 人类走棋（最小化玩家）
            min_eval = float('inf')
            best_move = None
            
            for move in moves:
                # 创建棋盘副本
                new_board = [row[:] for row in board]
                new_board = self.make_move_on_board(new_board, move)
                
                # 递归评估
                eval_score, _ = self.minimax(new_board, depth + 1, alpha, beta, True, max_depth, start_time, max_time)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha剪枝
            
            return min_eval, best_move
    
    def get_ai_move_minimax(self, max_time=3):
        """AI走棋 - 使用Minimax算法（难度3）"""
        self.search_nodes = 0
        start_time = time.time()
        
        # 首先检查AI是否有合法移动
        if not self.has_legal_moves('A'):
            return None  # AI无法移动，游戏应该结束
        
        # 迭代深化搜索
        best_move = None
        best_score = float('-inf')
        
        # 初始搜索深度
        depth = 2
        max_depth = 4  # 最大搜索深度
        
        while depth <= max_depth and time.time() - start_time < max_time:
            current_board = [row[:] for row in self.board]
            
            # 执行Minimax搜索
            score, move = self.minimax(
                board=current_board,
                depth=0,
                alpha=float('-inf'),
                beta=float('inf'),
                maximizing_player=True,
                max_depth=depth,
                start_time=start_time,
                max_time=max_time
            )
            
            # 如果找到了更好的移动，更新
            if move is not None:
                best_move = move
                best_score = score
            
            # 如果分数非常高（接近获胜），提前返回
            if score > 5000:
                break
            
            # 增加搜索深度
            depth += 1
        
        # 记录搜索信息（用于调试）
        search_time = time.time() - start_time
        print(f"AI搜索完成: 深度={depth-1}, 节点数={self.search_nodes}, 时间={search_time:.2f}秒")
        
        if best_move:
            return best_move
        else:
            # 如果Minimax没有返回移动，则回退到聪明随机
            return self.get_ai_move_smart_random()
    
    def get_ai_move(self):
        """AI走棋 - 根据难度选择算法"""
        # 首先检查AI是否有合法移动
        if not self.has_legal_moves('A'):
            return None  # AI无法移动，游戏应该结束
        
        if self.ai_difficulty == 1:  # 简单AI：完全随机
            return self.get_ai_move_simple_random()
        elif self.ai_difficulty == 2:  # 中等AI：聪明随机
            return self.get_ai_move_smart_random()
        else:  # 困难AI：使用Minimax算法
            return self.get_ai_move_minimax(max_time=3)

class AmazonChessGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("亚马逊棋")
        
        # 设置窗口初始位置和大小
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 900
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.game = AmazonChess()
        self.cell_size = 60
        self.colors = {
            'H': '#FFFFFF',  # 白色棋子（人类）
            'A': '#000000',  # 黑色棋子（AI）
            'X': '#808080',  # 灰色障碍
            '.': '#f0d9b5',  # 浅色格子
            'dark': '#b58863',  # 深色格子
            'highlight': '#90EE90',  # 高亮选中的棋子（浅绿色）
            'move_highlight': '#ADD8E6',  # 可移动位置（浅蓝色）
            'obstacle_highlight': '#FFD700'  # 可放置障碍的位置（金黄色）
        }
        
        self.ai_thinking = False
        self.last_move_count = 0
        self.search_info = ""  # 存储AI搜索信息
        
        self.create_menu()
        self.create_widgets()
        self.draw_board()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_menu(self):
        """创建菜单"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="游戏", menu=game_menu)
        game_menu.add_command(label="新游戏", command=self.new_game)
        game_menu.add_command(label="保存游戏", command=self.save_game)
        game_menu.add_command(label="加载游戏", command=self.load_game)
        game_menu.add_separator()
        game_menu.add_command(label="退出", command=self.on_closing)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="AI难度", command=self.set_ai_difficulty)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="游戏规则", command=self.show_rules)
        help_menu.add_command(label="操作说明", command=self.show_instructions)
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(self.root, text="亚马逊棋", font=("楷体", 24, "bold"), fg="#8B4513")
        title_label.pack(pady=10)
        
        # 棋盘区域
        self.canvas_frame = tk.Frame(self.root, bg="#8B4513", bd=3, relief=tk.RAISED)
        self.canvas_frame.pack(pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, 
                               width=self.cell_size * self.game.board_size + 4,
                               height=self.cell_size * self.game.board_size + 4,
                               bg="#8B4513", highlightthickness=0)
        self.canvas.pack(padx=2, pady=2)
        self.canvas.bind("<Button-1>", self.on_click)
        
        # 状态显示
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        self.status_label = tk.Label(self.status_frame, text="轮到人类玩家", 
                                    font=("宋体", 16), fg="blue")
        self.status_label.pack()
        
        self.phase_label = tk.Label(self.status_frame, text="请选择一个棋子", 
                                   font=("宋体", 12))
        self.phase_label.pack()
        
        # 游戏信息显示
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(side=tk.TOP, pady=10)
        
        # 棋子统计
        self.piece_count_label = tk.Label(self.info_frame, text="棋子: 人类 4 - 4 AI", 
                                         font=("宋体", 12))
        self.piece_count_label.pack(side=tk.LEFT, padx=20)
        
        # 移动计数
        self.move_count_label = tk.Label(self.info_frame, text="移动: 0", 
                                        font=("宋体", 12))
        self.move_count_label.pack(side=tk.LEFT, padx=20)
        
        # AI难度显示
        self.ai_difficulty_label = tk.Label(self.info_frame, text=f"AI难度: {self.game.ai_difficulty} (简单)", 
                                           font=("宋体", 12))
        self.ai_difficulty_label.pack(side=tk.LEFT, padx=20)
        
        # AI搜索信息显示
        self.search_info_label = tk.Label(self.info_frame, text="", 
                                         font=("宋体", 10), fg="#666666")
        self.search_info_label.pack(side=tk.LEFT, padx=20)
        
        # 控制按钮
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.TOP, pady=15)
        
        button_config = [
            ("新游戏", self.new_game, "#4CAF50"),
            ("保存", self.save_game, "#2196F3"),
            ("加载", self.load_game, "#FF9800"),
            ("AI走棋", self.ai_move, "#9C27B0"),
            ("悔棋", self.undo_move, "#F44336"),
            ("提示", self.show_hint, "#00BCD4"),
            ("测试AI", self.test_ai_moves, "#FF5722")
        ]
        
        for text, command, color in button_config:
            btn = tk.Button(self.button_frame, text=text, command=command, 
                           width=10, bg=color, fg="white", font=("宋体", 10))
            btn.pack(side=tk.LEFT, padx=5)
        
        # 信息显示框
        self.info_text_frame = tk.Frame(self.root)
        self.info_text_frame.pack(side=tk.TOP, pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.info_text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_text = tk.Text(self.info_text_frame, height=6, width=80, 
                                font=("宋体", 10), yscrollcommand=scrollbar.set)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.info_text.yview)
        
        self.info_text.insert(tk.END, "游戏开始！\n")
        self.info_text.insert(tk.END, "请选择您的棋子开始游戏。\n")
        self.info_text.config(state=tk.DISABLED)
    
    def draw_board(self):
        """绘制棋盘"""
        self.canvas.delete("all")
        
        # 绘制棋盘格子
        for i in range(self.game.board_size):
            for j in range(self.game.board_size):
                x1 = j * self.cell_size + 2
                y1 = i * self.cell_size + 2
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                # 交替颜色
                if (i + j) % 2 == 0:
                    fill_color = self.colors['.']
                else:
                    fill_color = self.colors['dark']
                
                # 高亮选中的棋子
                if self.game.selected_piece == (i, j):
                    fill_color = self.colors['highlight']
                
                # 高亮可移动的位置（第一阶段）
                if self.game.move_phase == 1 and (i, j) in self.game.valid_moves:
                    fill_color = self.colors['move_highlight']
                
                # 高亮可放置障碍的位置（第二阶段）
                if self.game.move_phase == 2 and (i, j) in self.game.valid_obstacles:
                    fill_color = self.colors['obstacle_highlight']
                
                # 绘制格子
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, 
                                           outline="black", width=1)
                
                # 绘制棋子或障碍
                piece = self.game.board[i][j]
                if piece != '.':
                    cx = x1 + self.cell_size // 2
                    cy = y1 + self.cell_size // 2
                    radius = self.cell_size // 3
                    
                    if piece == 'X':  # 障碍
                        # 绘制灰色方块
                        self.canvas.create_rectangle(cx - radius, cy - radius, 
                                                    cx + radius, cy + radius,
                                                    fill=self.colors[piece], 
                                                    outline="black", width=2)
                        # 在障碍上画X
                        self.canvas.create_line(cx - radius//2, cy - radius//2,
                                              cx + radius//2, cy + radius//2,
                                              fill="black", width=2)
                        self.canvas.create_line(cx - radius//2, cy + radius//2,
                                              cx + radius//2, cy - radius//2,
                                              fill="black", width=2)
                    else:  # 棋子
                        # 绘制棋子（圆形）
                        self.canvas.create_oval(cx - radius, cy - radius,
                                               cx + radius, cy + radius,
                                               fill=self.colors[piece], 
                                               outline="black", width=2)
                        
                        # 添加棋子标识
                        text_color = "black" if piece == 'H' else "white"
                        self.canvas.create_text(cx, cy, text=piece, 
                                              font=("Arial", 12, "bold"),
                                              fill=text_color)
        
        # 更新状态显示
        self.update_status()
    
    def update_status(self):
        """更新状态显示"""
        # 检查游戏是否结束
        if self.game.game_over:
            winner_text = "人类" if self.game.winner == 'H' else "AI"
            self.status_label.config(text=f"游戏结束！{winner_text}获胜！", fg="red")
            
            # 禁用棋盘点击
            self.canvas.unbind("<Button-1>")
        else:
            player = "人类" if self.game.current_player == 'H' else "AI"
            color = "blue" if self.game.current_player == 'H' else "red"
            self.status_label.config(text=f"轮到 {player} 玩家", fg=color)
            
            # 如果轮到AI且没有AI正在思考，则触发AI移动
            if self.game.current_player == 'A' and not self.ai_thinking:
                self.root.after(500, self.ai_move)
            
        # 更新阶段提示
        phases = ["请选择一个棋子", "请选择移动目标位置", "请选择放置障碍的位置"]
        if self.game.move_phase < len(phases):
            self.phase_label.config(text=phases[self.game.move_phase])
        
        # 更新棋子统计
        human_count = sum(1 for i in range(self.game.board_size) 
                         for j in range(self.game.board_size) 
                         if self.game.board[i][j] == 'H')
        ai_count = sum(1 for i in range(self.game.board_size) 
                      for j in range(self.game.board_size) 
                      if self.game.board[i][j] == 'A')
        self.piece_count_label.config(text=f"棋子: 人类 {human_count} - {ai_count} AI")
        
        # 更新移动计数
        move_count = len(self.game.move_history)
        self.move_count_label.config(text=f"移动: {move_count}")
        
        # 更新难度显示
        difficulty_names = ["简单", "中等", "困难"]
        difficulty_name = difficulty_names[min(self.game.ai_difficulty - 1, len(difficulty_names) - 1)]
        self.ai_difficulty_label.config(text=f"AI难度: {self.game.ai_difficulty} ({difficulty_name})")
        
        # 更新搜索信息
        self.search_info_label.config(text=self.search_info)
        
        # 更新信息显示
        self.info_text.config(state=tk.NORMAL)
        
        # 只在游戏变化时添加新信息
        if not hasattr(self, 'last_move_count'):
            self.last_move_count = 0
            
        if move_count > self.last_move_count:
            self.info_text.insert(tk.END, f"\n移动 #{move_count} 完成")
            self.last_move_count = move_count
            
            # 如果游戏结束，添加游戏结束信息
            if self.game.game_over:
                winner_text = "人类" if self.game.winner == 'H' else "AI"
                self.info_text.insert(tk.END, f"\n游戏结束！{winner_text}获胜！\n")
        
        # 滚动到最后
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def on_click(self, event):
        """处理棋盘点击事件"""
        if self.game.game_over or self.game.current_player == 'A' or self.ai_thinking:
            return
            
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        
        if not (0 <= row < self.game.board_size and 0 <= col < self.game.board_size):
            return
        
        # 坐标转换（考虑边框）
        if row < 0 or col < 0:
            return
        
        # 改进点1：如果点击的是已选中的棋子，取消选中
        if self.game.move_phase == 0 and self.game.selected_piece == (row, col):
            self.game.selected_piece = None
            self.game.valid_moves = []
            self.draw_board()
            return
            
        if self.game.move_phase == 0:  # 选择棋子阶段
            if self.game.board[row][col] == 'H':
                self.game.selected_piece = (row, col)
                self.game.from_pos = (row, col)
                self.game.move_phase = 1
                
                # 改进点2：显示可移动的位置
                self.game.valid_moves = self.game.get_valid_moves_from_position((row, col))
                
        elif self.game.move_phase == 1:  # 选择移动目标
            # 如果点击的是可移动位置
            if (row, col) in self.game.valid_moves:
                self.game.selected_piece = (row, col)
                self.game.move_phase = 2
                
                # 显示可放置障碍的位置，包括移动前的位置和它所在直线上的所有空位
                self.game.valid_obstacles = self.game.get_valid_obstacles_from_position((row, col), self.game.from_pos)
                    
            # 如果点击的是其他棋子
            elif self.game.board[row][col] == 'H':
                # 改为选择这个棋子
                self.game.selected_piece = (row, col)
                self.game.from_pos = (row, col)
                self.game.valid_moves = self.game.get_valid_moves_from_position((row, col))
                
        elif self.game.move_phase == 2:  # 选择障碍位置
            # 如果点击的是可放置障碍的位置
            if (row, col) in self.game.valid_obstacles:
                # 执行移动
                result = self.game.make_move(self.game.from_pos, self.game.selected_piece, (row, col))
                
                # 在信息框中记录移动
                self.info_text.config(state=tk.NORMAL)
                from_coord = f"{chr(65+self.game.from_pos[1])}{self.game.from_pos[0]+1}"
                to_coord = f"{chr(65+self.game.selected_piece[1])}{self.game.selected_piece[0]+1}"
                obstacle_coord = f"{chr(65+col)}{row+1}"
                self.info_text.insert(tk.END, f"\n人类移动: {from_coord} -> {to_coord}, 障碍在 {obstacle_coord}")
                self.info_text.config(state=tk.DISABLED)
                
                # 重置状态
                self.game.selected_piece = None
                self.game.from_pos = None
                self.game.move_phase = 0
                self.game.valid_moves = []
                self.game.valid_obstacles = []
                
                # 检查游戏结果
                if result is not None:
                    winner = "人类" if result == 'H' else "AI"
                    messagebox.showinfo("游戏结束", f"{winner}获胜！")
                
                self.draw_board()
            # 如果点击的是已选中的棋子位置
            elif (row, col) == self.game.selected_piece:
                # 回到第一阶段，但保持选择这个位置作为目标
                self.game.move_phase = 1
        
        self.draw_board()
    
    def ai_move(self):
        """AI走棋 - 使用相应难度的算法"""
        if self.game.game_over or self.game.current_player != 'A' or self.ai_thinking:
            return
        
        self.ai_thinking = True
            
        # 显示AI正在思考
        self.status_label.config(text="AI正在思考...", fg="purple")
        self.root.update()
        
        # 检查AI是否有合法移动
        if not self.game.has_legal_moves('A'):
            self.game.game_over = True
            self.game.winner = 'H'
            self.status_label.config(text="游戏结束！人类获胜！", fg="red")
            self.draw_board()
            messagebox.showinfo("游戏结束", "AI无法移动，人类获胜！")
            self.ai_thinking = False
            return
        
        # 获取AI移动
        move = self.game.get_ai_move()
        
        if move:
            from_pos, to_pos, obstacle_pos = move
            
            # 在信息框中显示AI的移动
            self.info_text.config(state=tk.NORMAL)
            from_coord = f"{chr(65+from_pos[1])}{from_pos[0]+1}"
            to_coord = f"{chr(65+to_pos[1])}{to_pos[0]+1}"
            obstacle_coord = f"{chr(65+obstacle_pos[1])}{obstacle_pos[0]+1}"
            self.info_text.insert(tk.END, f"\nAI移动: {from_coord} -> {to_coord}, 障碍在 {obstacle_coord}")
            
            # 如果是困难AI，添加搜索信息
            if self.game.ai_difficulty == 3:
                self.info_text.insert(tk.END, f"\n搜索信息: {self.search_info}")
            
            self.info_text.see(tk.END)
            self.info_text.config(state=tk.DISABLED)
            
            # 执行移动
            result = self.game.make_move(from_pos, to_pos, obstacle_pos)
            
            if result is not None:
                winner = "人类" if result == 'H' else "AI"
                messagebox.showinfo("游戏结束", f"{winner}获胜！")
        else:
            # AI没有合法移动，人类获胜
            self.game.game_over = True
            self.game.winner = 'H'
            messagebox.showinfo("游戏结束", "AI无法移动，人类获胜！")
        
        self.ai_thinking = False
        self.search_info = ""  # 清空搜索信息
        self.draw_board()
    
    def test_ai_moves(self):
        """测试AI可以进行的移动（调试用）"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, "\n=== AI移动测试 ===")
        
        # 获取所有可能的AI移动
        ai_moves = self.game.get_all_possible_moves('A')
        self.info_text.insert(tk.END, f"\nAI可能的移动数: {len(ai_moves)}")
        
        # 显示前几个可能的移动
        for i, move in enumerate(ai_moves[:5]):
            from_pos, to_pos, obstacle_pos = move
            from_coord = f"{chr(65+from_pos[1])}{from_pos[0]+1}"
            to_coord = f"{chr(65+to_pos[1])}{to_pos[0]+1}"
            obstacle_coord = f"{chr(65+obstacle_pos[1])}{obstacle_pos[0]+1}"
            self.info_text.insert(tk.END, f"\n移动 {i+1}: {from_coord} -> {to_coord}, 障碍在 {obstacle_coord}")
        
        # 测试评估函数
        score = self.game.evaluate_board_state()
        self.info_text.insert(tk.END, f"\n当前局面评估分数: {score:.2f}")
        
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def new_game(self):
        """开始新游戏"""
        self.game = AmazonChess()
        self.ai_thinking = False
        self.last_move_count = 0
        self.search_info = ""
        
        # 重新绑定棋盘点击事件
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "新游戏开始！\n")
        self.info_text.insert(tk.END, "请选择您的棋子开始游戏。\n")
        self.info_text.config(state=tk.DISABLED)
        
        self.draw_board()
        messagebox.showinfo("新游戏", "新游戏已开始！")
    
    def save_game(self):
        """保存游戏"""
        if self.ai_thinking:
            messagebox.showwarning("保存失败", "AI正在思考，请稍后再试")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            game_state = {
                'board': self.game.board,
                'current_player': self.game.current_player,
                'game_over': self.game.game_over,
                'winner': self.game.winner,
                'move_history': self.game.move_history,
                'selected_piece': self.game.selected_piece,
                'from_pos': self.game.from_pos,
                'move_phase': self.game.move_phase,
                'valid_moves': self.game.valid_moves,
                'valid_obstacles': self.game.valid_obstacles,
                'ai_difficulty': self.game.ai_difficulty
            }
            
            try:
                with open(filename, 'w') as f:
                    json.dump(game_state, f, indent=2)
                
                messagebox.showinfo("保存成功", "游戏已保存！")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存游戏时出错: {str(e)}")
    
    def load_game(self):
        """加载游戏"""
        if self.ai_thinking:
            messagebox.showwarning("加载失败", "AI正在思考，请稍后再试")
            return
            
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    game_state = json.load(f)
                
                self.game.board = game_state['board']
                self.game.current_player = game_state['current_player']
                self.game.game_over = game_state['game_over']
                self.game.winner = game_state['winner']
                self.game.move_history = game_state['move_history']
                self.game.selected_piece = tuple(game_state['selected_piece']) if game_state['selected_piece'] else None
                self.game.from_pos = tuple(game_state['from_pos']) if game_state['from_pos'] else None
                self.game.move_phase = game_state['move_phase']
                self.game.valid_moves = [tuple(pos) for pos in game_state['valid_moves']]
                self.game.valid_obstacles = [tuple(pos) for pos in game_state['valid_obstacles']]
                self.game.ai_difficulty = game_state.get('ai_difficulty', 1)
                
                # 重新绑定棋盘点击事件
                if not self.game.game_over:
                    self.canvas.bind("<Button-1>", self.on_click)
                
                self.ai_thinking = False
                self.last_move_count = len(self.game.move_history)
                self.search_info = ""
                
                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "游戏已加载！\n")
                if self.game.game_over:
                    winner = "人类" if self.game.winner == 'H' else "AI"
                    self.info_text.insert(tk.END, f"游戏状态: {winner}获胜\n")
                else:
                    current_player = "人类" if self.game.current_player == 'H' else "AI"
                    self.info_text.insert(tk.END, f"当前玩家: {current_player}\n")
                self.info_text.config(state=tk.DISABLED)
                
                self.draw_board()
                messagebox.showinfo("加载成功", "游戏已加载！")
            except Exception as e:
                messagebox.showerror("加载失败", f"加载游戏时出错: {str(e)}")
    
    def undo_move(self):
        """悔棋功能"""
        if self.ai_thinking:
            messagebox.showwarning("悔棋失败", "AI正在思考，请稍后再试")
            return
            
        if self.game.undo_move():
            # 重新绑定棋盘点击事件
            self.canvas.bind("<Button-1>", self.on_click)
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.insert(tk.END, "\n已撤销上一步移动")
            self.info_text.config(state=tk.DISABLED)
            
            self.draw_board()
        else:
            messagebox.showwarning("悔棋", "无法悔棋")
    
    def show_hint(self):
        """显示提示"""
        if self.game.current_player == 'H' and self.game.selected_piece:
            moves = self.game.get_valid_moves_from_position(self.game.selected_piece)
            if moves:
                # 随机选择一个移动作为提示
                hint_move = random.choice(moves)
                hint_obstacles = self.game.get_valid_obstacles_from_position(hint_move, self.game.selected_piece)
                if hint_obstacles:
                    hint_obstacle = random.choice(hint_obstacles)
                    
                    messagebox.showinfo("提示", 
                        f"建议移动:\n从 ({self.game.selected_piece[0]+1},{chr(65+self.game.selected_piece[1])}) "
                        f"移动到 ({hint_move[0]+1},{chr(65+hint_move[1])})\n"
                        f"然后在 ({hint_obstacle[0]+1},{chr(65+hint_obstacle[1])}) 放置障碍")
            else:
                messagebox.showwarning("提示", "选中的棋子无法移动")
    
    def set_ai_difficulty(self):
        """设置AI难度"""
        difficulty = tk.simpledialog.askinteger("AI难度", "设置AI难度 (1=简单, 2=中等, 3=困难):", 
                                               minvalue=1, maxvalue=3, initialvalue=self.game.ai_difficulty)
        if difficulty:
            self.game.ai_difficulty = difficulty
            difficulty_names = ["简单", "中等", "困难"]
            difficulty_name = difficulty_names[min(difficulty - 1, len(difficulty_names) - 1)]
            messagebox.showinfo("AI难度", f"AI难度已设置为 {difficulty} ({difficulty_name})")
            self.draw_board()
    
    def show_rules(self):
        """显示游戏规则"""
        rules = """
亚马逊棋规则：

1. 棋盘：10x10方格棋盘
2. 棋子：每方有4个亚马逊（人类：白色，AI：黑色）
3. 移动规则：
   a) 选择一个己方亚马逊（像国际象棋的后：横、竖、斜任意距离）
   b) 移动到空白位置（不能穿越其他棋子或障碍）
   c) 在移动后的位置放置一个障碍（灰色方块）
4. 障碍规则：
   - 障碍永久存在，不能移动或移除
   - 不能放在有棋子或其他障碍的位置
   - 可以放在棋子移动前的位置（该位置现在为空）
   - 也可以放在棋子移动前位置所在直线路径上的任何空位
5. 胜负条件：
   - 当一方无法移动任何亚马逊时，游戏立即结束，对方获胜
   - 注意：即使棋子还在棋盘上，如果无法移动就输了
        """
        messagebox.showinfo("游戏规则", rules)
    
    def show_instructions(self):
        """显示操作说明"""
        instructions = """
操作说明：

1. 选择棋子：
   - 点击己方的白色棋子
   - 选中的棋子会变为绿色
   - 可移动的位置会显示为浅蓝色

2. 移动棋子：
   - 点击浅蓝色的格子移动棋子
   - 移动后，棋子会到达新位置

3. 放置障碍：
   - 移动后，可放置障碍的位置会显示为金黄色
   - 点击金黄色格子放置障碍
   - 注意：棋子移动前的位置也可以放置障碍
   - 棋子移动前位置所在直线路径上的所有空位也可以放置障碍

4. 取消选择：
   - 点击已选中的棋子可以取消选择
   - 或选择其他棋子

5. 控制按钮：
   - 新游戏：开始新游戏
   - 保存/加载：保存或读取游戏进度

6. AI难度：
   - 简单：随机移动
   - 中等：优先移动到中心区域
   - 困难：使用Minimax搜索算法，思考更深

7. 游戏结束：
   - 当一方无法移动任何棋子时，游戏立即结束
   - 获胜方会收到通知
        """
        messagebox.showinfo("操作说明", instructions)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if messagebox.askokcancel("退出", "确定要退出游戏吗？"):
            self.root.destroy()
    
    def run(self):
        """运行游戏"""
        self.root.mainloop()

def main():
    """主函数，处理可能的异常"""
    try:
        game_gui = AmazonChessGUI()
        game_gui.run()
    except Exception as e:
        print(f"程序运行时出错: {e}")
        print("请确保已安装Python并正确配置环境。")
        input("按Enter键退出...")

if __name__ == "__main__":
    main()