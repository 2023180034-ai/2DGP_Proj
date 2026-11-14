import math


FOLLOW_SPEED = 2.5


class Camera:
    def __init__(self, world_width, world_height, viewport_width, viewport_height):
        self.world_width = world_width
        self.world_height = world_height
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.x = 0
        self.y = 0

    def reset(self, target_x, target_y):
        self.x = self._clamp_x(target_x - self.viewport_width / 2)
        self.y = self._clamp_y(target_y - self.viewport_height / 2)

    def follow(self, target_x, target_y, delta_time):
        blend = 1 - math.exp(-FOLLOW_SPEED * delta_time)
        target_camera_x = self._clamp_x(target_x - self.viewport_width / 2)
        target_camera_y = self._clamp_y(target_y - self.viewport_height / 2)
        self.x += (target_camera_x - self.x) * blend
        self.y += (target_camera_y - self.y) * blend

    def _clamp_x(self, x):
        return min(max(x, 0), max(0, self.world_width - self.viewport_width))

    def _clamp_y(self, y):
        return min(max(y, 0), max(0, self.world_height - self.viewport_height))
