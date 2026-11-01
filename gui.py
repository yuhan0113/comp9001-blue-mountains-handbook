"""Optional Tkinter interface. Run with python3 gui.py."""
import csv

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, font as tkfont
except ImportError:
    tk = ttk = messagebox = None

from data_loader import load_catalogue, positive_number
from recommendations import recommend, time_alternatives, validate_preferences, trade_offs, preparation
from main import format_results, save_report

BG_DARK = '#0B1115'
BG_PANEL = '#172126'
BG_SIDEBAR = '#11191E'
TEXT_PRIMARY = '#F2F3EF'
TEXT_SECONDARY = '#95A3A8'
ACCENT_BLUE = '#557D8D'
ACCENT_GREEN = '#8A9F89'
BORDER = '#28343A'

MOOD_OPTIONS = {'Taking it easy': 'relaxed', 'Keen to explore': 'exploring',
                'Ready for a workout': 'active', 'No preference': 'any'}
SCENERY_OPTIONS = {'Views': 'views', 'Waterfalls': 'waterfalls',
                   'Forest': 'forest', 'No preference': 'any'}
ROUTE_OPTIONS = {'Loop': 'loop', 'Return': 'return', 'One-way': 'one-way',
                 'No preference': 'any'}


def preferences_from_form(mood, minutes, scenery, difficulty, extra, distance, route):
    """Translate display labels; use the same numeric and backend validation."""
    try:
        preferences = dict(mood=MOOD_OPTIONS[mood], max_minutes=positive_number(minutes),
                           scenery=SCENERY_OPTIONS[scenery], difficulty=difficulty.lower(),
                           max_distance=positive_number(distance) if extra else None,
                           route=ROUTE_OPTIONS[route] if extra else 'any')
    except (ValueError, KeyError):
        raise ValueError('Enter a positive number for walking time and, if enabled, distance.') from None
    validate_preferences(preferences)
    return preferences


def town_text(location, trails):
    lines = [location['name'], f"NSW {location['postcode']}", '', 'OVERVIEW', location['description']]
    for label, key in [('History', 'history'), ('Things to do', 'things_to_do'),
                       ('Food and supplies', 'food_supplies')]:
        lines.extend(['', label.upper(), location[key]])
    local = [t['name'] for t in trails if t['location_id'] == location['id']]
    nearby = [t['name'] for t in trails if t['id'] in location['nearby_walk_ids']]
    lines.extend(['', 'LOCAL WALKS', '\n'.join(local) or 'No local route in this catalogue.'])
    if nearby:
        lines.extend(['', 'NEARBY / CONNECTING WALKS — travel may be needed', '\n'.join(nearby)])
    lines.extend(['', 'REFERENCES', location['source'], location['visitor_source'],
                  location['food_source'], '', 'Check current opening hours and bookings.'])
    return '\n'.join(lines)


def elevation_text(trail):
    prefix = 'Approx. ' if trail['elevation_source'].startswith('Project estimate') else ''
    return f"{prefix}{trail['elevation_gain_m']} m"


def duration_text(minutes):
    hours, remainder = divmod(minutes, 60)
    return (f'{hours} hr' + (f' {remainder} min' if remainder else '')) if hours else f'{minutes} min'


def walk_detail_text(trail):
    return '\n'.join([
        trail['name'], trail['location_id'].replace('-', ' ').title(), '',
        f"{trail['distance_km']:g} km · {duration_text(trail['minutes'])} · "
        f"{trail['difficulty'].title()} · {trail['route'].title()}",
        elevation_text(trail) + ' elevation gain', '', 'ABOUT THIS WALK', trail['description'],
        '', 'SCENERY', ' · '.join(value.title() for value in trail['scenery']),
        '', 'MOOD', next(label for label, value in MOOD_OPTIONS.items() if value == trail['mood']),
        '', 'GETTING THERE', trail['transport_note'], '', 'ROUTE NOTES', trail['data_note'],
        '', 'REFERENCES', trail['source'], trail['elevation_source']])


def blend_colour(start, end, fraction):
    """Interpolate two palette colours for a short hover transition."""
    channels = [round(int(start[i:i + 2], 16) * (1 - fraction)
                      + int(end[i:i + 2], 16) * fraction) for i in (1, 3, 5)]
    return '#' + ''.join(f'{channel:02x}' for channel in channels)


class BlueMountainsGUI:
    """Three views over the shared catalogue; recommendation state is one report."""
    def __init__(self, root, locations, trails):
        self.root, self.locations, self.trails = root, locations, trails
        self.active_page = None
        self.report = None
        self.button_surfaces = {}
        root.title('Blue Mountains Handbook')
        root.geometry('1100x700')
        root.minsize(960, 700)
        root.configure(bg=BG_DARK)
        self.style()
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(root, style='Sidebar.TFrame', padding=(18, 28))
        sidebar.grid(row=0, column=0, sticky='ns')
        ttk.Label(sidebar, text='BLUE MOUNTAINS\nHANDBOOK', style='Identity.TLabel').pack(anchor='w')
        ttk.Label(sidebar, text='Personalised Bushwalking\n& Local Guide',
                  style='SidebarMuted.TLabel').pack(anchor='w', pady=(10, 32))
        self.pages, self.nav = {}, {}
        for name in ('Find a Walk', 'Browse Walks', 'Explore Towns'):
            button = ttk.Button(sidebar, text=name, style='Nav.TButton',
                                command=lambda n=name: self.show(n))
            self.add_hover(button, BG_SIDEBAR, BG_PANEL, '#24343B')
            button.pack(fill='x', pady=4)
            self.nav[name] = button
            page = ttk.Frame(root, padding=(30, 24, 26, 12))
            page.grid(row=0, column=1, sticky='nsew')
            self.pages[name] = page
        ttk.Label(sidebar, text='Offline guide', style='SidebarMuted.TLabel').pack(side='bottom', anchor='w')
        ttk.Label(root, text='Check current track notices, weather and access before walking.',
                  style='Muted.TLabel', padding=(24, 10)).grid(row=1, column=1, sticky='ew')
        self.build_find(self.pages['Find a Walk'])
        self.build_browse(self.pages['Browse Walks'])
        self.build_towns(self.pages['Explore Towns'])
        self.show('Find a Walk')

    def style(self):
        families = set(tkfont.families(self.root))
        self.font = next((name for name in ('SF Pro Text', 'Helvetica Neue', 'Helvetica')
                          if name in families), tkfont.nametofont('TkDefaultFont').actual('family'))
        style = self.ttk_style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', background=BG_DARK, foreground=TEXT_PRIMARY, font=(self.font, 11))
        style.configure('TFrame', background=BG_DARK)
        style.configure('Sidebar.TFrame', background=BG_SIDEBAR)
        style.configure('Identity.TLabel', background=BG_SIDEBAR, font=(self.font, 16, 'bold'))
        style.configure('SidebarMuted.TLabel', background=BG_SIDEBAR, foreground=TEXT_SECONDARY)
        # Keep standard keyboard activation, but omit the dotted focus element.
        style.layout('Nav.TButton', [('Button.border', {'sticky': 'nswe', 'children': [
            ('Button.padding', {'sticky': 'nswe', 'children': [
                ('Button.label', {'sticky': 'nswe'})]})]})])
        style.configure('Nav.TButton', background=BG_SIDEBAR, anchor='w', padding=(12, 12))
        style.map('Nav.TButton', background=[('active', BG_PANEL)])
        style.configure('Selected.Nav.TButton', background='#24343B')
        style.layout('Tile.TButton', style.layout('Nav.TButton'))
        # Replace the removed 1 px focus inset to preserve button dimensions.
        style.configure('Tile.TButton', padding=(15, 14), background=BG_PANEL)
        style.configure('Selected.Tile.TButton', background=ACCENT_BLUE)
        style.map('Selected.Tile.TButton', background=[('active', ACCENT_BLUE), ('pressed', ACCENT_BLUE)])
        style.map('Selected.Nav.TButton', background=[('active', '#24343B')])
        style.configure('TSeparator', background=BORDER)
        style.configure('TPanedwindow', background=BORDER)
        style.layout('Horizontal.Sash', [('Sash.hsash', {'sticky': 'nswe'})])
        style.configure('Horizontal.Sash', sashthickness=2)
        style.layout('Vertical.Sash', [('Sash.vsash', {'sticky': 'nswe'})])
        style.configure('Vertical.Sash', sashthickness=2)

        style.configure('TLabel', background=BG_DARK)
        style.configure('Muted.TLabel', foreground=TEXT_SECONDARY)
        style.configure('Title.TLabel', font=(self.font, 28, 'bold'))
        style.configure('Heading.TLabel', font=(self.font, 16, 'bold'), foreground=ACCENT_GREEN)
        style.configure('TScrollbar', background=BORDER, troughcolor=BG_PANEL,
                        arrowcolor=TEXT_SECONDARY, borderwidth=0)
        style.configure('TButton', background=BG_PANEL, padding=(12, 9), borderwidth=0)
        style.map('TButton', background=[('pressed', ACCENT_BLUE), ('active', BORDER)],
                  foreground=[('disabled', TEXT_SECONDARY)], bordercolor=[('focus', ACCENT_GREEN)])
        style.configure('Accent.TButton', background=ACCENT_BLUE)
        style.layout('Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children': [
            ('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]})])
        style.configure('Vertical.TScrollbar', width=7, background=BORDER, troughcolor=BG_DARK,
                        bordercolor=BG_DARK, lightcolor=BORDER, darkcolor=BORDER)
        style.configure('TEntry', borderwidth=0, relief='flat', bordercolor=BG_PANEL,
                        lightcolor=BG_PANEL, darkcolor=BG_PANEL)
        style.configure('TCombobox', borderwidth=0, relief='flat', bordercolor=BG_PANEL,
                        lightcolor=BG_PANEL, darkcolor=BG_PANEL, arrowcolor=TEXT_SECONDARY)
        style.map('TEntry', bordercolor=[('focus', TEXT_SECONDARY)])
        style.map('TCombobox', bordercolor=[('focus', TEXT_SECONDARY)])
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        style.configure('TEntry', fieldbackground=BG_PANEL, foreground=TEXT_PRIMARY,
                        insertcolor=TEXT_PRIMARY, padding=5)
        style.configure('TCombobox', fieldbackground=BG_PANEL, foreground=TEXT_PRIMARY, padding=5)
        style.map('TCombobox', fieldbackground=[('readonly', BG_PANEL)],
                  foreground=[('readonly', TEXT_PRIMARY)], selectbackground=[('readonly', BG_PANEL)])
        style.configure('TCheckbutton', background=BG_DARK, foreground=TEXT_PRIMARY)
        style.map('TCheckbutton', background=[('active', BG_DARK)])
        style.configure('Treeview', background=BG_PANEL, fieldbackground=BG_PANEL,
                        foreground=TEXT_PRIMARY, rowheight=40, borderwidth=0)
        style.configure('Treeview.Cell', padding=(12, 0))
        style.configure('Treeview.Heading', background=BG_SIDEBAR, foreground=TEXT_SECONDARY)
        style.map('Treeview', background=[('selected', ACCENT_BLUE)])
        self.root.option_add('*TCombobox*Listbox.background', BG_PANEL)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT_PRIMARY)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT_BLUE)

    def add_hover(self, button, normal, hover, selected=None):
        """Give each button an independent surface; retain ttk keyboard bindings."""
        name = f'Hover{len(self.button_surfaces)}.{button.cget("style")}'
        self.button_surfaces[button] = dict(style=name, normal=normal, hover=hover,
            selected_colour=selected, selected=False, hovered=False, colour=normal, job=None)
        # Override theme active/pressed maps so they cannot interrupt the fade.
        self.ttk_style.map(name, background=[('!disabled', normal)])
        button.configure(style=name)
        button.bind('<Enter>', lambda event: self.fade_surface(button, True), add='+')
        button.bind('<Leave>', lambda event: self.fade_surface(button, False), add='+')
        button.bind('<Destroy>', lambda event: self.cancel_fade(button), add='+')

    def cancel_fade(self, button):
        surface = self.button_surfaces[button]
        if surface['job'] is not None:
            self.root.after_cancel(surface['job'])
            surface['job'] = None

    def select_surface(self, button, selected):
        surface = self.button_surfaces[button]
        surface['selected'] = selected
        self.fade_surface(button)

    def fade_surface(self, button, hovered=None):
        surface = self.button_surfaces[button]
        if hovered is not None:
            surface['hovered'] = hovered
        self.cancel_fade(button)
        target = (surface['selected_colour'] if surface['selected'] else
                  surface['hover'] if surface['hovered'] else surface['normal'])
        # Selection is immediate and always retains the exact approved colour.
        if surface['selected']:
            surface['colour'] = target
            self.ttk_style.map(surface['style'], background=[('!disabled', target)])
            return
        start = surface['colour']
        if start == target:
            return

        def step(number):
            surface['job'] = None
            colour = target if number == 6 else blend_colour(start, target, number / 6)
            surface['colour'] = colour
            self.ttk_style.map(surface['style'], background=[('!disabled', colour)])
            if number < 6:
                surface['job'] = self.root.after(20, step, number + 1)

        surface['job'] = self.root.after(20, step, 1)

    def show(self, name):
        self.active_page = name
        self.pages[name].tkraise()
        if name == 'Browse Walks':
            self.root.after_idle(lambda: self.browse_split.sashpos(0, 420))
        elif name == 'Explore Towns':
            self.root.after_idle(lambda: self.towns_split.sashpos(0, 270))
        for label, button in self.nav.items():
            self.select_surface(button, label == name)

    def text_panel(self, parent):
        """One readable detail surface shared by walks and towns."""
        frame = ttk.Frame(parent)
        content = ttk.Frame(frame, padding=(36, 26, 12, 26))
        content.place(x=0, y=0, relheight=1)
        # About 650 px of readable text, with the scrollbar just 12 px beside it.
        frame.bind('<Configure>', lambda event: content.place_configure(
            width=min(722, max(1, event.width))))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        text = tk.Text(content, wrap='word', bg=BG_DARK, fg=TEXT_PRIMARY,
                       width=1, height=1, font=(self.font, 12), relief='flat',
                       padx=0, pady=0, borderwidth=0, selectbackground=ACCENT_BLUE,
                       highlightthickness=0, spacing1=2, spacing3=6, state='disabled')
        text.tag_configure('title', font=(self.font, 21, 'bold'), spacing3=8)
        text.tag_configure('metadata', foreground=TEXT_SECONDARY, font=(self.font, 11))
        text.tag_configure('section', font=(self.font, 11, 'bold'),
                           foreground=ACCENT_GREEN, spacing1=14, spacing3=6)
        scroll = ttk.Scrollbar(content, command=text.yview)
        text.configure(yscrollcommand=lambda first, last: self.scroll_visibility(scroll, first, last))
        text.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
        scroll.grid(row=0, column=1, sticky='ns')
        return frame, text

    def write(self, widget, text):
        """Apply the same title, metadata and section hierarchy on both pages."""
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        sections = {'OVERVIEW', 'ABOUT THIS WALK', 'HISTORY', 'THINGS TO DO',
                    'FOOD AND SUPPLIES', 'LOCAL WALKS', 'SCENERY', 'MOOD',
                    'GETTING THERE', 'ROUTE NOTES', 'REFERENCES'}
        for index, line in enumerate(text.splitlines(), 1):
            if index == 1:
                tag = 'title'
            elif index == 2 or (index in (4, 5) and ' · ' in line) or line.endswith(' elevation gain'):
                tag = 'metadata'
            elif line in sections or line.startswith('NEARBY / CONNECTING WALKS'):
                tag = 'section'
            else:
                continue
            widget.tag_add(tag, f'{index}.0', f'{index}.end')
        widget.configure(state='disabled')
        widget.yview_moveto(0)

    def master_list(self, parent, row):
        """Identical headerless, keyboard-selectable rows for both catalogues."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='nsew')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=('walk',), show='', selectmode='browse')
        tree.column('walk', width=200, minwidth=60, stretch=True)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(frame, command=tree.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        tree.configure(yscrollcommand=lambda first, last: self.scroll_visibility(scroll, first, last))
        return tree

    def selector(self, parent, label, values, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky='w', pady=(0, 6))
        var = tk.StringVar(value=list(values)[0])
        box = ttk.Combobox(parent, textvariable=var, values=list(values), state='readonly', width=27)
        box.grid(row=row + 1, column=0, sticky='ew')
        parent.columnconfigure(0, weight=1)
        return var

    def page_header(self, page, title, subtitle):
        ttk.Label(page, text=title, style='Title.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(page, text=subtitle, style='Muted.TLabel').grid(row=1, column=0, sticky='w', pady=(6, 18))
        page.columnconfigure(0, weight=1)

    def tiles(self, parent, variable, choices, columns):
        buttons = []
        for index, label in enumerate(choices):
            button = ttk.Button(parent, text=label, style='Tile.TButton',
                                command=lambda value=label: variable.set(value))
            self.add_hover(button, BG_PANEL, BORDER, ACCENT_BLUE)
            gap = 8 if index % columns < columns - 1 else 0
            button.grid(row=index // columns, column=index % columns,
                        sticky='ew', padx=(0, gap), pady=4)
            parent.columnconfigure(index % columns, weight=1, uniform='tiles')
            buttons.append((label, button))
        def update(*args):
            for label, button in buttons:
                self.select_surface(button, variable.get() == label)
        variable.trace_add('write', update)
        update()

    def build_find(self, page):
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)
        viewport = ttk.Frame(page, width=800)
        viewport.grid(row=0, column=0, sticky='ns')
        viewport.grid_propagate(False)
        viewport.columnconfigure(0, weight=1)
        viewport.rowconfigure(0, weight=1)
        # Match the page's 30 px left and 26 px right padding.
        page.bind('<Configure>', lambda event: viewport.configure(
            width=min(800, max(1, event.width - 56))))
        page = viewport
        self.find_canvas = tk.Canvas(page, background=BG_DARK, highlightthickness=0, borderwidth=0)
        self.find_canvas.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(page, command=self.find_canvas.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.find_canvas.configure(yscrollcommand=lambda first, last: self.scroll_visibility(scroll, first, last))
        content = ttk.Frame(self.find_canvas, padding=(0, 0, 12, 28))
        window = self.find_canvas.create_window(0, 0, window=content, anchor='nw')
        self.find_canvas.bind('<Configure>', lambda event: self.find_canvas.itemconfigure(window, width=event.width))
        content.bind('<Configure>', lambda event: self.find_canvas.configure(scrollregion=self.find_canvas.bbox('all')))
        self.root.bind_all('<MouseWheel>', self.scroll_find, add='+')
        self.root.bind_all('<Button-4>', self.scroll_find, add='+')
        self.root.bind_all('<Button-5>', self.scroll_find, add='+')
        self.root.bind_all('<FocusIn>', self.reveal_find_focus, add='+')
        page = content
        self.page_header(page, 'Find a Walk', 'What kind of day are you planning?')
        self.form = form = ttk.Frame(page)
        form.grid(row=2, column=0, sticky='ew')
        form.columnconfigure(0, weight=1)
        ttk.Label(form, text='How are you feeling today?').grid(row=0, column=0, sticky='w')
        self.mood = tk.StringVar(value='No preference')
        mood_tiles = ttk.Frame(form)
        mood_tiles.grid(row=1, column=0, sticky='ew', pady=(4, 12))
        self.tiles(mood_tiles, self.mood, MOOD_OPTIONS, 4)
        row = ttk.Frame(form)
        row.grid(row=2, column=0, sticky='ew')
        row.columnconfigure(0, weight=1, uniform='inputs')
        row.columnconfigure(1, weight=1, uniform='inputs')
        time = ttk.Frame(row, padding=(0, 0, 9, 0))
        time.grid(row=0, column=0, sticky='new')
        ttk.Label(time, text='Walking time · minutes').pack(anchor='w', pady=(0, 6))
        self.minutes = tk.StringVar()
        self.time_entry = ttk.Entry(time, textvariable=self.minutes, width=12)
        self.time_entry.pack(fill='x')
        scenery = ttk.Frame(row, padding=(9, 0, 0, 0))
        scenery.grid(row=0, column=1, sticky='new')
        self.scenery = self.selector(scenery, 'What would you like to see?', SCENERY_OPTIONS, 0)
        self.scenery.set('No preference')
        ttk.Label(form, text='What difficulty are you comfortable with?').grid(row=3, column=0, sticky='w', pady=(16, 4))
        self.difficulty = tk.StringVar(value='Easy')
        difficulty_tiles = ttk.Frame(form)
        difficulty_tiles.grid(row=4, column=0, sticky='ew')
        self.tiles(difficulty_tiles, self.difficulty, ['Easy', 'Moderate', 'Hard'], 3)
        self.extra = tk.BooleanVar()
        self.extra_button = ttk.Button(form, text='＋ More preferences',
                        command=self.toggle_extra_choice)
        self.extra_button.grid(row=5, column=0, sticky='w', pady=16)
        self.extra_frame = ttk.Frame(form)
        self.extra_frame.grid(row=6, column=0, sticky='ew')
        self.extra_frame.columnconfigure(0, weight=1, uniform='extras')
        self.extra_frame.columnconfigure(1, weight=1, uniform='extras')
        distance_frame = ttk.Frame(self.extra_frame, padding=(0, 0, 9, 0))
        distance_frame.grid(row=0, column=0, sticky='new')
        ttk.Label(distance_frame, text='Maximum distance · km').pack(anchor='w', pady=(0, 6))
        self.distance = tk.StringVar()
        self.distance_entry = ttk.Entry(distance_frame, textvariable=self.distance, width=12)
        self.distance_entry.pack(fill='x')
        route_frame = ttk.Frame(self.extra_frame, padding=(9, 0, 0, 0))
        route_frame.grid(row=0, column=1, sticky='new')
        self.route = self.selector(route_frame, 'Preferred route style', ROUTE_OPTIONS, 0)
        self.route.set('No preference')
        self.extra_frame.grid_remove()
        actions = ttk.Frame(page)
        actions.grid(row=3, column=0, sticky='ew', pady=(10, 8))
        self.find_button = ttk.Button(actions, text='Find My Walk', style='Accent.TButton', command=self.find)
        self.add_hover(self.find_button, ACCENT_BLUE,
                       blend_colour(ACCENT_BLUE, TEXT_SECONDARY, 0.15))
        self.find_button.pack(side='right')
        self.feedback = tk.StringVar(value='Allow extra time for travel and breaks.')
        ttk.Label(page, textvariable=self.feedback, style='Muted.TLabel', wraplength=700).grid(
            row=4, column=0, sticky='w', pady=(8, 24))
        self.results_heading = ttk.Frame(page)
        self.results_heading.grid(row=5, column=0, sticky='ew', pady=(20, 16))
        ttk.Label(self.results_heading, text='Your walk suggestions', style='Heading.TLabel').pack(side='left')
        self.save_button = ttk.Button(self.results_heading, text='Save Report', command=self.save, state='disabled')
        self.save_button.pack(side='right')
        self.results_heading.grid_remove()
        self.results = ttk.Frame(page)
        self.results.grid(row=6, column=0, sticky='ew')
        for variable in (self.mood, self.minutes, self.scenery, self.difficulty, self.extra, self.distance, self.route):
            variable.trace_add('write', self.preferences_changed)
        self.time_entry.bind('<Return>', lambda event: self.find())
        self.result_label(self.results, 'Choose how you’re feeling, how much time you have and what you’d like to see.')
        self.result_label(self.results, f'{len(self.trails)} walks · {len(self.locations)} Blue Mountains towns and areas', 'muted')

    def scroll_visibility(self, scrollbar, first, last):
        scrollbar.set(first, last)
        if float(first) <= 0 and float(last) >= 1:
            scrollbar.grid_remove()
        else:
            scrollbar.grid()

    def scroll_find(self, event):
        if self.active_page != 'Find a Walk':
            return
        widget = event.widget
        # Only route wheel events from widgets inside this page.
        if not str(widget).startswith(str(self.pages['Find a Walk'])):
            return
        if self.find_canvas.yview() == (0.0, 1.0):
            return
        if getattr(event, 'num', None) in (4, 5):
            amount = -3 if event.num == 4 else 3
        else:
            delta = event.delta
            amount = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
        self.find_canvas.yview_scroll(amount, 'units')
        return 'break'

    def reveal_find_focus(self, event):
        if self.active_page != 'Find a Walk' or not str(event.widget).startswith(str(self.form)):
            return
        self.root.update_idletasks()
        top = event.widget.winfo_rooty() - self.find_canvas.winfo_rooty()
        if top < 0 or top + event.widget.winfo_height() > self.find_canvas.winfo_height():
            bounds = self.find_canvas.bbox('all')
            if bounds:
                y = self.find_canvas.canvasy(0) + top
                self.find_canvas.yview_moveto(max(0, y - 20) / max(1, bounds[3]))

    def result_label(self, parent, text, role='body'):
        sizes = {'title': (21, 'bold'), 'section': (12, 'bold'), 'body': (12,), 'muted': (11,)}
        label = ttk.Label(parent, text=text, font=(self.font, *sizes[role]), justify='left',
                          foreground=TEXT_SECONDARY if role == 'muted' else TEXT_PRIMARY,
                          wraplength=650)
        label.pack(fill='x', anchor='w', pady=(12 if role == 'section' else 5, 5))
        label.bind('<Configure>', lambda event: label.configure(wraplength=max(100, event.width - 8)))
        return label

    def clear_results(self):
        for child in self.results.winfo_children():
            child.destroy()

    def toggle_extra_choice(self):
        self.extra.set(not self.extra.get())
        self.toggle_extra()

    def preferences_changed(self, *args):
        self.save_button.configure(state='disabled')
        self.report = None
        self.feedback.set('Preferences changed — select Find My Walk to update your suggestions.')

    def display_results(self, results, prefs):
        self.clear_results()
        self.results_heading.grid()
        self.result_label(self.results, f"Up to {prefs['max_minutes']:g} minutes · {prefs['difficulty'].title()} or easier", 'muted')
        for index, result in enumerate(results[:3], 1):
            trail = result['trail']
            if index > 1:
                ttk.Separator(self.results).pack(fill='x', pady=30)
            self.result_label(self.results, f'{index:02}', 'muted')
            self.result_label(self.results, trail['name'], 'title')
            self.result_label(self.results, trail['location_id'].replace('-', ' ').title(), 'muted')
            self.result_label(self.results, f"{trail['distance_km']:g} km · {duration_text(trail['minutes'])} · "
                              f"{trail['difficulty'].title()} · {trail['route'].title()}")
            self.result_label(self.results, 'Elevation gain: ' + elevation_text(trail), 'muted')
            matches = []
            if prefs['mood'] != 'any' and prefs['mood'] == trail['mood']:
                matches.append(next(label for label, value in MOOD_OPTIONS.items() if value == prefs['mood']))
            if prefs['scenery'] != 'any' and prefs['scenery'] in trail['scenery']:
                matches.append(prefs['scenery'].title())
            if prefs['route'] != 'any' and prefs['route'] == trail['route']:
                matches.append('Route style')
            if matches:
                self.result_label(self.results, 'Matches your day', 'section')
                self.result_label(self.results, ' · '.join(matches))
            self.result_label(self.results, trail['description'])
            notes = trade_offs(trail, prefs)
            if notes:
                self.result_label(self.results, 'Trade-offs', 'section')
                self.result_label(self.results, '\n'.join(notes))
            self.result_label(self.results, 'Getting there', 'section')
            self.result_label(self.results, trail['transport_note'])
            self.result_label(self.results, 'Preparation', 'section')
            self.result_label(self.results, '\n'.join(preparation(trail, True)))
        self.root.update_idletasks()
        bounds = self.find_canvas.bbox('all')
        if bounds:
            self.find_canvas.yview_moveto(self.results_heading.winfo_y() / max(1, bounds[3]))

    def toggle_extra(self):
        self.extra_button.configure(text='− Fewer preferences' if self.extra.get() else '＋ More preferences')
        if self.extra.get():
            self.extra_frame.grid()
        else:
            self.extra_frame.grid_remove()

    def find(self):
        self.report = None
        self.save_button.configure(state='disabled')
        for variable, entry, label in ((self.minutes, self.time_entry, 'walking time in minutes'),
                                        (self.distance, self.distance_entry, 'maximum distance in km')):
            if variable is self.distance and not self.extra.get():
                continue
            try:
                positive_number(variable.get())
            except ValueError:
                self.feedback.set(f'Enter a positive number for {label}, for example 70 minutes or 5 km.')
                entry.focus_set()
                entry.selection_range(0, 'end')
                return
        try:
            prefs = preferences_from_form(self.mood.get(), self.minutes.get(), self.scenery.get(),
                                          self.difficulty.get(), self.extra.get(), self.distance.get(),
                                          self.route.get())
        except ValueError as error:
            self.feedback.set(str(error))
            return
        results = recommend(self.trails, prefs)
        if not results:
            longer = time_alternatives(self.trails, prefs)
            if longer:
                minutes = longer[0]['minutes']
                if messagebox.askyesno('Allow more walking time?',
                        f'No walk fits your current limits. The shortest option within your other '
                        f'limits needs {minutes} minutes.\n\nAllow {minutes} minutes instead?', parent=self.root):
                    prefs['max_minutes'] = minutes
                    self.minutes.set(str(minutes))
                    results = recommend(self.trails, prefs)
            if not results:
                self.clear_results()
                self.results_heading.grid_remove()
                self.result_label(self.results, 'No walks match these limits.', 'title')
                self.result_label(self.results, 'Your limits have not changed. Try another time, distance or difficulty.')
                self.feedback.set('No matches. Adjust your preferences and try again.')
                return
        self.report = format_results(results, prefs, True)
        self.display_results(results, prefs)
        self.feedback.set(f'{min(3, len(results))} suggestions found. Full route details are in Browse Walks.')
        self.save_button.configure(state='normal')

    def save(self):
        if self.report is None:
            return
        try:
            path = save_report(self.report)
        except OSError as error:
            messagebox.showerror('Could not save report', str(error), parent=self.root)
        else:
            self.feedback.set(f'Report saved — appended to {path.name}.')

    def build_browse(self, page):
        self.page_header(page, 'Browse Walks', 'Explore the trails. Select a walk to read its story.')
        page.rowconfigure(2, weight=1)
        split = ttk.Panedwindow(page, orient='horizontal')
        split.grid(row=2, column=0, sticky='nsew')
        listing = ttk.Frame(split, padding=(0, 0, 12, 0))
        listing.columnconfigure(0, weight=1)
        listing.rowconfigure(2, weight=1)
        split.add(listing, weight=0)
        self.browse_split = split
        self.root.after_idle(lambda: split.sashpos(0, 420))
        self.area = self.selector(listing, 'Area', ['All'] + [l['name'] for l in self.locations], 0)
        listing.winfo_children()[-1].bind('<<ComboboxSelected>>', lambda event: self.filter_walks())
        self.tree = self.master_list(listing, 2)
        self.tree.bind('<<TreeviewSelect>>', self.walk_details)
        self.tree.bind('<Configure>', lambda event: self.fit_walk_names())
        panel, self.details = self.text_panel(split)
        split.add(panel, weight=3)
        self.filter_walks()

    def filter_walks(self):
        self.tree.delete(*self.tree.get_children())
        location = next((l for l in self.locations if l['name'] == self.area.get()), None)
        for trail in self.trails:
            if location and trail['location_id'] != location['id'] and trail['id'] not in location['nearby_walk_ids']:
                continue
            name = trail['name']
            if location and trail['location_id'] != location['id']:
                name += ' (nearby / connecting)'
            self.tree.insert('', 'end', iid=trail['id'], values=(name,))
        self.fit_walk_names()
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.walk_details()
        else:
            self.write(self.details, 'No walks in this area.')

    def fit_walk_names(self):
        font = tkfont.Font(family=self.font, size=11)
        width = max(100, self.tree.winfo_width() - 32)
        self.tree.column('walk', width=width)
        location = next((l for l in self.locations if l['name'] == self.area.get()), None)
        for trail in self.trails:
            if not self.tree.exists(trail['id']):
                continue
            name = trail['name']
            if location and trail['location_id'] != location['id']:
                name = 'Nearby · ' + name
            display = name
            while len(display) > 1 and font.measure(display) > width:
                display = display[:-2] + '…'
            self.tree.item(trail['id'], values=(display,))

    def walk_details(self, event=None):
        selection = self.tree.selection()
        if selection:
            trail = next(t for t in self.trails if t['id'] == selection[0])
            text = walk_detail_text(trail)
            location = next((l for l in self.locations if l['name'] == self.area.get()), None)
            if location and trail['location_id'] != location['id']:
                text += '\n\nNearby / connecting walk — travel to another area may be needed.'
            self.write(self.details, text)

    def build_towns(self, page):
        self.page_header(page, 'Explore Towns', 'A local handbook, from the foothills to the upper mountains.')
        page.rowconfigure(2, weight=1)
        split = ttk.Panedwindow(page, orient='horizontal')
        split.grid(row=2, column=0, sticky='nsew')
        listing = ttk.Frame(split, padding=(0, 0, 12, 0))
        listing.columnconfigure(0, weight=1)
        listing.rowconfigure(0, weight=1)
        split.add(listing, weight=0)
        self.towns_split = split
        self.root.after_idle(lambda: split.sashpos(0, 270))
        self.town_list = self.master_list(listing, 0)
        for location in self.locations:
            self.town_list.insert('', 'end', iid=location['id'], values=(location['name'],))
        panel, self.town_details = self.text_panel(split)
        split.add(panel, weight=3)
        self.town_list.bind('<<TreeviewSelect>>', self.show_town)
        self.town_list.selection_set(self.locations[0]['id'])
        self.show_town()

    def show_town(self, event=None):
        selected = self.town_list.selection()
        if not selected:
            return
        location = next(l for l in self.locations if l['id'] == selected[0])
        text = town_text(location, self.trails)
        self.write(self.town_details, text)


def main():
    if tk is None:
        print('Tkinter is unavailable. Use a Python installation with Tkinter, or run python3 main.py.')
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f'Cannot open the graphical interface: {error}. Run python3 main.py for the terminal version.')
        return 1
    try:
        locations, trails = load_catalogue()
    except (OSError, ValueError, csv.Error) as error:
        root.withdraw()
        messagebox.showerror('Cannot load catalogue', str(error), parent=root)
        root.destroy()
        return 1
    BlueMountainsGUI(root, locations, trails)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
