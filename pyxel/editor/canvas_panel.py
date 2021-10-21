import pyxel

from .settings import (
    PANEL_SELECT_BORDER_COLOR,
    PANEL_SELECT_FRAME_COLOR,
    TOOL_BUCKET,
    TOOL_CIRC,
    TOOL_CIRCB,
    TOOL_PENCIL,
    TOOL_RECT,
    TOOL_RECTB,
    TOOL_SELECT,
)
from .widgets import ScrollBar, Widget
from .widgets.settings import WIDGET_HOLD_TIME, WIDGET_PANEL_COLOR, WIDGET_REPEAT_TIME


class CanvasPanel(Widget):
    """
    Variables:
        color_var
        tool_var
        image_no_var
        tilemap_no_var
        canvas_var
        focus_x_var
        focus_y_var
        help_message_var
    """

    def __init__(self, parent):
        super().__init__(parent, 11, 16, 130, 130)

        if hasattr(parent, "tilemap_no_var"):
            self._is_tilemap_mode = True
        else:
            self._is_tilemap_mode = False

        self._history_data = None
        self._press_x = 0
        self._press_y = 0
        self._last_x = 0
        self._last_y = 0
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._select_x1 = 0
        self._select_y1 = 0
        self._select_x2 = 0
        self._select_y2 = 0
        self._copy_buffer = None
        self._is_dragged = False
        self._is_assist_mode = False
        self._temp_canvas = (
            pyxel.Tilemap(16, 16, 0) if self._is_tilemap_mode else pyxel.Image(16, 16)
        )

        self.add_history = parent.add_history

        self.copy_var("color_var", parent)
        self.copy_var("tool_var", parent)
        self.copy_var("image_no_var", parent)
        self.copy_var("canvas_var", parent)
        self.copy_var("help_message_var", parent)

        if self._is_tilemap_mode:
            self.copy_var("tilemap_no_var", parent)

        # horizontal scroll bar
        self._h_scroll_bar = ScrollBar(
            self,
            0,
            129,
            length=130,
            scroll_range=32,
            slider_range=2,
            value=0,
            is_horizontal=True,
        )
        self._h_scroll_bar.add_event_listener("change", self.__on_h_scroll_bar_change)

        # vertical scroll bar
        self._v_scroll_bar = ScrollBar(
            self,
            129,
            0,
            length=130,
            scroll_range=32,
            slider_range=2,
            value=0,
            is_vertical=True,
        )
        self._v_scroll_bar.add_event_listener("change", self.__on_v_scroll_bar_change)

        # focus_x_var
        self.new_var("focus_x_var", None)
        self.add_var_event_listener("focus_x_var", "get", self.__on_focus_x_get)
        self.add_var_event_listener("focus_x_var", "set", self.__on_focus_x_set)

        # focus_y_var
        self.new_var("focus_y_var", None)
        self.add_var_event_listener("focus_y_var", "get", self.__on_focus_y_get)
        self.add_var_event_listener("focus_y_var", "set", self.__on_focus_y_set)

        # event listeners
        self.add_event_listener("mouse_down", self.__on_mouse_down)
        self.add_event_listener("mouse_up", self.__on_mouse_up)
        self.add_event_listener("mouse_click", self.__on_mouse_click)
        self.add_event_listener("mouse_drag", self.__on_mouse_drag)
        self.add_event_listener("mouse_hover", self.__on_mouse_hover)
        self.add_event_listener("update", self.__on_update)
        self.add_event_listener("draw", self.__on_draw)

    def _add_pre_history(self, canvas):
        self._history_data = data = {}

        if self._is_tilemap_mode:
            data["tilemap"] = self.tilemap_no_var
        else:
            data["image"] = self.image_no_var

        data["pos"] = (self.focus_x_var, self.focus_y_var)
        data["before"] = canvas.copy()

    def _add_post_history(self, canvas):
        data = self._history_data
        data["after"] = canvas.copy()

        if data["before"] != data["after"]:
            self.add_history(data)

    def _screen_to_view(self, x, y):
        x = min(max((x - self.x - 1) // 8, 0), 15)
        y = min(max((y - self.y - 1) // 8, 0), 15)
        return x, y

    def _reset_temp_canvas(self):
        self._temp_canvas.blt(
            0,
            0,
            self.canvas_var,
            self.focus_x_var,
            self.focus_y_var,
            16,
            16,
        )

    def __on_focus_x_get(self, value):
        return self._h_scroll_bar.value_var * 8

    def __on_focus_x_set(self, value):
        self._h_scroll_bar.value_var = int(round(value / 8))

        return None

    def __on_focus_y_get(self, value):
        return self._v_scroll_bar.value_var * 8

    def __on_focus_y_set(self, value):
        self._v_scroll_bar.value_var = int(round(value / 8))

        return None

    def __on_h_scroll_bar_change(self, value):
        self.focus_x_var = value * 8

    def __on_v_scroll_bar_change(self, value):
        self.focus_y_var = value * 8

    def __on_mouse_down(self, key, x, y):
        if key != pyxel.MOUSE_BUTTON_LEFT:
            return

        x, y = self._screen_to_view(x, y)

        self._press_x = x
        self._press_y = y

        self._is_dragged = True
        self._is_assist_mode = False

        if self.tool_var == TOOL_SELECT:
            self._select_x1 = self._select_x2 = x
            self._select_y1 = self._select_y2 = y
        elif self.tool_var >= TOOL_PENCIL and self.tool_var <= TOOL_CIRC:
            self._reset_temp_canvas()
            self._temp_canvas.pset(x, y, self.color_var)
        elif self.tool_var == TOOL_BUCKET:
            self._reset_temp_canvas()

            self._add_pre_history(
                self.canvas_var.get_slice(self.focus_x_var, self.focus_y_var, 16, 16)
            )

            self.canvas.fill(x, y, self.color_var)

            self.canvas.blt(
                self.focus_x_var,
                self.focus_y_var,
                self._temp_canvas,
                0,
                0,
                16,
                16,
            )

            self._add_post_history(
                self.canvas_var.get_slice(self.focus_x_var, self.focus_y_var, 16, 16)
            )

        self._last_x = x
        self._last_y = y

    def __on_mouse_up(self, key, x, y):
        if key != pyxel.MOUSE_BUTTON_LEFT:
            return

        self._is_dragged = False

        if TOOL_PENCIL <= self.tool_var <= TOOL_CIRC:
            self._add_pre_history(
                self.canvas_var.get_slice(self.focus_x_var, self.focus_y_var, 16, 16)
            )

            self.canvas_var.blt(
                self.focus_x_var,
                self.focus_y_var,
                self._temp_canvas,
                0,
                0,
                16,
                16,
            )

            self._add_post_history(
                self.canvas_var.get_slice(self.focus_x_var, self.focus_y_var, 16, 16)
            )

    def __on_mouse_click(self, key, x, y):
        if key == pyxel.MOUSE_BUTTON_RIGHT:
            x = self.focus_x_var + (x - self.x) // 8
            y = self.focus_y_var + (y - self.y) // 8

            if self._is_tilemap_mode:
                self.color_var = pyxel.tilemap(self.tilemap_var).data[y][x]
            else:
                self.color_var = pyxel.image(self.image_var).data[y][x]

    def __on_mouse_drag(self, key, x, y, dx, dy):
        if key == pyxel.MOUSE_BUTTON_LEFT:
            x1 = self._press_x
            y1 = self._press_y
            x2 = (x - self.x - 1) // 8
            y2 = (y - self.y - 1) // 8

            if self.tool_var == TOOL_SELECT:
                x2 = min(max(x2, 0), 15)
                y2 = min(max(y2, 0), 15)
                self._select_x1, self._select_x2 = (x1, x2) if x1 < x2 else (x2, x1)
                self._select_y1, self._select_y2 = (y1, y2) if y1 < y2 else (y2, y1)
            elif self.tool_var == TOOL_PENCIL:
                if self._is_assist_mode:
                    self._overlay_canvas.clear()
                    self._overlay_canvas.line(x1, y1, x2, y2, self.color_var)
                else:
                    self._temp_canvas.line(
                        self._last_x, self._last_y, x2, y2, self.color_var
                    )
            elif self.tool_var == TOOL_RECTB:
                self._reset_temp_canvas()
                self._temp_canvas.rectb2(
                    x1,
                    y1,
                    x2,
                    y2,
                    self.color_var,
                )
            elif self.tool_var == TOOL_RECT:
                self._reset_temp_canvas()
                self._temp_canvas.rect2(
                    x1,
                    y1,
                    x2,
                    y2,
                    self.color_var,
                )
            elif self.tool_var == TOOL_CIRCB:
                self._reset_temp_canvas()
                self._temp_canvas.ellipb(x1, y1, x2, y2, self.color_var)
            elif self.tool_var == TOOL_CIRC:
                self._reset_temp_canvas()
                self._temp_canvas.ellip(x1, y1, x2, y2, self.color_var)

            self._last_x = x2
            self._last_y = y2

        elif key == pyxel.MOUSE_BUTTON_RIGHT:
            self._drag_offset_x -= dx
            self._drag_offset_y -= dy

            if abs(self._drag_offset_x) >= 16:
                offset = self._drag_offset_x // 16
                self.focus_x_var += offset * 8
                self._drag_offset_x -= offset * 16

            if abs(self._drag_offset_y) >= 16:
                offset = self._drag_offset_y // 16
                self.focus_y_var += offset * 8
                self._drag_offset_y -= offset * 16

            self.focus_x_var = min(max(self.focus_x_var, 0), 240)
            self.focus_y_var = min(max(self.focus_y_var, 0), 240)

    def __on_mouse_hover(self, x, y):
        if self.tool_var == TOOL_SELECT:
            s = "COPY:CTRL+C PASTE:CTRL+V"
        elif self._is_dragged:
            s = "ASSIST:SHIFT"
        else:
            s = "PICK:R-CLICK VIEW:R-DRAG"

        x, y = self._screen_to_view(x, y)
        x += self.focus_x_var
        y += self.focus_y_var
        self.help_message_var = s + " ({},{})".format(x, y)

    def __on_update(self):
        if self._is_dragged and not self._is_assist_mode and pyxel.btn(pyxel.KEY_SHIFT):
            self._is_assist_mode = True

        if (
            self.tool_var == TOOL_SELECT
            and self._select_x1 >= 0
            and (pyxel.btn(pyxel.KEY_CTRL) or pyxel.btn(pyxel.KEY_GUI))
        ):
            if pyxel.btnp(pyxel.KEY_C):
                self._copy_buffer = self.canvas_var.get_slice(
                    self.focus_x_var + self._select_x1,
                    self.focus_y_var + self._select_y1,
                    self._select_x2 - self._select_x1 + 1,
                    self._select_y2 - self._select_y1 + 1,
                )
            elif self._copy_buffer is not None and pyxel.btnp(pyxel.KEY_V):
                width, height = len(self._copy_buffer[0]), len(self._copy_buffer)
                width -= max(self._select_x1 + width - 16, 0)
                height -= max(self._select_y1 + height - 16, 0)

                self._add_pre_history(
                    self.canvas_var.get_slice(
                        self.focus_x_var, self.focus_y_var, 16, 16
                    )
                )

                self.canvas_var.set_slice(
                    self.focus_x_var + self._select_x1,
                    self.focus_y_var + self._select_y1,
                    width,
                    height,
                    self._copy_buffer,
                )

                self._add_post_history(
                    self.canvas_var.get_slice(
                        self.focus_x_var, self.focus_y_var, 16, 16
                    )
                )

        if (
            pyxel.btn(pyxel.KEY_SHIFT)
            or pyxel.btn(pyxel.KEY_CTRL)
            or pyxel.btn(pyxel.KEY_ALT)
            or pyxel.btn(pyxel.KEY_GUI)
        ):
            return

        if pyxel.btnp(pyxel.KEY_LEFT, WIDGET_HOLD_TIME, WIDGET_REPEAT_TIME):
            self.focus_x_var -= 8

        if pyxel.btnp(pyxel.KEY_RIGHT, WIDGET_HOLD_TIME, WIDGET_REPEAT_TIME):
            self.focus_x_var += 8

        if pyxel.btnp(pyxel.KEY_UP, WIDGET_HOLD_TIME, WIDGET_REPEAT_TIME):
            self.focus_y_var -= 8

        if pyxel.btnp(pyxel.KEY_DOWN, WIDGET_HOLD_TIME, WIDGET_REPEAT_TIME):
            self.focus_y_var += 8

        # self.focus_x_var = min(max(self.focus_x_var, 0), 240)
        # self.focus_y_var = min(max(self.focus_y_var, 0), 240)

        # self._h_scroll_bar.value = self.focus_x_var // 8
        # self._v_scroll_bar.value = self.focus_y_var // 8

    def __on_draw(self):
        self.draw_panel(self.x, self.y, self.width, self.height)

        if self._is_tilemap_mode:
            pass
            """
            pyxel.bltm(
                self.x + 1,
                self.y + 1,
                self.parent.tilemap,
                self.parent.focus_x,
                self.parent.focus_y,
                16,
                16,
            )

            for i in range(16):
                y = self.y + i * 8 + 1
                for j in range(16):
                    x = self.x + j * 8 + 1

                    val = self._overlay_canvas.data[i][j]
                    if val != OverlayCanvas.COLOR_NONE:
                        sx = (val % 32) * 8
                        sy = (val // 32) * 8
                        pyxel.blt(x, y, self.parent.image, sx, sy, 8, 8)
            """
        else:
            canvas, offset_x, offset_y = (
                (self._temp_canvas, 0, 0)
                if self._is_dragged
                else (self.canvas_var, self.focus_x_var, self.focus_y_var)
            )

            for i in range(16):
                y = self.y + i * 8 + 1
                for j in range(16):
                    x = self.x + j * 8 + 1
                    pyxel.rect(x, y, 8, 8, canvas.pget(offset_x + j, offset_y + i))

        pyxel.line(
            self.x + 1, self.y + 64, self.x + 128, self.y + 64, WIDGET_PANEL_COLOR
        )
        pyxel.line(
            self.x + 64, self.y + 1, self.x + 64, self.y + 128, WIDGET_PANEL_COLOR
        )

        if self.tool_var == TOOL_SELECT and self._select_x1 >= 0:
            pyxel.clip(self.x + 1, self.y + 1, self.x + 128, self.y + 128)

            x = self._select_x1 * 8 + 12
            y = self._select_y1 * 8 + 17
            w = self._select_x2 * 8 - x + 20
            h = self._select_y2 * 8 - y + 25

            pyxel.rectb(x, y, w, h, PANEL_SELECT_FRAME_COLOR)
            pyxel.rectb(x + 1, y + 1, w - 2, h - 2, PANEL_SELECT_BORDER_COLOR)
            pyxel.rectb(x - 1, y - 1, w + 2, h + 2, PANEL_SELECT_BORDER_COLOR)

            pyxel.clip()

    @staticmethod
    def _adjust_region(x1, y1, x2, y2, is_assist_mode):
        if is_assist_mode:
            dx = x2 - x1
            dy = y2 - y1

            if abs(dx) > abs(dy):
                y2 = y1 + abs(dx) * (1 if dy > 0 else -1)
            else:
                x2 = x1 + abs(dy) * (1 if dx > 0 else -1)

        x1, x2 = (x1, x2) if x1 < x2 else (x2, x1)
        y1, y2 = (y1, y2) if y1 < y2 else (y2, y1)

        return x1, y1, x2, y2
