"""
This is the main entry of your program. Almost all things you need to implement is in this file.
The main class Sketch inherit from CanvasBase. For the parts you need to implement, they all marked.
First version Created on 09/28/2018

:author: micou(Zezhou Sun)
:version: 2021.2.1

"""

import os
import typing

import wx
import math
import random
import numpy as np

from Buff import Buff
from Point import Point
from ColorType import ColorType
from CanvasBase import CanvasBase

try:
    # From pip package "Pillow"
    from PIL import Image
except Exception:
    print("Need to install PIL package. Pip package name is Pillow")
    raise ImportError


class AxisCalcData:
    def __init__(self, init: int, final: int):
        delta = final - init
        self.delta = abs(delta)
        self.trans = 1 if delta >= 0 else -1
        self.init = init * self.trans
        self.final = final * self.trans


class Sketch(CanvasBase):
    """
    Please don't forget to override interrupt methods, otherwise NotImplementedError will throw out
    
    Class Variable Explanation:

    * debug(int): Define debug level for log printing

        * 0 for stable version, minimum log is printed
        * 1 will print general logs for lines and triangles
        * 2 will print more details and do some type checking, which might be helpful in debugging
    
    * texture(Buff): loaded texture in Buff instance
    * random_color(bool): Control flag of random color generation of point.
    * doTexture(bool): Control flag of doing texture mapping
    * doSmooth(bool): Control flag of doing smooth
    * doAA(bool): Control flag of doing anti-aliasing
    * doAAlevel(int): anti-aliasing super sampling level
        
    Method Instruction:

    * Interrupt_MouseL(R): Used to deal with mouse click interruption. Canvas will be refreshed with updated buff
    * Interrupt_Keyboard: Used to deal with keyboard press interruption. Use this to add new keys or new methods
    * drawPoint: method to draw a point
    * drawLine: method to draw a line
    * drawTriangle: method to draw a triangle with filling and smoothing
    
    List of methods to override the ones in CanvasBase:

    * Interrupt_MouseL
    * Interrupt_MouseR
    * Interrupt_Keyboard
        
    Here are some public variables in parent class you might need:

    * points_r: list<Point>. to store all Points from Mouse Right Button
    * points_l: list<Point>. to store all Points from Mouse Left Button
    * buff    : Buff. buff of current frame. Change on it will change display on screen
    * buff_last: Buff. Last frame buffer
        
    """

    debug = 0
    texture_file_path = "./pattern.jpg"
    texture = None

    # control flags
    randomColor = False
    doTexture = False
    doSmooth = False
    doAA = False
    doAAlevel = 4

    # test case status
    MIN_N_STEPS = 6
    MAX_N_STEPS = 192
    n_steps = 12  # For test case only
    test_case_index = 0
    test_case_list = []  # If you need more test case, write them as a method and add it to list

    def __init__(self, parent):
        """
        Initialize the instance, load texture file to Buff, and load test cases.

        :param parent: wxpython frame
        :type parent: wx.Frame
        """
        super(Sketch, self).__init__(parent)
        self.test_case_list = [lambda _: self.clear(),
                               self.testCaseLine01,
                               self.testCaseLine02,
                               self.testCaseTri01,
                               self.testCaseTri02,
                               self.testCaseTriTexture01]  # method at here must accept one argument, n_steps
        # Try to read texture file
        if os.path.isfile(self.texture_file_path):
            # Read image and make it to a ndarray
            texture_image = Image.open(self.texture_file_path)
            texture_array = np.array(texture_image).astype(np.uint8)
            # Because imported image is upside down, reverse it
            texture_array = np.flip(texture_array, axis=0)
            # Store texture image in our Buff format
            self.texture = Buff(texture_array.shape[1], texture_array.shape[0])
            self.texture.setStaticBuffArray(np.transpose(texture_array, (1, 0, 2)))
            if self.debug > 0:
                print("Texture Loaded with shape: ", texture_array.shape)
                print("Texture Buff have size: ", self.texture.size)
        else:
            raise ImportError("Cannot import texture file")

    def __addPoint2Pointlist(self, pointlist: typing.List[Point], x: int, y: int):
        if self.randomColor:
            p = Point((x, y), ColorType(random.random(), random.random(), random.random()))
        else:
            p = Point((x, y), ColorType(1, 0, 0))
        pointlist.append(p)

    # Deal with Mouse Left Button Pressed Interruption
    def Interrupt_MouseL(self, x: int, y: int):
        self.__addPoint2Pointlist(self.points_l, x, y)
        # Draw a point when one point provided or a line when two ends provided
        if len(self.points_l) % 2 == 1:
            if self.debug > 0:
                print("draw a point", self.points_l[-1])
            self.drawPoint(self.buff, self.points_l[-1])
        elif len(self.points_l) % 2 == 0 and len(self.points_l) > 0:
            if self.debug > 0:
                print("draw a line from ", self.points_l[-1], " -> ", self.points_l[-2])
            self.drawPoint(self.buff, self.points_l[-1])
            self.drawLine(self.buff, self.points_l[-2], self.points_l[-1],
                          self.doSmooth, self.doAA, self.doAAlevel)
            self.points_l.clear()

    # Deal with Mouse Right Button Pressed Interruption
    def Interrupt_MouseR(self, x: int, y: int):
        self.__addPoint2Pointlist(self.points_r, x, y)
        if len(self.points_r) % 3 == 1:
            if self.debug > 0:
                print("draw a point", self.points_r[-1])
            self.drawPoint(self.buff, self.points_r[-1])
        elif len(self.points_r) % 3 == 2:
            if self.debug > 0:
                print("draw a line from ", self.points_r[-1], " -> ", self.points_r[-2])
            self.drawLine(self.buff, self.points_r[-2], self.points_r[-1],
                          self.doSmooth, self.doAA, self.doAAlevel)
        elif len(self.points_r) % 3 == 0 and len(self.points_r) > 0:
            if self.debug > 0:
                print("draw a triangle {} -> {} -> {}".format(self.points_r[-3], self.points_r[-2], self.points_r[-1]))
            self.drawPoint(self.buff, self.points_r[-1])
            self.drawTriangle(self.buff, self.points_r[-3], self.points_r[-2], self.points_r[-1],
                              self.doSmooth, self.doAA, self.doAAlevel, self.doTexture)
            self.points_r.clear()

    def Interrupt_Keyboard(self, keycode: int):
        """
        keycode Reference: https://docs.wxpython.org/wx.KeyCode.enumeration.html#wx-keycode

        * r, R: Generate Random Color point
        * c, C: clear buff and screen
        * LEFT, UP: Last Test case
        * t, T, RIGHT, DOWN: Next Test case
        """
        # Trigger for test cases
        if keycode in [wx.WXK_LEFT, wx.WXK_UP]:  # Last Test Case
            self.clear()
            if len(self.test_case_list) != 0:
                self.test_case_index = (self.test_case_index - 1) % len(self.test_case_list)
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)
        if keycode in [ord("t"), ord("T"), wx.WXK_RIGHT, wx.WXK_DOWN]:  # Next Test Case
            self.clear()
            if len(self.test_case_list) != 0:
                self.test_case_index = (self.test_case_index + 1) % len(self.test_case_list)
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)
        if chr(keycode) in ",<":
            self.clear()
            self.n_steps = max(self.MIN_N_STEPS, round(self.n_steps / 2))
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)
        if chr(keycode) in ".>":
            self.clear()
            self.n_steps = min(self.MAX_N_STEPS, round(self.n_steps * 2))
            self.test_case_list[self.test_case_index](self.n_steps)
            print("Display Test case: ", self.test_case_index, "n_steps: ", self.n_steps)

        # Switches
        if chr(keycode) in "rR":
            self.randomColor = not self.randomColor
            print("Random Color: ", self.randomColor)
        if chr(keycode) in "cC":
            self.clear()
            print("clear Buff")
        if chr(keycode) in "sS":
            self.doSmooth = not self.doSmooth
            print("Do Smooth: ", self.doSmooth)
        if chr(keycode) in "aA":
            self.doAA = not self.doAA
            print("Do Anti-Aliasing: ", self.doAA)
        if chr(keycode) in "mM":
            self.doTexture = not self.doTexture
            print("texture mapping: ", self.doTexture)

    def queryTextureBuffPoint(self, texture: Buff, x: int, y: int) -> Point:
        """
        Query a point at texture buff, should only be used in texture buff query

        :param texture: The texture buff you want to query from
        :type texture: Buff
        :param x: The query point x coordinate
        :type x: int
        :param y: The query point y coordinate
        :type y: int
        :rtype: Point
        """
        if self.debug > 1:
            if x != min(max(0, int(x)), texture.width - 1):
                print(f"Warning: Texture Query x: {x} coordinate outbound")
            if y != min(max(0, int(y)), texture.height - 1):
                print(f"Warning: Texture Query y: {y} coordinate outbound")
        return texture.getPointFromPointArray(x, y)

    @staticmethod
    def drawPoint(buff: Buff, point: Point, alpha=1.0):
        """
        Draw a point on buff

        :param buff: The buff to draw point on
        :type buff: Buff
        :param point: A point to draw on buff
        :type point: Point
        :param alpha: Control the opaqueness of the color
        :type alpha: float from 0.0 to 1.0
        :rtype: None
        """
        x, y = point.coords
        color = point.color

        if alpha <= 0.0:
            return
        elif alpha < 1.0:
            orig_c = buff.getPoint(x, y).color
            color = Sketch.interpolate_color(orig_c, color, alpha)

        # because we have already specified buff.buff has data type uint8, type conversion will be done in numpy
        buff.buff[x, y, 0] = color.r * 255
        buff.buff[x, y, 1] = color.g * 255
        buff.buff[x, y, 2] = color.b * 255

    def a(self):
        self.buff.getPoint()

    @staticmethod
    def __check_AAlevel(AAlevel: int):
        if type(AAlevel) != int or AAlevel <= 0:
            raise ValueError("AAlevel must be an integer >= 1.")

    def drawLine(self, buff: Buff, p1: Point, p2: Point, doSmooth=True, doAA=False, doAAlevel=4):
        """
        Draw a line between p1 and p2 on buff

        :param buff: The buff to edit
        :type buff: Buff
        :param p1: One end point of the line
        :type p1: Point
        :param p2: Another end point of the line
        :type p2: Point
        :param doSmooth: Control flag of color smooth interpolation
        :type doSmooth: bool
        :param doAA: Control flag of doing anti-aliasing
        :type doAA: bool
        :param doAAlevel: anti-aliasing super sampling level
        :type doAAlevel: int
        :rtype: None
        """

        if not doAA:
            def drawLineCallback(x_point, y_point, t, eof: bool):
                if not eof:
                    self.drawPoint(buff, Point((x_point, y_point),
                                               self.interpolate_color(p1.color, p2.color, t) if doSmooth else p1.color))

            self.bresenham_iterator(p1.coords[0], p1.coords[1], p2.coords[0], p2.coords[1], drawLineCallback)
        else:
            # Here we do not use the values computed by the Bresenham function
            # because we need to calculate the ratio between lower and upper here,
            # And extrapolating the ratio by p_k here requires more floating computation.
            # So here we use the original function values directly.
            def drawAACallback(x1, y1, a1, x2, y2, a2, t, eof: bool):
                if not eof:
                    cur_color = self.interpolate_color(p1.color, p2.color, t) if doSmooth else p1.color
                    self.drawPoint(buff, Point((x1, y1), cur_color), a1)
                    self.drawPoint(buff, Point((x2, y2), cur_color), a2)
            self.antialias_iterator(p1.coords[0], p1.coords[1], p2.coords[0], p2.coords[1], drawAACallback)

        # end code of drawing
        return

    def drawTriangle(self, buff: Buff, p1: Point, p2: Point, p3: Point,
                     doSmooth=True, doAA=False, doAAlevel=4, doTexture=False):
        """
        draw Triangle to buff. apply smooth color filling if doSmooth set to true, otherwise fill with first point color
        if doAA is true, apply anti-aliasing to triangle based on doAAlevel given.

        :param buff: The buff to edit
        :type buff: Buff
        :param p1: First triangle vertex
        :param p2: Second triangle vertex
        :param p3: Third triangle vertex
        :type p1: Point
        :type p2: Point
        :type p3: Point
        :param doSmooth: Color smooth filling control flag
        :type doSmooth: bool
        :param doAA: Anti-aliasing control flag
        :type doAA: bool
        :param doAAlevel: Anti-aliasing super sampling level
        :type doAAlevel: int
        :param doTexture: Draw triangle with texture control flag
        :type doTexture: bool
        :rtype: None
        """

        # Sort the three points by the y-value from smallest to largest
        pt_sorted_y = [p1, p2, p3]
        pt_sorted_y.sort(key=lambda p: p.coords[1])
        pt_sorted_x = [p1, p2, p3]
        pt_sorted_x.sort(key=lambda p: p.coords[0])
        # Draw the triangle as two parts, top and bottom.
        first_point = last_point = None

        # If the y-value of the 1st point and the 2nd point are not the same
        if pt_sorted_y[0].coords[1] < pt_sorted_y[1].coords[1]:
            first_point = pt_sorted_y[0]
            # If the y-value of the 2nd point and the 3rd point are not the same
            if pt_sorted_y[1].coords[1] < pt_sorted_y[2].coords[1]:
                last_point = pt_sorted_y[2]
                # Select the point as the middle point
                middle_point_1 = pt_sorted_y[1]
                # Another point needs to be interpolated,
                # calculating the x-coordinate and the value of rgb
                new_y = middle_point_1.coords[1]
                new_t = Sketch.ratio(first_point.coords[1], middle_point_1.coords[1], last_point.coords[1])
                new_x = Sketch.interpolate(first_point.coords[0], last_point.coords[0], new_t)
                new_color = self.interpolate_color(first_point.color, last_point.color, new_t)
                middle_point_2 = Point((new_x, new_y), new_color)
            else:
                # If y-value of the second point and the third point are same
                middle_point_1 = pt_sorted_y[1]
                middle_point_2 = pt_sorted_y[2]

            # Middle two points should be sorted from smallest to largest
            if middle_point_1.coords[0] > middle_point_2.coords[0]:
                middle_point_1, middle_point_2 = middle_point_2, middle_point_1
        else:
            middle_point_1 = pt_sorted_y[0]
            middle_point_2 = pt_sorted_y[1]
            # If the second point and the third point has different y-value
            if pt_sorted_y[1].coords[1] < pt_sorted_y[2].coords[1]:
                if middle_point_1.coords[0] > middle_point_2.coords[0]:
                    middle_point_1, middle_point_2 = middle_point_2, middle_point_1
                last_point = pt_sorted_y[2]
            else:
                # Show that the three points are on the same horizontal line and
                # therefore the triangle is degenerate into a horizontal straight line.
                # Sort the three points by x coordinate from smallest to largest
                pt_sorted_y.sort(key=lambda p: p.coords[0])
                middle_point_1 = pt_sorted_y[0]
                middle_point_2 = pt_sorted_y[2]

        if self.debug:
            print("Up and bottom parts:")
            print(f"first_point: {first_point.coords if first_point else None}")
            print(f"middle_points: {middle_point_1.coords}, {middle_point_2.coords}")
            print(f"last_point: {last_point.coords if last_point else None}")
            print()

        # last_y is used to traverse y in Bresenham using
        last_y = None
        last_x_begin = last_x_end = 0
        p1_y2x = {}
        p2_y2x = {}

        #    x
        #   x-xx
        #  x----xx
        # x-------xx
        #
        # Here x is the outer boundary of the triangle.
        # --- is the inside.

        def addEdge(d: dict, y: int, x1: int, x2: int):
            """
            Utility to add edge data.
            The edge here refers to the outer contour of the triangle.
            It is drawn from the bottom to the top and used to set the boundary data on both sides.
            """
            if x1 > x2:
                x1, x2 = x2, x1
            if y not in d:
                # If the y value has not been added yet, set a new one
                d[y] = (x1, x2)
            else:
                # Merge with the old boundary if it already exists
                d[y] = (min(d[y][0], x1), max(d[y][1], x2))
        def find_point_edge(x: int, y: int, eof: bool,
                            dict_to_store: typing.Dict[int, typing.Tuple[int, int]]):
            """
            Callback function used to find the boundary.
            It detects the y-value of the point returned by Bresenham each time and
            updates the range of x if y has not changed, otherwise it creates a new boundary.
            """
            nonlocal last_y, last_x_begin, last_x_end
            if last_y is None:
                last_y = y
                last_x_begin = last_x_end = x
            elif last_y != y:
                addEdge(dict_to_store, last_y, last_x_begin, last_x_end)
                last_y = y
                last_x_begin = last_x_end = x
            else:
                last_x_end = x
            if eof:
                addEdge(dict_to_store, last_y, last_x_begin, last_x_end)

        if first_point is not None:
            self.bresenham_iterator(first_point.coords[0], first_point.coords[1],
                                    middle_point_1.coords[0], middle_point_1.coords[1],
                                    lambda x, y, t, eof:  find_point_edge(x, y, eof, p1_y2x))
            self.bresenham_iterator(first_point.coords[0], first_point.coords[1],
                                    middle_point_2.coords[0], middle_point_2.coords[1],
                                    lambda x, y, t, eof:  find_point_edge(x, y, eof, p2_y2x))
        if last_point is not None:
            self.bresenham_iterator(middle_point_1.coords[0], middle_point_1.coords[1],
                                    last_point.coords[0], last_point.coords[1],
                                    lambda x, y, t, eof:  find_point_edge(x, y, eof, p1_y2x))
            self.bresenham_iterator(middle_point_2.coords[0], middle_point_2.coords[1],
                                    last_point.coords[0], last_point.coords[1],
                                    lambda x, y, t, eof:  find_point_edge(x, y, eof, p2_y2x))

        for y in range(pt_sorted_y[0].coords[1], pt_sorted_y[2].coords[1] + 1):
            x1, x2 = p1_y2x[y]
            x3, x4 = p2_y2x[y]

            color, color1, color2 = None, None, None
            texture_ty = 0
            if not doTexture and not doSmooth:
                color = p1.color
            else:
                if doTexture:
                    # Here the position of the y-value relative to the height of
                    # the whole triangle is needed (highest point - lowest point position)
                    texture_ty = Sketch.ratio(pt_sorted_y[0].coords[1], y, pt_sorted_y[2].coords[1])
                else:
                    # Calculate the color of the point at the beginning and end of the line
                    if y <= middle_point_1.coords[1]:
                        # Here, if y is in the upper half of the triangle,
                        # we need to calculate the position of y relative to the height of the upper half
                        if first_point is not None:
                            t = Sketch.ratio(first_point.coords[1], y, middle_point_1.coords[1])
                            color1 = self.interpolate_color(first_point.color, middle_point_1.color, t)
                            color2 = self.interpolate_color(first_point.color, middle_point_2.color, t)
                        else:
                            color1 = middle_point_1.color
                            color2 = middle_point_2.color
                    else:
                        # Here, if y is in the lower half of the triangle,
                        # we need to calculate the position of y relative to the height of the lower half
                        if last_point is not None:
                            t = Sketch.ratio(middle_point_1.coords[1], y, last_point.coords[1])
                            color1 = self.interpolate_color(middle_point_1.color, last_point.color, t)
                            color2 = self.interpolate_color(middle_point_2.color, last_point.color, t)
                        else:
                            color1 = middle_point_1.color
                            color2 = middle_point_2.color

            # I'm going to let it draw half of the outer edges,
            # in non-anti-aliased mode.
            aa_left = math.floor(Sketch.interpolate(x1, x2, 0.5))
            aa_right = math.ceil(Sketch.interpolate(x3, x4, 0.5))

            for x in range(x1, x4 + 1):
                if doTexture or doSmooth:
                    tx = Sketch.ratio(x1, x, x4)
                    if not doTexture:
                        color = self.interpolate_color(color1, color2, tx)
                    else:
                        map_x = tx * (self.texture.width - 1)
                        map_y = texture_ty * (self.texture.height - 1)
                        color = self.textureAutoMapping(map_x, map_y)
                        
                if aa_left < x < aa_right:
                    self.drawPoint(buff, Point((x, y), color))
                elif not doAA:
                    # boundary part
                    # It must be not doAA to draw,
                    # otherwise the boundary need to call the anti-aliasing algorithm to draw.
                    self.drawPoint(buff, Point((x, y), color))

        if doAA:
            # If anti-aliasing is required, we also need to fill the edges
            def aaCallback(x1, y1, a1, x2, y2, a2, time: float, eof: bool, cl1: ColorType, cl2: ColorType):
                if not doSmooth and not doTexture:
                    # for plain color
                    clr = p1.color
                elif not doTexture:
                    clr = self.interpolate_color(cl1, cl2, time)
                    # for gradient color
                else:
                    # for using maps
                    nonlocal p1_y2x, p2_y2x
                    ty1 = Sketch.ratio(first_point.coords[1], y1, last_point.coords[1])
                    x_most_left = p1_y2x[y1][0]
                    x_most_right = p2_y2x[y1][1]
                    tx1 = Sketch.ratio(x_most_left, x1, x_most_right)
                    map_x = tx1 * (self.texture.width - 1)
                    map_y = ty1 * (self.texture.height - 1)
                    clr = self.textureAutoMapping(map_x, map_y)
                self.drawPoint(buff, Point((x1, y1), clr), a1)
                self.drawPoint(buff, Point((x2, y2), clr), a2)

            Sketch.antialias_iterator(pt_sorted_y[0].coords[0], pt_sorted_y[0].coords[1], pt_sorted_y[1].coords[0], pt_sorted_y[1].coords[1],
                lambda x1, y1, a1, x2, y2, a2, t, eof: aaCallback(x1, y1, a1, x2, y2, a2, t, eof, pt_sorted_y[0].color, pt_sorted_y[1].color))
            Sketch.antialias_iterator(pt_sorted_y[0].coords[0], pt_sorted_y[0].coords[1], pt_sorted_y[2].coords[0], pt_sorted_y[2].coords[1],
                lambda x1, y1, a1, x2, y2, a2, t, eof: aaCallback(x1, y1, a1, x2, y2, a2, t, eof, pt_sorted_y[0].color, pt_sorted_y[2].color))
            Sketch.antialias_iterator(pt_sorted_y[1].coords[0], pt_sorted_y[1].coords[1], pt_sorted_y[2].coords[0], pt_sorted_y[2].coords[1],
                lambda x1, y1, a1, x2, y2, a2, t, eof: aaCallback(x1, y1, a1, x2, y2, a2, t, eof, pt_sorted_y[1].color, pt_sorted_y[2].color))
        return

    def textureAutoMapping(self, map_x, map_y) -> ColorType:
        # do bilinear interpolation here
        if int(map_x) == map_x and int(map_y) == map_y:
            color = self.queryTextureBuffPoint(self.texture, int(map_x), int(map_y)).color
        elif int(map_x) == map_x and int(map_y) != map_y:
            color_a = self.queryTextureBuffPoint(self.texture, int(map_x), math.floor(map_y)).color
            color_b = self.queryTextureBuffPoint(self.texture, int(map_x), math.ceil(map_y)).color
            color = self.interpolate_color(color_a, color_b, map_y % 1)
        elif int(map_x) != map_x and int(map_y) == map_y:
            color_a = self.queryTextureBuffPoint(self.texture, math.floor(map_x), int(map_y)).color
            color_b = self.queryTextureBuffPoint(self.texture, math.ceil(map_x), int(map_y)).color
            color = self.interpolate_color(color_a, color_b, map_x % 1)
        else:
            # Get the left color first
            color_a = self.queryTextureBuffPoint(self.texture, math.floor(map_x), math.floor(map_y)).color
            color_b = self.queryTextureBuffPoint(self.texture, math.floor(map_x), math.ceil(map_y)).color
            color_left = self.interpolate_color(color_a, color_b, map_y % 1)
            # Get the right color again
            color_a = self.queryTextureBuffPoint(self.texture, math.ceil(map_x), math.floor(map_y)).color
            color_b = self.queryTextureBuffPoint(self.texture, math.ceil(map_x), math.ceil(map_y)).color
            color_right = self.interpolate_color(color_a, color_b, map_y % 1)
            # Final: interpolation
            color = self.interpolate_color(color_left, color_right, map_x % 1)
        return color

    @staticmethod
    def bresenham_iterator(x1, y1, x2, y2, callback: typing.Callable[[int, int, float, bool], None]):
        x1 = round(x1)
        x2 = round(x2)
        y1 = round(y1)
        y2 = round(y2)
        x_data = AxisCalcData(x1, x2)
        y_data = AxisCalcData(y1, y2)
        x_step_mode = False
        if abs(y_data.delta) <= abs(x_data.delta):
            x_step_mode = True
        else:
            x_data, y_data = y_data, x_data
        p = 2 * y_data.delta - x_data.delta

        cur_x = cur_y = 0
        while True:
            if x_data.delta > 0:
                t = cur_x / x_data.delta
            else:
                t = 1
            draw_x = (cur_x + x_data.init) * x_data.trans
            draw_y = (cur_y + y_data.init) * y_data.trans
            if x_step_mode:
                callback(draw_x, draw_y, t, False)
            else:
                callback(draw_y, draw_x, t, False)
            cur_x += 1
            if cur_x >= (x_data.delta + 1):
                break
            y_step = 1 if p > 0 else 0
            cur_y += y_step
            p = p + 2 * y_data.delta - 2 * x_data.delta * y_step
        callback(0, 0, 0, True)

    @staticmethod
    def antialias_iterator(x1, y1, x2, y2,
                           callback: typing.Callable[[int, int, float,
                                                      int, int, float,
                                                      float, bool], None]):
        x_data = AxisCalcData(x1, x2)
        y_data = AxisCalcData(y1, y2)
        x_step_mode = False
        if abs(y_data.delta) <= abs(x_data.delta):
            x_step_mode = True
        else:
            x_data, y_data = y_data, x_data

        for cur_x in range(0, x_data.delta + 1):
            if x_data.delta > 0:
                t = cur_x / x_data.delta
            else:
                t = 1
            value_y = cur_x * y_data.delta / x_data.delta
            floor_y = int(value_y)
            alpha_k_1 = value_y - floor_y
            alpha_k = 1 - alpha_k_1

            draw_x = (cur_x + x_data.init) * x_data.trans
            draw_y = (floor_y + y_data.init) * y_data.trans
            draw_y_1 = (floor_y + 1 + y_data.init) * y_data.trans
            if x_step_mode:
                callback(draw_x, draw_y, alpha_k, draw_x, draw_y_1, alpha_k_1, t, False)
            else:
                callback(draw_y, draw_x, alpha_k, draw_y_1, draw_x, alpha_k_1, t, False)
        callback(0, 0, 0, 0, 0, 0, 0, True)

    @staticmethod
    def interpolate(start: float, end: float, t: float):
        return start * (1 - t) + end * t

    @staticmethod
    def interpolate_color(color1: ColorType,
                          color2: ColorType,
                          t: float):
        return ColorType(
            Sketch.interpolate(color1.r, color2.r, t),
            Sketch.interpolate(color1.g, color2.g, t),
            Sketch.interpolate(color1.b, color2.b, t),
        )

    @staticmethod
    def ratio(start: float, value: float, end: float):
        if end == start or value < start:
            return 0
        elif value > end:
            return 1
        else:
            return (value - start) / (end - start)

    # test for lines in all directions
    def testCaseLine01(self, n_steps: int):
        center_x = int(self.buff.width / 2)
        center_y = int(self.buff.height / 2)
        radius = int(min(self.buff.width, self.buff.height) * 0.45)

        v0 = Point([center_x, center_y], ColorType(1, 1, 0))
        for step in range(0, n_steps):
            theta = math.pi * step / n_steps
            v1 = Point([center_x + int(math.sin(theta) * radius), center_y + int(math.cos(theta) * radius)],
                       ColorType(0, 0, (1 - step / n_steps)))
            v2 = Point([center_x - int(math.sin(theta) * radius), center_y - int(math.cos(theta) * radius)],
                       ColorType(0, (1 - step / n_steps), 0))
            self.drawLine(self.buff, v2, v0, doSmooth=True, doAA=self.doAA)
            self.drawLine(self.buff, v0, v1, doSmooth=True, doAA=self.doAA)

    # test for lines: drawing circle and petal 
    def testCaseLine02(self, n_steps: int):
        n_steps = 2 * n_steps
        d_theta = 2 * math.pi / n_steps
        d_petal = 12 * math.pi / n_steps
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        radius = (0.75 * min(cx, cy))
        p = radius * 0.25

        # Outer petals
        for i in range(n_steps + 2):
            self.drawLine(self.buff,
                          Point((math.floor(0.5 + radius * math.sin(d_theta * i) + p * math.sin(d_petal * i)) + cx,
                                 math.floor(0.5 + radius * math.cos(d_theta * i) + p * math.cos(d_petal * i)) + cy),
                                ColorType(1, (128 + math.sin(d_theta * i * 5) * 127 / 255),
                                          (128 + math.cos(d_theta * i * 5) * 127 / 255))),
                          Point((math.floor(
                              0.5 + radius * math.sin(d_theta * (i + 1)) + p * math.sin(d_petal * (i + 1))) + cx,
                                 math.floor(0.5 + radius * math.cos(d_theta * (i + 1)) + p * math.cos(
                                     d_petal * (i + 1))) + cy),
                                ColorType(1, (128 + math.sin(d_theta * 5 * (i + 1)) * 127 / 255),
                                          (128 + math.cos(d_theta * 5 * (i + 1)) * 127 / 255))),
                          doSmooth=True, doAA=self.doAA, doAAlevel=self.doAAlevel)

        # Draw circle
        for i in range(n_steps + 1):
            v0 = Point((math.floor(0.5 * radius * math.sin(d_theta * i)) + cx,
                        math.floor(0.5 * radius * math.cos(d_theta * i)) + cy), ColorType(1, 97. / 255, 0))
            v1 = Point((math.floor(0.5 * radius * math.sin(d_theta * (i + 1))) + cx,
                        math.floor(0.5 * radius * math.cos(d_theta * (i + 1))) + cy), ColorType(1, 97. / 255, 0))
            self.drawLine(self.buff, v0, v1, doSmooth=True, doAA=self.doAA, doAAlevel=self.doAAlevel)

    # test for smooth filling triangle
    def testCaseTri01(self, n_steps: int):
        n_steps = int(n_steps / 2)
        delta = 2 * math.pi / n_steps
        radius = int(min(self.buff.width, self.buff.height) * 0.45)
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        theta = 0

        for _ in range(n_steps):
            theta += delta
            v0 = Point((cx, cy), ColorType(1, 1, 1))
            v1 = Point((int(cx + math.sin(theta) * radius), int(cy + math.cos(theta) * radius)),
                       ColorType((127. + 127. * math.sin(theta)) / 255,
                                 (127. + 127. * math.sin(theta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + 4 * math.pi / 3)) / 255))
            v2 = Point((int(cx + math.sin(theta + delta) * radius), int(cy + math.cos(theta + delta) * radius)),
                       ColorType((127. + 127. * math.sin(theta + delta)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 4 * math.pi / 3)) / 255))
            self.drawTriangle(self.buff, v1, v0, v2, False, self.doAA, self.doAAlevel)

    def testCaseTri02(self, n_steps: int):
        # Test case for no smooth color filling triangle
        n_steps = int(n_steps / 2)
        delta = 2 * math.pi / n_steps
        radius = int(min(self.buff.width, self.buff.height) * 0.45)
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        theta = 0

        for _ in range(n_steps):
            theta += delta
            v0 = Point((cx, cy), ColorType(1, 1, 1))
            v1 = Point((int(cx + math.sin(theta) * radius), int(cy + math.cos(theta) * radius)),
                       ColorType((127. + 127. * math.sin(theta)) / 255,
                                 (127. + 127. * math.sin(theta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + 4 * math.pi / 3)) / 255))
            v2 = Point((int(cx + math.sin(theta + delta) * radius), int(cy + math.cos(theta + delta) * radius)),
                       ColorType((127. + 127. * math.sin(theta + delta)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 4 * math.pi / 3)) / 255))
            self.drawTriangle(self.buff, v0, v1, v2, True, self.doAA, self.doAAlevel)

    def testCaseTriTexture01(self, n_steps: int):
        # Test case for no smooth color filling triangle
        n_steps = int(n_steps / 2)
        delta = 2 * math.pi / n_steps
        radius = int(min(self.buff.width, self.buff.height) * 0.45)
        cx = int(self.buff.width / 2)
        cy = int(self.buff.height / 2)
        theta = 0

        triangleList = []
        for _ in range(n_steps):
            theta += delta
            v0 = Point((cx, cy), ColorType(1, 1, 1))
            v1 = Point((int(cx + math.sin(theta) * radius), int(cy + math.cos(theta) * radius)),
                       ColorType((127. + 127. * math.sin(theta)) / 255,
                                 (127. + 127. * math.sin(theta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + 4 * math.pi / 3)) / 255))
            v2 = Point((int(cx + math.sin(theta + delta) * radius), int(cy + math.cos(theta + delta) * radius)),
                       ColorType((127. + 127. * math.sin(theta + delta)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 2 * math.pi / 3)) / 255,
                                 (127. + 127. * math.sin(theta + delta + 4 * math.pi / 3)) / 255))
            triangleList.append([v0, v1, v2])

        for t in triangleList:
            self.drawTriangle(self.buff, *t, doTexture=True)


if __name__ == "__main__":
    def main():
        print("This is the main entry! ")
        app = wx.App(False)
        # Set FULL_REPAINT_ON_RESIZE will repaint everything when scaling the frame
        # here is the style setting for it: wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE
        # wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER will disable canvas resize.
        frame = wx.Frame(None, size=(500, 500), title="Test",
                         style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        canvas = Sketch(frame)
        canvas.debug = 0

        frame.Show()
        app.MainLoop()


    def codingDebug():
        """
        If you are still working on the assignment, we suggest to use this as the main call.
        There will be more strict type checking in this version, which might help in locating your bugs.
        """
        print("This is the debug entry! ")
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()

        app = wx.App(False)
        # Set FULL_REPAINT_ON_RESIZE will repaint everything when scaling the frame
        # here is the style setting for it: wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE
        # wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER will disable canvas resize.
        frame = wx.Frame(None, size=(500, 500), title="Test", style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE)
        canvas = Sketch(frame)
        canvas.debug = 2
        frame.Show()
        app.MainLoop()

        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('cumtime').reverse_order()
        stats.print_stats()


    main()
    # codingDebug()
