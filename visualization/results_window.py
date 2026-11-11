"""Batch results window: comparison table and charts, plus the batch progress panel for the main window.

Tabs:
  Table     summary per method variant for the chosen movement and placement; click a column
            header to sort, the best value in each column is green
  Charts    runtime, memory, search effort and footprint (evaluation.report.comparison_figure)
  Quality   observed and effective branching factor, optimality score per movement
  Frontier  frontier size as each method expands nodes on the representative map
"""
import os
import sys

import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

from evaluation import report

SIZE = (1180, 760)
MIN_SIZE = (820, 520)
DPI = 100
TOOLBAR = 92
TABS = ("Table", "Charts", "Quality", "Frontier")

BACKGROUND = (245, 245, 245)
TOOLBAR_FILL = (50, 50, 50)
BUTTON_FILL = (75, 75, 75)
BUTTON_ACTIVE = (255, 215, 0)
TEXT_LIGHT = (235, 235, 235)
TEXT_DARK = (30, 30, 30)
TEXT_MUTED = (110, 110, 110)
ROW_ALT = (232, 236, 242)
HEADER_FILL = (210, 216, 226)
BEST = (20, 140, 60)
FLAG = (200, 60, 60)

#(header, summary field, format, relative width, better: "low" / "high" / None)
COLUMNS = [
    ("Method", "variant", None, 3.2, None),
    ("Moves", "path_moves", ".1f", 0.9, "low"),
    ("Cost", "path_cost", ".2f", 0.9, "low"),
    ("C*/C", "optimality_ratio", ".3f", 0.9, "high"),
    ("Expanded", "expanded", ".0f", 1.15, "low"),
    ("Generated", "generated", ".0f", 1.2, "low"),
    ("b avg", "branching_avg", ".2f", 0.8, None),
    ("b max", "branching_max", "d", 0.8, None),
    ("b*", "ebf", ".3f", 0.85, "low"),
    ("Footprint", "peak_footprint", ".0f", 1.25, "low"),
    ("Time ms", "time_ms_mean", ".3f", 1.25, "low"),
    ("+/- std", "time_ms_std", ".3f", 0.95, None),
    ("Best", "time_ms_min", ".3f", 0.95, "low"),
    ("Worst", "time_ms_max", ".3f", 0.95, "low"),
    ("Mem KiB", "mem_kib_mean", ".1f", 1.05, "low"),
    ("Score", "score", ".1f", 0.85, "high"),
]

TABLE_NOTES = [
    "Means over the maps in this movement/placement set. Time and memory: mean, std, best and worst over the "
    "repeated runs of each map, averaged over maps.",
    "C*/C = optimal cost / cost found (1 = optimal).  b* = effective branching factor at the shortest depth "
    "(1 = only path nodes expanded).  Footprint = peak frontier + explored.",
    "Score = 100 x (C*/C) x (fewest expansions on the map / expansions).  * = heuristic not admissible for "
    "this movement.  Full details: log.txt in the results folder.",
]


class Button:
    def __init__(self, label, key):
        self.label = label
        self.key = key
        self.rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, surface, font, active):
        pygame.draw.rect(surface, BUTTON_FILL, self.rect, border_radius=4)
        pygame.draw.rect(surface, BUTTON_ACTIVE if active else (120, 120, 120), self.rect, 2, border_radius=4)
        text = font.render(self.label, True, TEXT_LIGHT)
        surface.blit(text, text.get_rect(center=self.rect.center))


class ResultsWindow:
    def __init__(self, results, out_dir):
        self.results = results
        self.out_dir = out_dir
        protocol = results["protocol"]
        self.window = pygame.Window(f"Batch Results: {protocol['name']}", SIZE, resizable=True)
        self.window.minimum_size = MIN_SIZE
        self.surface = self.window.get_surface()
        self.closed = False
        self.font = pygame.font.Font(None, 22)
        self.small = pygame.font.Font(None, 19)
        self.title_font = pygame.font.Font(None, 26)

        self.tab = TABS[0]
        self.movement = protocol["movements"][0]
        self.placement = report.ALL
        self.sort_field = None
        self.sort_descending = False
        self.scroll = 0
        self._images = {}   #cached chart images by (tab, movement, placement, size)

        placements = sorted({run["placement"] for run in results["runs"]})
        self.tab_buttons = [Button(tab, tab) for tab in TABS]
        self.movement_buttons = [Button(m, m) for m in protocol["movements"]]
        self.placement_buttons = [Button("All", report.ALL)] + (
            [Button(p.capitalize(), p) for p in placements] if len(placements) > 1 else [])
        self.folder_button = Button("Open results folder", "folder")
        self._header_rects = []
        self._layout()

    # ------------------------------------------------------------ layout and events

    def _layout(self):
        width, _ = self.window.size
        x = 12
        for button in self.tab_buttons:
            button.rect = pygame.Rect(x, 10, 100, 30)
            x += 106
        self.folder_button.rect = pygame.Rect(width - 182, 10, 170, 30)
        x = 12
        for button in self.movement_buttons:
            button.rect = pygame.Rect(x, 52, 70, 28)
            x += 76
        x += 18
        for button in self.placement_buttons:
            button.rect = pygame.Rect(x, 52, 82, 28)
            x += 88
        self._filters_right = x

    def handle_event(self, event):
        if event.type == pygame.WINDOWCLOSE:
            self.closed = True
            return
        if event.type == pygame.WINDOWRESIZED:
            self.surface = self.window.get_surface()
            self._layout()
            return
        if event.type == pygame.MOUSEWHEEL and self.tab == "Table":
            self.scroll = max(0, self.scroll - event.y * 3)
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        for button in self.tab_buttons:
            if button.rect.collidepoint(pos):
                self.tab = button.key
        for button in self.movement_buttons:
            if button.rect.collidepoint(pos):
                self.movement = button.key
        for button in self.placement_buttons:
            if button.rect.collidepoint(pos):
                self.placement = button.key
        if self.folder_button.rect.collidepoint(pos):
            self._open_folder()
        if self.tab == "Table":
            for rect, field in self._header_rects:
                if rect.collidepoint(pos):
                    if self.sort_field == field:
                        self.sort_descending = not self.sort_descending
                    else:
                        self.sort_field, self.sort_descending = field, False

    def _open_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.out_dir)
            else:
                import subprocess
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(self.out_dir)])
        except OSError:
            pass

    def destroy(self):
        self.window.destroy()

    # ------------------------------------------------------------ drawing

    def draw(self):
        if self.closed:
            return
        if self.surface.get_size() != tuple(self.window.size):
            self.surface = self.window.get_surface()
            self._layout()
        surface = self.surface
        surface.fill(BACKGROUND)
        self._draw_toolbar(surface)
        content = pygame.Rect(0, TOOLBAR, surface.get_width(), surface.get_height() - TOOLBAR)
        if self.tab == "Table":
            self._draw_table(surface, content)
        else:
            image = self._chart_image(content.size)
            if image is not None:
                surface.blit(image, content.topleft)
        self.window.flip()

    def _draw_toolbar(self, surface):
        pygame.draw.rect(surface, TOOLBAR_FILL, (0, 0, surface.get_width(), TOOLBAR))
        for button in self.tab_buttons:
            button.draw(surface, self.font, button.key == self.tab)
        self.folder_button.draw(surface, self.small, False)
        uses_movement = self.tab in ("Table", "Charts")
        uses_placement = self.tab in ("Table", "Charts", "Quality")
        for button in self.movement_buttons:
            button.draw(surface, self.small, uses_movement and button.key == self.movement)
        for button in self.placement_buttons:
            button.draw(surface, self.small, uses_placement and button.key == self.placement)
        r = self.results
        state = "CANCELLED, partial" if r["cancelled"] else "complete"
        info = (f"{len(r['maps'])} maps, {r['protocol']['repeats']} repeats, "
                f"{r['measurements_done']}/{r['measurements_total']} measurements, {r['elapsed_s']} s, {state}")
        text = self.small.render(info, True, TEXT_LIGHT)
        surface.blit(text, (self._filters_right + 10, 58))

    def _chart_image(self, size):
        key = (self.tab, self.movement, self.placement, size)
        if key not in self._images:
            figsize = (size[0] / DPI, size[1] / DPI)
            if self.tab == "Charts":
                figure = report.comparison_figure(self.results, self.movement, self.placement, figsize, DPI)
            elif self.tab == "Quality":
                figure = report.quality_figure(self.results, self.placement, figsize, DPI)
            else:
                figure = report.frontier_figure(self.results, figsize, DPI)
            canvas = FigureCanvasAgg(figure)
            canvas.draw()
            self._images[key] = pygame.image.frombuffer(bytes(canvas.buffer_rgba()),
                                                        canvas.get_width_height(), "RGBA").copy()
        return self._images[key]

    def _rows(self):
        rows = report.summary_rows(self.results, self.movement, self.placement)
        if self.sort_field:
            present = [r for r in rows if r.get(self.sort_field) is not None]
            missing = [r for r in rows if r.get(self.sort_field) is None]
            present.sort(key=lambda r: r[self.sort_field], reverse=self.sort_descending)
            rows = present + missing
        return rows

    def _draw_table(self, surface, area):
        rows = self._rows()
        title = f"{self.results['protocol']['name']}: {self.movement}, placement {self.placement}"
        if rows:
            title += f"  ({rows[0]['maps']} maps)"
        surface.blit(self.title_font.render(title, True, TEXT_DARK), (area.x + 12, area.y + 10))

        left = area.x + 10
        width = area.width - 20
        total = sum(c[3] for c in COLUMNS)
        widths = [int(width * c[3] / total) for c in COLUMNS]
        row_height = 26
        top = area.y + 40

        best = {}
        for header, field, spec, _, better in COLUMNS:
            values = [r[field] for r in rows if r.get(field) is not None]
            if better and values:
                best[field] = min(values) if better == "low" else max(values)

        self._header_rects = []
        x = left
        pygame.draw.rect(surface, HEADER_FILL, (left, top, width, row_height))
        for (header, field, spec, _, better), column_width in zip(COLUMNS, widths):
            label = header + ((" v" if self.sort_descending else " ^") if field == self.sort_field else "")
            text = self.small.render(label, True, TEXT_DARK)
            rect = pygame.Rect(x, top, column_width, row_height)
            if spec is None:
                surface.blit(text, text.get_rect(midleft=(x + 6, rect.centery)))
            else:
                surface.blit(text, text.get_rect(midright=(rect.right - 6, rect.centery)))
            self._header_rects.append((rect, field))
            x += column_width

        visible = max(1, (area.bottom - top - row_height - 70) // row_height)
        self.scroll = min(self.scroll, max(0, len(rows) - visible))
        y = top + row_height
        for index, row in enumerate(rows[self.scroll:self.scroll + visible]):
            if index % 2:
                pygame.draw.rect(surface, ROW_ALT, (left, y, width, row_height))
            x = left
            for (header, field, spec, _, better), column_width in zip(COLUMNS, widths):
                value = row.get(field)
                if spec is None:
                    label = value + (" *" if row["admissible"] is False else "")
                    color = FLAG if row["admissible"] is False else TEXT_DARK
                    text = self.small.render(label, True, color)
                    surface.blit(text, text.get_rect(midleft=(x + 6, y + row_height // 2)))
                else:
                    is_best = field in best and value is not None and abs(value - best[field]) < 1e-9
                    text = (self.small if not is_best else self.font).render(
                        report.fmt(value, spec), True, BEST if is_best else TEXT_DARK)
                    surface.blit(text, text.get_rect(midright=(x + column_width - 6, y + row_height // 2)))
                x += column_width
            y += row_height
        pygame.draw.rect(surface, (180, 180, 180), (left, top, width, y - top), 1)
        if len(rows) > visible:
            hint = self.small.render(f"rows {self.scroll + 1}-{self.scroll + visible} of {len(rows)}, scroll for more",
                                     True, TEXT_MUTED)
            surface.blit(hint, (left, y + 4))
            y += 20

        y += 12
        for note in TABLE_NOTES:
            text = self.small.render(note, True, TEXT_MUTED)
            surface.blit(text, (left, y))
            y += 18
        folder = self.small.render(f"Saved to: {self.out_dir}", True, TEXT_MUTED)
        surface.blit(folder, (left, y + 4))


def draw_progress(surface, area, job):
    """Batch progress panel in the main window, over the grid area."""
    font = pygame.font.Font(None, 26)
    small = pygame.font.Font(None, 20)
    panel = pygame.Rect(0, 0, min(area.width - 40, 560), 120)
    panel.center = area.center
    pygame.draw.rect(surface, (45, 45, 45), panel, border_radius=8)
    pygame.draw.rect(surface, BUTTON_ACTIVE, panel, 2, border_radius=8)
    title = "Cancelling, finishing the current measurement..." if job.cancelling else f"Batch running: {job.name}"
    surface.blit(font.render(title, True, TEXT_LIGHT), (panel.x + 16, panel.y + 14))
    bar = pygame.Rect(panel.x + 16, panel.y + 48, panel.width - 32, 18)
    pygame.draw.rect(surface, (80, 80, 80), bar, border_radius=4)
    filled = bar.copy()
    filled.width = int(bar.width * job.fraction)
    if filled.width:
        pygame.draw.rect(surface, (90, 170, 255), filled, border_radius=4)
    count = f"{job.done} / {job.total} measurements ({100 * job.fraction:.0f}%)" if job.total else "preparing maps..."
    surface.blit(small.render(count, True, TEXT_LIGHT), (panel.x + 16, panel.y + 74))
    detail = job.text
    while detail and small.size(detail)[0] > panel.width - 32:
        detail = detail[:-4] + "..."
    surface.blit(small.render(detail, True, (180, 180, 180)), (panel.x + 16, panel.y + 94))
