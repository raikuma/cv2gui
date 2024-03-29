import sys
from collections import defaultdict
import cv2
import numpy as np


class Window:
    # Events
    ON_KEY_DOWN = "onKeyDown"
    ON_MOUSE_DOWN = "onMouseDown"
    ON_MOUSE_MOVE = "onMouseMove"
    ON_MOUSE_UP = "onMouseUp"
    ON_UPDATE = "onUpdate"

    def __init__(self, name, width=640, height=480, background_color=(0, 0, 0), fps=60):
        self.name = name
        self.width = width
        self.height = height
        self.background_color = background_color
        self.objects = []
        self.canvas = np.zeros((self.height, self.width, 3), np.uint8)
        self.fps = fps
        self.event_listeners = defaultdict(list)

        cv2.namedWindow(self.name)
        cv2.resizeWindow(self.name, self.width, self.height)
        cv2.setMouseCallback(self.name, self.mouse_callback)

    def show(self):
        while self:
            self.update()
            key = cv2.waitKey(1 if self.fps < 0 else int(1000 / self.fps))
            if key != -1:
                for callback in self.event_listeners[self.ON_KEY_DOWN]:
                    callback(key)
                if key == 27:  # ESC
                    self.close()
                    break

    def update(self):
        for callback in self.event_listeners[self.ON_UPDATE]:
            callback(self.delta)
        self.draw()
        cv2.imshow(self.name, self.canvas)

    def draw(self):
        self.canvas[:] = self.background_color
        for obj in self.objects:
            # print(sys.getrefcount(obj))
            if obj.visible:
                obj.draw(self.canvas)

    def add(self, obj):
        self.objects.append(obj)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for callback in self.event_listeners[self.ON_MOUSE_DOWN]:
                callback(x, y)
        if event == cv2.EVENT_MOUSEMOVE:
            for callback in self.event_listeners[self.ON_MOUSE_MOVE]:
                callback(x, y)
        if event == cv2.EVENT_LBUTTONUP:
            for callback in self.event_listeners[self.ON_MOUSE_UP]:
                callback(x, y)

    def add_event_listener(self, event, callback):
        self.event_listeners[event].append(callback)

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
        self.parent = None
        self.childs = []
        self.visible = True

    def draw(self, canvas):
        for obj in self.childs:
            if obj.visible:
                obj.draw(canvas)

    def add(self, obj):
        self.childs.append(obj)
        obj.parent = self

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

    @property
    def rpos(self):
        if self.parent is None:
            return self.pos
        else:
            return (self.x - self.parent.x, self.y - self.parent.y)

    @rpos.setter
    def rpos(self, value):
        self.x = value[0] + self.parent.x
        self.y = value[1] + self.parent.y


class Sprite(Object):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if type(data) is str:
            data = cv2.imread(data)
        self.pixels = np.array(data, dtype=np.uint8)

    def draw(self, canvas):
        sx = max(-self.x, 0)
        sy = max(-self.y, 0)
        ex = self.pixels.shape[1] - max(
            self.x + self.pixels.shape[1] - canvas.shape[1], 0
        )
        ey = self.pixels.shape[0] - max(
            self.y + self.pixels.shape[0] - canvas.shape[0], 0
        )
        target_area = np.s_[self.y + sy : self.y + ey, self.x + sx : self.x + ex]
        if sx < ex and sy < ey:
            if self.pixels.shape[-1] == 4:  # alpha blending
                alpha = self.pixels[sy:ey, sx:ex, 3:4] / 255
                canvas[target_area] = (1 - alpha) * canvas[
                    target_area
                ] + alpha * self.pixels[sy:ey, sx:ex, :3]
            else:
                canvas[target_area] = self.pixels[sy:ey, sx:ex]
        super().draw(canvas)

    def scale(self, factor):
        self.pixels = cv2.resize(self.pixels, (0, 0), fx=factor, fy=factor)

    def contain(self, x, y):
        return 0 <= x - self.x < self.width and 0 <= y - self.y < self.height

    @property
    def width(self):
        return self.pixels.shape[1]

    @property
    def height(self):
        return self.pixels.shape[0]


class Text(Object):
    def __init__(
        self,
        text,
        *args,
        font_size=100,
        color=(255, 255, 255),
        align="center",
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.text = text
        self.font = cv2.FONT_HERSHEY_COMPLEX
        self.font_scale = font_size / 50
        self.font_color = color
        self.font_thickness = 1
        self.font_line_type = cv2.LINE_AA
        self.align = align

    def draw(self, canvas):
        if self.align == "center":
            dx = -self.width // 2
        elif self.align == "right":
            dx = -self.width
        else:
            dx = 0
        cv2.putText(
            canvas,
            self.text,
            (self.x + dx, self.y),
            self.font,
            self.font_scale,
            self.font_color,
            self.font_thickness,
            self.font_line_type,
        )
        super().draw(canvas)

    @property
    def width(self):
        return cv2.getTextSize(
            self.text, self.font, self.font_scale, self.font_thickness
        )[0][0]

    @property
    def height(self):
        return cv2.getTextSize(
            self.text, self.font, self.font_scale, self.font_thickness
        )[0][1]
