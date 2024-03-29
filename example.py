import cv2gui as cg
import numpy as np

# Create a window
win = cg.Window("Example")

# Create Objects
container = cg.Object(0, 0)
obj = cg.Sprite(np.full((100, 100, 3), (255, 0, 0), np.uint8), 100, 100)
container.add(obj)
img = cg.Sprite("blue.png")
container.add(img)

# Add Objects to the window
win.add(container)

# Mouse event
def onMouseMove(x, y):
    container.pos = (x, y)
    print(x, y)
win.add_event_listener('onMouseMove', onMouseMove)

def onKeyDown(key):
    if key == ord('d'):
        obj.rpos = (obj.rpos[0] + 1, obj.rpos[1])
    if key == ord('a'):
        obj.rpos = (obj.rpos[0] - 1, obj.rpos[1])
    print(key)
win.add_event_listener('onKeyDown', onKeyDown)

def onUpdate(delta):
    arr = obj.pixels
    arr[:, :, 0] += 1
win.add_event_listener('onUpdate', onUpdate)

win.show()
