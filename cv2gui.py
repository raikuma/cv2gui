import sys
from collections import defaultdict
import cv2
import numpy as np

class Window:
    def __init__(self, name, width=640, height=480, background_color=(0, 0, 0)):
        self.name = name
        self.width = width
        self.height = height
        self.background_color = background_color
        self.objects = []
        self.canvas = np.zeros((self.height, self.width, 3), np.uint8)
        self.fps = 60

        self.eventHandlers = defaultdict(list)
        self.addEventHandler('onKeyDown', self.defaultKeyDownHandler)

        cv2.namedWindow(self.name)
        cv2.resizeWindow(self.name, self.width, self.height)
        cv2.setMouseCallback(self.name, self.mouseCallback)

    def show(self):
        while self:
            self.update()
            key = cv2.waitKey(1 if self.fps < 0 else int(1000 / self.fps))
            if key != -1:
                for callback in self.eventHandlers['onKeyDown']:
                    callback(key)

    def update(self):
        for callback in self.eventHandlers['onUpdate']:
            callback(self.delta)
        self.draw()
        cv2.imshow(self.name, cv2.cvtColor(self.canvas, cv2.COLOR_RGB2BGR))

    def draw(self):
        self.canvas[:] = self.background_color
        for obj in self.objects:
            # print(sys.getrefcount(obj))
            obj.draw(self.canvas)

    def add(self, obj):
        self.objects.append(obj)

    def mouseCallback(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            for callback in self.eventHandlers['onMouseMove']:
                callback(x, y)

    def addEventHandler(self, event, callback):
        self.eventHandlers[event].append(callback)

    def defaultKeyDownHandler(self, key):
        if key == 27: # ESC
            self.close()

    def close(self):
        try:
            cv2.destroyWindow(self.name)
        except:
            pass

    @property
    def delta(self):
        return 1 / self.fps

    def __bool__(self):
        return cv2.getWindowProperty(self.name, cv2.WND_PROP_VISIBLE) > 0
    
    def __nonzero__(self):
        return self.__bool__()

    def __del__(self):
        self.close()

class Object:
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y
        self.childs = []

    def draw(self, canvas):
        for obj in self.childs:
            obj.draw(canvas)

    def add(self, obj):
        self.childs.append(obj)

    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        dx = value - self._x
        self._x += dx
        for obj in self.childs:
            obj.x += dx

    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        dy = value - self._y
        self._y += dy
        for obj in self.childs:
            obj.y += dy

    @property
    def pos(self):
        return (self.x, self.y)
    
    @pos.setter
    def pos(self, value):
        self.x, self.y = value
    

class Sprite(Object):
    def __init__(self, array, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if type(array) is str:
            array = cv2.imread(array)
        self.array = np.array(array, dtype=np.uint8)

    def draw(self, canvas):
        sx = max(-self.x, 0)
        sy = max(-self.y, 0)
        ex = self.array.shape[1] - max(self.x + self.array.shape[1] - canvas.shape[1], 0)
        ey = self.array.shape[0] - max(self.y + self.array.shape[0] - canvas.shape[0], 0)
        if sx < ex and sy < ey:
            canvas[self.y+sy:self.y+ey, self.x+sx:self.x+ex] = self.array[sy:ey, sx:ex]
        super().draw(canvas)

    @property
    def pixels(self):
        return self.array