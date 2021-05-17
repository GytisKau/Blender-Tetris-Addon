bl_info = {
    "name": "Play Tetris!",
    "description": "Bored? Good! Play the jankiest version of Tetris right here in Blender!",
    "author": "Gytis Kaulakis",
    "version": (1, 0),
    "blender": (3, 00, 0),
    "location": "View3D > Tetris",
    "support": "COMMUNITY",
    "category": "Games",
}

import random
import copy
import numpy as np
import bpy
from bpy.types import Operator, Panel


class Properties(bpy.types.PropertyGroup):
    level : bpy.props.IntProperty(default=1, name='')
    block : bpy.props.BoolProperty(default=False, name='')
    sizeX : bpy.props.IntProperty(default=10, name='')
    sizeY : bpy.props.IntProperty(default=20, name='')
    
colors = [
    'COLLECTION_COLOR_01',
    'COLLECTION_COLOR_02',
    'COLLECTION_COLOR_03',
    'COLLECTION_COLOR_04',
    'COLLECTION_COLOR_05',
    'COLLECTION_COLOR_06',
    'COLLECTION_COLOR_07',
]

class Figure:
    x = 0
    y = 0

    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],
        [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]],
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
        [[1, 2, 5, 6]],
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(self.figures) - 1)
        self.color = random.randint(1, len(colors) - 1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

class Tetris:
    level = 2
    score = 0
    state = "start"
    field = []
    height = 0
    width = 0
    figure = None

    def __init__(self, height, width):
        
        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.state = "start"
        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):
        self.figure = Figure(3, 0)

    def intersects(self):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y > self.height - 1 or \
                            j + self.figure.x > self.width - 1 or \
                            j + self.figure.x < 0 or \
                            self.field[i + self.figure.y][j + self.figure.x] > 0:
                        intersection = True
        return intersection

    def break_lines(self):
        lines = 0
        for i in range(1, self.height):
            zeros = 0
            for j in range(self.width):
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0:
                lines += 1
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
        self.score += lines ** 2

    def go_space(self):
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    def go_down(self):
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

game = Tetris(20, 10)
    

class TetrisOperator(bpy.types.Operator):
    """Operator witch starts the Tetris game"""
    bl_idname = "wm.play_tetris_operator"
    bl_label = "Play Tetris Operator"

    _timer = None
    
    done = False
    fps = 24
    counter = 0

    pressing_down = False
    
    def modal(self, context, event):
        props = context.scene.properties
        global game
        
        if event.type in {'RIGHTMOUSE'}:
            self.cancel(context)
            done = True
            return {'CANCELLED'}
        if game.state == "gameover":
            return {'CANCELLED'}
        
        if game.figure is None:
            game.new_figure()
        self.counter += 1
        if self.counter > 100000:
            self.counter = 0
        
        if self.counter % (self.fps // props.level // 1) == 0 or self.pressing_down:
            if game.state == "start":
                game.go_down()
        
    
        if event.value == 'PRESS':
            if event.type == 'UP_ARROW':
                game.rotate()
            if event.type == 'DOWN_ARROW':
                self.pressing_down = True
            if event.type == 'LEFT_ARROW':
                game.go_side(-1)
            if event.type == 'RIGHT_ARROW':
                game.go_side(1)
            if event.type == 'SPACE':
                game.go_space()
            if event.type == 'ESC':
                game.__init__(20, 10)
                
        if event.value == 'RELEASE':
            if event.type == 'DOWN_ARROW':
                self.pressing_down = False
        
        # Hacky force update... idk how to do it otherwise
        if event.type == 'TIMER':
            bob = context.preferences.themes[0].view_3d.space.gradients.high_gradient
            bob.h += 0
            
        #return {'PASS_THROUGH'}
        return {'RUNNING_MODAL'}
                    
    def execute(self, context):
        props = context.scene.properties
        global game
        
        self.done = False
        self.fps = 24
        game = Tetris(props.sizeY, props.sizeX)
        self.counter = 0
        
        self.pressing_down = False
        
        # Change background colors
        wm = context.window_manager
        self._timer = wm.event_timer_add(1/self.fps, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
            
class Tetris_Panel(Panel):
    bl_label = "Tetris"
    bl_idname = "OBJECT_PT_TETRIS_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ".objectmode"
    bl_category = "Tetris"
    bl_order = 3
    

    def draw(self, context):
        props = context.scene.properties
        layout = self.layout
        layout.use_property_decorate = False
        
        global game
        
        sizeX = props.sizeX
        sizeY = props.sizeY
        
        grid = layout.box().grid_flow(row_major=True, columns=sizeX, even_columns=True, even_rows=True, align=True)
        grid.enabled = False
        
        field = copy.deepcopy(game.field)
        
        if game.figure is not None:
            for i in range(4):
                for j in range(4):
                    p = i * 4 + j
                    if p in game.figure.image():
                        field[i + game.figure.y][j + game.figure.x] = game.figure.color
                                          
        for i in range(game.height):
            for j in range(game.width):
                if field[i][j] > 0:
                    grid.prop(props, "block", icon_only=True, icon=colors[field[i][j]])
                else:
                    grid.prop(props, "block", icon_only=True, icon='BLANK1')

        
        
        column = layout.column(align=True)
        row = column.row(align=True)
        row.alignment = 'CENTER'
        
        if game:
            row.label(text="Score: " + str(game.score))
            if game.state == "gameover":
                row.label(text="Game Over")
            
        row.operator('wm.play_tetris_operator', text="Play", icon='PLAY')
        
        row = column.row(align=True)
        row.label(text="Press the Right Mouse button to stop")
        
        row = column.row(align=True)
        row.prop(props, 'sizeX', text="Width")
        row = column.row(align=True)
        row.prop(props, 'sizeY', text="Height")
        row = column.row()
        row.prop(props, 'level', text="Speed")

def register():
    # Panels
    bpy.utils.register_class(Tetris_Panel)
    
    bpy.utils.register_class(Properties)
    bpy.types.Scene.properties = bpy.props.PointerProperty(type=Properties)
    
    # Operators
    bpy.utils.register_class(TetrisOperator)
    
def unregister():
    #Properties
    bpy.utils.unregister_class(Properties)
    del bpy.types.Scene.properties
    
    # Panels
    bpy.utils.unregister_class(Tetris_Panel)
    
    # Operators
    bpy.utils.unregister_class(TetrisOperator)


if __name__ == '__main__':
    register()
    