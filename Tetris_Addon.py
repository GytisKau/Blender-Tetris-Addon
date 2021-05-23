bl_info = {
    "name": "Play Tetris!",
    "description": "Bored? Good! Play the jankiest version of Tetris right here in Blender!",
    "author": "Gytis Kaulakis",
    "version": (2, 0),
    "blender": (3, 00, 0),
    "location": "View3D > Tetris",
    "support": "COMMUNITY",
    "category": "Games",
}

import random
import time
import copy
import numpy as np
import bpy
from bpy.types import Operator, Panel, AddonPreferences


class Properties(bpy.types.PropertyGroup):
    block : bpy.props.BoolProperty(default=False, name='')
    sizeX : bpy.props.IntProperty(default=10, name='', min=10, soft_max=50)
    sizeY : bpy.props.IntProperty(default=20, name='', min=10, soft_max=50)
    top_score : bpy.props.IntProperty(default=0, name='')
    random_icons : bpy.props.BoolProperty(default=False, name='')
    
colors = [[
    'COLLECTION_COLOR_01',
    'COLLECTION_COLOR_02',
    'COLLECTION_COLOR_03',
    'COLLECTION_COLOR_04',
    'COLLECTION_COLOR_05',
    'COLLECTION_COLOR_06',
    'COLLECTION_COLOR_07',]]
colors.append(bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys())

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
        self.color = random.randint(1, len(colors[0]) - 1)
        self.color2 = random.randint(1, len(colors[1]) - 1)
        if self.color2 == 92:
            self.color2 = 93
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
    field2 = []
    height = 0
    width = 0
    figure = None
    next_figure = None
    lines_broken = 0
    pieces_placed = 0

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.field = []
        self.field2 = []
        self.score = 0
        self.lines_broken = 0
        self.pieces_placed = 0
        
        self.state = "start"
        self.next_figure = Figure(self.width // 2 - 1, 0)
        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)
            self.field2.append(new_line[:])
        

    def new_figure(self):
        self.figure = self.next_figure
        self.next_figure = Figure(self.width // 2 - 1, 0)
        self.pieces_placed += 1

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
                        self.field2[i1][j] = self.field2[i1 - 1][j]
        self.score += lines ** 2
        self.lines_broken += lines

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
                    self.field2[i + self.figure.y][j + self.figure.x] = self.figure.color2
                    
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
game.state = "gameover"
    

class TetrisOperator(Operator):
    """Start Tetris"""
    bl_idname = "wm.play_tetris_operator"
    bl_label = "Play Tetris Operator"

    _timer = None
    
    done = False
    fps = 5
    counter = 0
    start_time = 0.0

    pressing_down = False
    
    def modal(self, context, event):
        props = context.scene.properties
        if __name__ != '__main__':
                addon_props = context.preferences.addons[__name__].preferences
                
        global game
        
        if event.type in {'RIGHTMOUSE', 'ESC'} or game.state == "gameover":
            self.cancel(context)
            game.state = "gameover"
            done = True
            
            if __name__ != '__main__':
                addon_props.time_played += time.time() - self.start_time
                addon_props.games_played += 1
                addon_props.lines_broken += game.lines_broken
                addon_props.pieces_placed += game.pieces_placed
                    
                if addon_props.global_top_score < game.score:
                    addon_props.global_top_score = game.score
                    self.report({'INFO'}, "New High Score: " + str(game.score) + "!")
                else:
                    self.report({'INFO'}, "Game over")
            else:
                if props.top_score < game.score:
                    props.top_score = game.score
                    self.report({'INFO'}, "New High Score: " + str(game.score) + "!")
                else:
                    self.report({'INFO'}, "Game over")
                
            return {'CANCELLED'}
        
        if game.figure is None:
            if __name__ != '__main__':
                addon_props.pieces_placed += 1
            game.new_figure()
        self.counter += 1
        if self.counter > 100000:
            self.counter = 0
        
        if self.counter % (self.fps // max(game.score//30, 1)) == 0:
            if game.state == "start":
                game.go_down()
    
        if event.value == 'PRESS':
            if event.type in {'UP_ARROW', 'W'}:
                game.rotate()
            if event.type in {'DOWN_ARROW', 'S'}:
                game.go_down()
            if event.type in {'LEFT_ARROW', 'A'}:
                game.go_side(-1)
            if event.type in {'RIGHT_ARROW', 'D'}:
                game.go_side(1)
            if event.type == 'SPACE':
                game.go_space()
            #if event.type == 'P':
            #    game.score += 1
                
        if event.value == 'RELEASE':
            if event.type in {'DOWN_ARROW', 'S'}:
                self.pressing_down = False
        
        # Hacky UI force update... idk how to do it otherwise
        if event.type == 'TIMER':
            bob = context.preferences.themes[0].view_3d.space.gradients.high_gradient
            bob.h += 0
            
        #return {'PASS_THROUGH'} #If you don't want to freze Blender while playing
        return {'RUNNING_MODAL'}
                    
    def execute(self, context):
        props = context.scene.properties
        
        global game
        
        self.report({'INFO'}, "Game started!")
        self.done = False
        self.fps = 24
        game = Tetris(props.sizeY, props.sizeX)
        self.counter = 0
        self.start_time = time.time()
        
        self.pressing_down = False
        
        game.new_figure()
        
        # timer update
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
    

    def draw(self, context):
        props = context.scene.properties
        if __name__ != '__main__':
            addon_props = context.preferences.addons[__name__].preferences
        layout = self.layout
        layout.use_property_decorate = False
        
        global game
        
        sizeX = props.sizeX
        sizeY = props.sizeY
        
        field = copy.deepcopy(game.field)
        field2 = copy.deepcopy(game.field2)
        
        # Add the flying figure to the frozen field
        if game.figure is not None:
            for i in range(4):
                for j in range(4):
                    p = i * 4 + j
                    if p in game.figure.image():
                        field[i + game.figure.y][j + game.figure.x] = game.figure.color
                        field2[i + game.figure.y][j + game.figure.x] = game.figure.color2
                        
        grid = layout.grid_flow(row_major=True, columns=sizeX, even_columns=True, even_rows=True, align=True)
        grid.enabled = False
                                          
        # Draw the main Tetris grid
        for i in range(game.height):
            for j in range(game.width):
                if field[i][j] > 0:
                    if props.random_icons:
                        grid.prop(props, "block", icon_only=True, icon=colors[1][field2[i][j]])
                    else:
                        grid.prop(props, "block", icon_only=True, icon=colors[0][field[i][j]])
                else:
                    grid.prop(props, "block", icon_only=True, icon='BLANK1')
                    
        
        # Draw game info and the Play button
        column = layout.column()
        row = column.row(align=True)
        row.alignment = 'CENTER'
        
        row.label(text="Score: " + str(game.score))
        if __name__ != '__main__':
            row.label(text="Top score: " + str(addon_props.global_top_score))
        else:
            row.label(text="Top score: " + str(props.top_score))
        row.operator('wm.play_tetris_operator', text="Play", icon='PLAY')
        
        # Make two columns with 'cf'
        #cf = layout.column_flow(columns=2, align=False)
        cf = layout.split(factor=110/context.region.width) # First container is Constant width
        column1 = cf.grid_flow(row_major=True, columns=4, even_columns=True, even_rows=True, align=True)
        column1.enabled = False
        
        column2 = cf.column()
        
        # Draw the preview grid
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if game.next_figure is not None and p in game.next_figure.image():
                    if props.random_icons:
                        column1.prop(props, "block", icon_only=True, icon=colors[1][game.next_figure.color2])
                    else:
                        column1.prop(props, "block", icon_only=True, icon=colors[0][game.next_figure.color])
                else:
                    column1.prop(props, "block", icon_only=True, icon='BLANK1')
                    
        # Draw the settings
        column2.prop(props, 'sizeX', text="Width")
        column2.prop(props, 'sizeY', text="Height")
        row = column2.row()
        row.scale_y = 2
        row.prop(props, 'random_icons', text="Random icons", toggle=1, expand=True)
        
        # Draw info of how to Cancel the game
        if game.state != "gameover":
            column = layout.column()
            row = column.row()
            row.label(text="Press ESC or RMB to stop", icon='QUESTION')


class Tetris_Preferences(AddonPreferences):
     bl_idname = __name__
     
     global_top_score : bpy.props.IntProperty(default=0, name='')
     games_played : bpy.props.IntProperty(default=0, name='')
     pieces_placed : bpy.props.IntProperty(default=0, name='')
     lines_broken : bpy.props.IntProperty(default=0, name='')
     time_played : bpy.props.FloatProperty(default=0, name='')
     
     
     def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Top score: " + str(self.global_top_score))
        row.label(text="Games played: " + str(self.games_played))
        row.label(text="Pieces placed: " + str(self.pieces_placed))
        row.label(text="Lines broken: " + str(self.lines_broken))
        time = int(self.time_played)
        h = time // 3600;
        m = (time - (h * 3600)) // 60;
        s = time - (h * 3600 + m * 60);
        
        row.label(text="Time played: %d hrs. %d min. %d s." % (h, m, s))

def register():
    # Panels
    bpy.utils.register_class(Tetris_Panel)
    
    bpy.utils.register_class(Properties)
    bpy.utils.register_class(Tetris_Preferences)
    bpy.types.Scene.properties = bpy.props.PointerProperty(type=Properties)
    
    # Operators
    bpy.utils.register_class(TetrisOperator)
    
def unregister():
    #Properties
    bpy.utils.unregister_class(Properties)
    del bpy.types.Scene.properties
    
    # Panels
    bpy.utils.unregister_class(Tetris_Panel)
    bpy.utils.unregister_class(Tetris_Preferences)
    
    # Operators
    bpy.utils.unregister_class(TetrisOperator)


if __name__ == '__main__':
    register()
    