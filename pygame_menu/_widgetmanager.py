"""
pygame-menu
https://github.com/ppizarror/pygame-menu

MENU WIDGET MANAGER
Easy widget add/remove to Menus.

License:
-------------------------------------------------------------------------------
The MIT License (MIT)
Copyright 2017-2021 Pablo Pizarro R. @ppizarror

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-------------------------------------------------------------------------------
"""

__all__ = ['WidgetManager']

import textwrap
import warnings
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pygame_menu
import pygame_menu.widgets
import pygame_menu.events as _events
import pygame_menu.locals as _locals
import pygame_menu.themes as _themes
import pygame_menu.utils as _utils

from pygame_menu.widgets.widget.colorinput import ColorInputColorType, ColorInputHexFormatType
from pygame_menu.widgets.widget.textinput import TextInputModeType
from pygame_menu._types import Any, Union, Callable, Dict, Optional, CallbackType, \
    NumberType, Vector2NumberType, List, Tuple


# noinspection PyProtectedMember
class WidgetManager(object):
    """
    Add/Remove widgets to the Menu.

    :param menu: Menu reference
    """
    _menu: 'pygame_menu.Menu'

    def __init__(self, menu: 'pygame_menu.Menu') -> None:
        self._menu = menu

    @property
    def _theme(self) -> '_themes.Theme':
        """
        Return menu theme.

        :return: Menu theme reference
        """
        return self._menu.get_theme()

    def _filter_widget_attributes(self, kwargs: Dict) -> Dict[str, Any]:
        """
        Return the valid widgets attributes from a dictionary.
        The valid (key, value) are removed from the initial dictionary.

        :param kwargs: Optional keyword arguments (input attributes)
        :return: Dictionary of valid attributes
        """
        attributes = {}
        align = kwargs.pop('align', self._theme.widget_alignment)
        assert isinstance(align, str)
        attributes['align'] = align

        background_is_color = False
        background_color = kwargs.pop('background_color', self._theme.widget_background_color)
        if background_color is not None:
            if isinstance(background_color, pygame_menu.BaseImage):
                pass
            else:
                _utils.assert_color(background_color)
                background_is_color = True
        attributes['background_color'] = background_color

        background_inflate = kwargs.pop('background_inflate', self._theme.widget_background_inflate)
        _utils.assert_vector(background_inflate, 2)
        assert background_inflate[0] >= 0 and background_inflate[1] >= 0, \
            'both background inflate components must be equal or greater than zero'
        attributes['background_inflate'] = background_inflate

        border_color = kwargs.pop('border_color', self._theme.widget_border_color)
        _utils.assert_color(border_color)
        attributes['border_color'] = border_color

        border_inflate = kwargs.pop('border_inflate', self._theme.widget_border_inflate)
        _utils.assert_vector(border_inflate, 2)
        assert isinstance(border_inflate[0], int) and border_inflate[0] >= 0
        assert isinstance(border_inflate[1], int) and border_inflate[1] >= 0
        attributes['border_inflate'] = border_inflate

        border_width = kwargs.pop('border_width', self._theme.widget_border_width)
        assert isinstance(border_width, int) and border_width >= 0
        attributes['border_width'] = border_width

        attributes['font_antialias'] = self._theme.widget_font_antialias

        font_background_color = kwargs.pop('font_background_color', self._theme.widget_font_background_color)
        if font_background_color is None and \
                self._theme.widget_font_background_color_from_menu and \
                not background_is_color:
            if isinstance(self._theme.background_color, tuple):  # Is color
                _utils.assert_color(self._theme.background_color)
                font_background_color = self._theme.background_color
        attributes['font_background_color'] = font_background_color

        font_color = kwargs.pop('font_color', self._theme.widget_font_color)
        _utils.assert_color(font_color)
        attributes['font_color'] = font_color

        font_name = kwargs.pop('font_name', self._theme.widget_font)
        assert isinstance(font_name, (str, Path))
        attributes['font_name'] = str(font_name)

        font_size = kwargs.pop('font_size', self._theme.widget_font_size)
        assert isinstance(font_size, int)
        assert font_size > 0, 'font size must be greater than zero'
        attributes['font_size'] = font_size

        margin = kwargs.pop('margin', self._theme.widget_margin)
        assert isinstance(margin, tuple)
        assert len(margin) == 2, 'margin must be a tuple or list of 2 numbers'
        attributes['margin'] = margin

        padding = kwargs.pop('padding', self._theme.widget_padding)
        assert isinstance(padding, (int, float, tuple))
        attributes['padding'] = padding

        readonly_color = kwargs.pop('readonly_color', self._theme.readonly_color)
        _utils.assert_color(readonly_color)
        attributes['readonly_color'] = readonly_color

        readonly_selected_color = kwargs.pop('readonly_selected_color', self._theme.readonly_selected_color)
        _utils.assert_color(readonly_selected_color)
        attributes['readonly_selected_color'] = readonly_selected_color

        selection_color = kwargs.pop('selection_color', self._theme.selection_color)
        _utils.assert_color(selection_color)
        attributes['selection_color'] = selection_color

        selection_effect = kwargs.pop('selection_effect', self._theme.widget_selection_effect)
        if selection_effect is None:
            selection_effect = pygame_menu.widgets.NoneSelection()
        assert isinstance(selection_effect, pygame_menu.widgets.core.Selection)
        attributes['selection_effect'] = selection_effect

        shadow = kwargs.pop('shadow', self._theme.widget_shadow)
        assert isinstance(shadow, bool)
        attributes['shadow'] = shadow

        shadow_color = kwargs.pop('shadow_color', self._theme.widget_shadow_color)
        _utils.assert_color(shadow_color)
        attributes['shadow_color'] = shadow_color

        shadow_position = kwargs.pop('shadow_position', self._theme.widget_shadow_position)
        assert isinstance(shadow_position, str)
        attributes['shadow_position'] = shadow_position

        shadow_offset = kwargs.pop('shadow_offset', self._theme.widget_shadow_offset)
        assert isinstance(shadow_offset, (int, float))
        attributes['shadow_offset'] = shadow_offset

        return attributes

    @staticmethod
    def _check_kwargs(kwargs: Dict) -> None:
        """
        Check kwargs after widget addition. It should be empty. Raises ``ValueError``.

        :param kwargs: Kwargs dict
        :return: None
        """
        for invalid_keyword in kwargs.keys():
            msg = 'widget addition optional parameter kwargs.{} is not valid'.format(invalid_keyword)
            raise ValueError(msg)

    def _append_widget(self, widget: 'pygame_menu.widgets.Widget') -> None:
        """
        Add a widget to the list of widgets.

        :param widget: Widget object
        :return: None
        """
        assert isinstance(widget, pygame_menu.widgets.Widget)
        assert widget.get_menu() == self._menu, 'widget cannot have a different instance of menu'
        self._menu._widgets.append(widget)
        if self._menu._index < 0 and widget.is_selectable:
            widget.select()
            self._menu._index = len(self._menu._widgets) - 1
        self._menu._stats.added_widgets += 1
        self._menu._widgets_surface = None  # If added on execution time forces the update of the surface
        self._menu._render()

    def _configure_widget(self, widget: 'pygame_menu.widgets.Widget', **kwargs) -> None:
        """
        Update the given widget with the parameters defined at
        the Menu level.

        :param widget: Widget object
        :param kwargs: Optional keywords arguments
        :return: None
        """
        assert isinstance(widget, pygame_menu.widgets.Widget)
        assert widget.get_menu() is None, 'widget cannot have an instance of menu'

        widget.set_menu(self._menu)
        self._menu._check_id_duplicated(widget.get_id())

        widget.set_alignment(
            align=kwargs['align']
        )
        widget.set_background_color(
            color=kwargs['background_color'],
            inflate=kwargs['background_inflate']
        )
        widget.set_border(
            width=kwargs['border_width'],
            color=kwargs['border_color'],
            inflate=kwargs['border_inflate']
        )
        widget.set_controls(
            joystick=self._menu._joystick,
            mouse=self._menu._mouse,
            touchscreen=self._menu._touchscreen
        )
        widget.set_font(
            antialias=kwargs['font_antialias'],
            background_color=kwargs['font_background_color'],
            color=kwargs['font_color'],
            font=kwargs['font_name'],
            font_size=kwargs['font_size'],
            readonly_color=kwargs['readonly_color'],
            readonly_selected_color=kwargs['readonly_selected_color'],
            selected_color=kwargs['selection_color']
        )
        widget.set_margin(
            x=kwargs['margin'][0],
            y=kwargs['margin'][1]
        )
        widget.set_padding(
            padding=kwargs['padding']
        )
        widget.set_selection_effect(
            selection=kwargs['selection_effect']
        )
        widget.set_shadow(
            color=kwargs['shadow_color'],
            enabled=kwargs['shadow'],
            offset=kwargs['shadow_offset'],
            position=kwargs['shadow_position']
        )

    def button(self,
               title: Any,
               action: Optional[Union['pygame_menu.Menu', '_events.MenuAction', Callable, int]],
               *args,
               **kwargs
               ) -> 'pygame_menu.widgets.Button':
        """
        Adds a button to the Menu.

        The arguments and unknown keyword arguments are passed to the action, if
        it's a callable object:

        .. code-block:: python

            action(*args)

        If ``accept_kwargs=True`` then the ``**kwargs`` are also unpacked on action call:

        .. code-block:: python

            action(*args, **kwargs)

        If ``onselect`` is defined, the callback is executed as follows:

        .. code-block:: python

            onselect(selected, widget, menu)

        kwargs (Optional)
            - ``accept_kwargs``             *(bool)* – Button action accepts ``**kwargs`` if it's a callable object (function-type), ``False`` by default
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``back_count``                *(int)* - Number of menus to go back if action is :py:data:`pygame_menu.events.BACK` event, default is ``1``
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``button_id``                 *(str)* - Widget ID
            - ``font_background_color``     *(tuple, list, None)* - Widget font background color
            - ``font_color``                *(tuple, list)* - Widget font color
            - ``font_name``                 *(str, Path)* - Widget font path
            - ``font_size``                 *(int)* - Font size of the widget
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``onselect``                  *(callable, None)* - Callback executed when selecting the widget
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: *(top, right, bottom, left)*
            - ``readonly_color``            *(tuple, list)* - Color of the widget if readonly mode
            - ``readonly_selected_color``   *(tuple, list)* - Color of the widget if readonly mode and is selected
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect
            - ``shadow``                    *(bool)* - Text shadow is enabled or disabled
            - ``shadow_color``              *(tuple, list)* - Text shadow color
            - ``shadow_position``           *(str)* - Text shadow position, see locals for position
            - ``shadow_offset``             *(int, float)* - Text shadow offset

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            Using ``action=None`` is the same as using ``action=pygame_menu.events.NONE``.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        .. warning::

            Be careful with kwargs collision. Consider that all optional documented
            kwargs keys are removed from the object.

        :param title: Title of the button
        :param action: Action of the button, can be a Menu, an event, or a function
        :param args: Additional arguments used by a function
        :param kwargs: Optional keyword arguments
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.Button`
        """
        total_back = kwargs.pop('back_count', 1)
        assert isinstance(total_back, int) and 1 <= total_back

        # Get ID
        button_id = kwargs.pop('button_id', '')
        assert isinstance(button_id, str), 'id must be a string'

        # Accept kwargs
        accept_kwargs = kwargs.pop('accept_kwargs', False)
        assert isinstance(accept_kwargs, bool)

        # Onselect callback
        onselect = kwargs.pop('onselect', None)

        # Filter widget attributes to avoid passing them to the callbacks
        attributes = self._filter_widget_attributes(kwargs)

        # Change action if certain events
        if action == _events.PYGAME_QUIT or action == _events.PYGAME_WINDOWCLOSE:
            action = _events.EXIT
        elif action is None:
            action = _events.NONE

        # If element is a Menu
        if isinstance(action, type(self._menu)):
            # Check for recursive
            if action == self._menu or action.in_submenu(self._menu, recursive=True):
                msg = 'Menu "{0}" is already on submenu structure, recursive menus lead ' \
                      'to unexpected behaviours. For returning to previous menu use ' \
                      'pygame_menu.events.BACK event defining an optional back_count ' \
                      'number of menus to return from, default is 1'.format(action.get_title())
                raise ValueError(msg)

            self._menu._submenus.append(action)
            widget = pygame_menu.widgets.Button(title, button_id, self._menu._open, action)
            widget.to_menu = True

        # If element is a MenuAction
        elif action == _events.BACK:  # Back to Menu
            widget = pygame_menu.widgets.Button(title, button_id, self._menu.reset, total_back)

        elif action == _events.CLOSE:  # Close Menu
            widget = pygame_menu.widgets.Button(title, button_id, self._menu._close)

        elif action == _events.EXIT:  # Exit program
            widget = pygame_menu.widgets.Button(title, button_id, self._menu._exit)

        elif action == _events.NONE:  # None action
            widget = pygame_menu.widgets.Button(title, button_id)

        elif action == _events.RESET:  # Back to Top Menu
            widget = pygame_menu.widgets.Button(title, button_id, self._menu.full_reset)

        # If element is a function or callable
        elif _utils.is_callable(action):
            if not accept_kwargs:
                widget = pygame_menu.widgets.Button(title, button_id, action, *args)
            else:
                widget = pygame_menu.widgets.Button(title, button_id, action, *args, **kwargs)

        else:
            raise ValueError('action must be a Menu, a MenuAction (event), a function (callable), or None')

        # Configure and add the button
        if not accept_kwargs:
            try:
                self._check_kwargs(kwargs)
            except ValueError:
                warnings.warn('button cannot accept kwargs. If you want to use kwargs options set accept_kwargs=True')
                raise
        self._configure_widget(widget=widget, **attributes)
        widget.set_selection_callback(onselect)
        self._append_widget(widget)
        return widget

    def color_input(self,
                    title: Union[str, Any],
                    color_type: ColorInputColorType,
                    color_id: str = '',
                    default: Any = '',
                    hex_format: ColorInputHexFormatType = 'none',
                    input_separator: str = ',',
                    input_underline: str = '_',
                    onchange: CallbackType = None,
                    onreturn: CallbackType = None,
                    onselect: Optional[Callable[[bool, 'pygame_menu.widgets.Widget', 'pygame_menu.Menu'], Any]] = None,
                    **kwargs
                    ) -> 'pygame_menu.widgets.ColorInput':
        """
        Add a color widget with RGB or Hex format to the Menu.
        Includes a preview box that renders the given color.

        The callbacks receive the current value and all unknown keyword
        arguments, where ``current_color=widget.get_value()``:

        .. code-block:: python

            onchange(current_color, **kwargs)
            onreturn(current_color, **kwargs)
            onselect(selected, widget, menu)

        kwargs (Optional)
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``dynamic_width``             *(int, float)* - If ``True`` the widget width changes if the previsualization color box is active or not
            - ``font_background_color``     *(tuple, list, None)* - Widget font background color
            - ``font_color``                *(tuple, list)* - Widget font color
            - ``font_name``                 *(str, Path)* - Widget font path
            - ``font_size``                 *(int)* - Font size of the widget
            - ``input_underline_vmargin``   *(int)* - Vertical margin of underline (px)
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: *(top, right, bottom, left)*
            - ``previsualization_margin``   *(int)* - Previsualization left margin from text input in px. Default is ``0``
            - ``previsualization_width``    *(int, float)* - Previsualization width as a factor of the height. Default is ``3``
            - ``readonly_color``            *(tuple, list)* - Color of the widget if readonly mode
            - ``readonly_selected_color``   *(tuple, list)* - Color of the widget if readonly mode and is selected
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect
            - ``shadow``                    *(bool)* - Text shadow is enabled or disabled
            - ``shadow_color``              *(tuple, list)* - Text shadow color
            - ``shadow_position``           *(str)* - Text shadow position, see locals for position
            - ``shadow_offset``             *(int, float)* - Text shadow offset

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        .. warning::

            Be careful with kwargs collision. Consider that all optional documented
            kwargs keys are removed from the object.

        :param title: Title of the color input
        :param color_type: Type of the color input
        :param color_id: ID of the color input
        :param default: Default value to display, if RGB type it must be a tuple ``(r,g,b)``, if HEX must be a string ``"#XXXXXX"``
        :param hex_format: Hex format string mode
        :param input_separator: Divisor between RGB channels, not valid in HEX format
        :param input_underline: Underline character
        :param onchange: Callback executed when changing the values of the color text
        :param onreturn: Callback executed when pressing return on the color text input
        :param onselect: Callback executed when selecting the widget
        :param kwargs: Optional keyword arguments
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.ColorInput`
        """
        assert isinstance(default, (str, tuple))

        # Filter widget attributes to avoid passing them to the callbacks
        attributes = self._filter_widget_attributes(kwargs)

        dynamic_width = kwargs.pop('dynamic_width', True)
        input_underline_vmargin = kwargs.pop('input_underline_vmargin', 0)
        prev_margin = kwargs.pop('previsualization_margin', 10)
        prev_width = kwargs.pop('previsualization_width', 3)

        widget = pygame_menu.widgets.ColorInput(
            color_type=color_type,
            colorinput_id=color_id,
            cursor_color=self._theme.cursor_color,
            cursor_switch_ms=self._theme.cursor_switch_ms,
            dynamic_width=dynamic_width,
            hex_format=hex_format,
            input_separator=input_separator,
            input_underline=input_underline,
            input_underline_vmargin=input_underline_vmargin,
            onchange=onchange,
            onreturn=onreturn,
            onselect=onselect,
            prev_margin=prev_margin,
            prev_width_factor=prev_width,
            title=title,
            **kwargs
        )

        self._configure_widget(widget=widget, **attributes)
        widget.set_default_value(default)
        self._append_widget(widget)

        return widget

    def image(self,
              image_path: Union[str, 'Path', 'pygame_menu.BaseImage', 'BytesIO'],
              angle: NumberType = 0,
              image_id: str = '',
              onselect: Optional[Callable[[bool, 'pygame_menu.widgets.Widget', 'pygame_menu.Menu'], Any]] = None,
              scale: Vector2NumberType = (1, 1),
              scale_smooth: bool = True,
              selectable: bool = False,
              **kwargs
              ) -> 'pygame_menu.widgets.Image':
        """
        Add a simple image to the Menu.

        If ``onselect`` is defined, the callback is executed as follows:

        .. code-block:: python

            onselect(selected, widget, menu)

        kwargs (Optional)
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: (top, right, bottom, left)
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        :param image_path: Path of the image (file) or a BaseImage object. If BaseImage object is provided the angle and scale are ignored
        :param angle: Angle of the image in degrees (clockwise)
        :param image_id: ID of the label
        :param onselect: Callback executed when selecting the widget
        :param scale: Scale of the image *(x, y)*
        :param scale_smooth: Scale is smoothed
        :param selectable: Image accepts user selection
        :param kwargs: Optional keyword arguments
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.Image`
        """
        assert isinstance(selectable, bool)

        # Remove invalid keys from kwargs
        for key in ['font_background_color', 'font_color', 'font_name', 'font_size', 'shadow', 'shadow_color',
                    'shadow_position', 'shadow_offset']:
            kwargs.pop(key, None)

        # Filter widget attributes to avoid passing them to the callbacks
        attributes = self._filter_widget_attributes(kwargs)

        widget = pygame_menu.widgets.Image(
            angle=angle,
            image_id=image_id,
            image_path=image_path,
            onselect=onselect,
            scale=scale,
            scale_smooth=scale_smooth
        )
        widget.is_selectable = selectable

        self._check_kwargs(kwargs)
        self._configure_widget(widget=widget, **attributes)
        self._append_widget(widget)

        return widget

    def label(self,
              title: Any,
              label_id: str = '',
              max_char: int = 0,
              onselect: Optional[Callable[[bool, 'pygame_menu.widgets.Widget', 'pygame_menu.Menu'], Any]] = None,
              selectable: bool = False,
              **kwargs
              ) -> Union['pygame_menu.widgets.Label', List['pygame_menu.widgets.Label']]:
        """
        Add a simple text to the Menu.

        If ``onselect`` is defined, the callback is executed as follows:

        .. code-block:: python

            onselect(selected, widget, menu)

        kwargs (Optional)
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``font_background_color``     *(tuple, list, None)* - Widget font background color
            - ``font_color``                *(tuple, list)* - Widget font color
            - ``font_name``                 *(str, Path)* - Widget font path
            - ``font_size``                 *(int)* - Font size of the widget
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: *(top, right, bottom, left)*
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect
            - ``shadow``                    *(bool)* - Text shadow is enabled or disabled
            - ``shadow_color``              *(tuple, list)* - Text shadow color
            - ``shadow_position``           *(str)* - Text shadow position, see locals for position
            - ``shadow_offset``             *(int, float)* - Text shadow offset

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        :param title: Text to be displayed
        :param label_id: ID of the label
        :param max_char: Split the title in several labels if the string length exceeds ``max_char``; ``0``: don't split, ``-1``: split to Menu width
        :param onselect: Callback executed when selecting the widget
        :param selectable: Label accepts user selection, if ``False`` long paragraphs cannot be scrolled through keyboard
        :param kwargs: Optional keyword arguments
        :return: Widget object, or List of widgets if the text overflows
        :rtype: :py:class:`pygame_menu.widgets.Label`, list[:py:class:`pygame_menu.widgets.Label`]
        """
        assert isinstance(label_id, str)
        assert isinstance(max_char, int)
        assert isinstance(selectable, bool)
        assert max_char >= -1

        title = str(title)
        if len(label_id) == 0:
            label_id = str(uuid4())

        # If newline detected, split in two new lines
        if '\n' in title:
            title = title.split('\n')
            widgets = []
            for t in title:
                wig = self.label(
                    title=t,
                    label_id=label_id + '+' + str(len(widgets) + 1),
                    max_char=max_char,
                    onselect=onselect,
                    selectable=selectable,
                    **kwargs
                )
                if isinstance(wig, list):
                    for w in wig:
                        widgets.append(w)
                else:
                    widgets.append(wig)
            return widgets

        # Wrap text to Menu width (imply additional calls to render functions)
        if max_char < 0:
            dummy_attrs = self._filter_widget_attributes(kwargs.copy())
            dummy = pygame_menu.widgets.Label(title=title)
            self._configure_widget(dummy, **dummy_attrs)
            max_char = int(1.0 * self._menu.get_width(inner=True) * len(title) / dummy.get_width())

        # If no overflow
        if len(title) <= max_char or max_char == 0:
            attributes = self._filter_widget_attributes(kwargs)
            widget = pygame_menu.widgets.Label(
                label_id=label_id,
                onselect=onselect,
                title=title
            )
            widget.is_selectable = selectable
            self._check_kwargs(kwargs)
            self._configure_widget(widget=widget, **attributes)
            self._append_widget(widget)

        else:
            self._menu._check_id_duplicated(label_id)  # Before adding + LEN
            widget = []
            for line in textwrap.wrap(title, max_char):
                widget.append(
                    self.label(
                        title=line,
                        label_id=label_id + '+' + str(len(widget) + 1),
                        max_char=max_char,
                        onselect=onselect,
                        selectable=selectable,
                        **kwargs
                    )
                )

        return widget

    def selector(self,
                 title: Any,
                 items: Union[List[Tuple[Any, ...]], List[str]],
                 default: int = 0,
                 onchange: CallbackType = None,
                 onreturn: CallbackType = None,
                 onselect: Optional[Callable[[bool, 'pygame_menu.widgets.Widget', 'pygame_menu.Menu'], Any]] = None,
                 selector_id: str = '',
                 **kwargs
                 ) -> 'pygame_menu.widgets.Selector':
        """
        Add a selector to the Menu: several items with values and
        two functions that are executed when changing the selector (left/right)
        and pressing return button on the selected item.

        The values of the selector are like:

        .. code-block:: python

            values = [('Item1', a, b, c...), ('Item2', d, e, f...)]

        The callbacks receive the current text, its index in the list,
        the associated arguments, and all unknown keyword arguments, where
        ``selected_value=widget.get_value()`` and ``selected_index=widget.get_index()``:

        .. code-block:: python

            onchange((selected_value, selected_index), a, b, c..., **kwargs)
            onreturn((selected_value, selected_index), a, b, c..., **kwargs)
            onselect(selected, widget, menu)

        For example, if ``selected_index=0`` then ``selected_value=('Item1', a, b, c...)``.

        kwargs (Optional)
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``font_background_color``     *(tuple, list, None)* - Widget font background color
            - ``font_color``                *(tuple, list)* - Widget font color
            - ``font_name``                 *(str, Path)* - Widget font path
            - ``font_size``                 *(int)* - Font size of the widget
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: *(top, right, bottom, left)*
            - ``readonly_color``            *(tuple, list)* - Color of the widget if readonly mode
            - ``readonly_selected_color``   *(tuple, list)* - Color of the widget if readonly mode and is selected
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect
            - ``shadow``                    *(bool)* - Text shadow is enabled or disabled
            - ``shadow_color``              *(tuple, list)* - Text shadow color
            - ``shadow_position``           *(str)* - Text shadow position, see locals for position
            - ``shadow_offset``             *(int, float)* - Text shadow offset

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        .. warning::

            Be careful with kwargs collision. Consider that all optional documented
            kwargs keys are removed from the object.

        :param title: Title of the selector
        :param items: Elements of the selector ``[('Item1', a, b, c...), ('Item2', d, e, f...)]``
        :param default: Index of default value to display
        :param onchange: Callback executed when when changing the selector
        :param onreturn: Callback executed when pressing return button
        :param onselect: Callback executed when selecting the widget
        :param selector_id: ID of the selector
        :param kwargs: Optional keyword arguments
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.Selector`
        """
        # Filter widget attributes to avoid passing them to the callbacks
        attributes = self._filter_widget_attributes(kwargs)

        widget = pygame_menu.widgets.Selector(
            default=default,
            elements=items,
            onchange=onchange,
            onreturn=onreturn,
            onselect=onselect,
            selector_id=selector_id,
            title=title,
            **kwargs
        )

        self._configure_widget(widget=widget, **attributes)
        self._append_widget(widget)

        return widget

    def toggle_switch(self,
                      title: Any,
                      default: Union[int, bool] = 0,
                      onchange: CallbackType = None,
                      toggleswitch_id: str = '',
                      state_text: Tuple[str, ...] = ('Off', 'On'),
                      state_values: Tuple[Any, ...] = (False, True),
                      **kwargs
                      ) -> 'pygame_menu.widgets.ToggleSwitch':
        """
        Add a toggle switch to the Menu: It can switch between two states.

        If user changes the status of the callback, ``onchange`` is fired:

        .. code-block:: python

            onchange(current_state_value, **kwargs)

        kwargs (Optional)
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``font_background_color``     *(tuple, list, None)* - Widget font background color
            - ``font_color``                *(tuple, list)* - Widget font color
            - ``font_name``                 *(str, Path)* - Widget font path
            - ``font_size``                 *(int)* - Font size of the widget
            - ``infinite``                  *(bool)* - The state can rotate. ``False`` by default
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: *(top, right, bottom, left)*
            - ``readonly_color``            *(tuple, list)* - Color of the widget if readonly mode
            - ``readonly_selected_color``   *(tuple, list)* - Color of the widget if readonly mode and is selected
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect
            - ``shadow``                    *(bool)* - Text shadow is enabled or disabled
            - ``shadow_color``              *(tuple, list)* - Text shadow color
            - ``shadow_position``           *(str)* - Text shadow position, see locals for position
            - ``shadow_offset``             *(int, float)* - Text shadow offset
            - ``slider_color``              *(tuple, list)* - Color of the slider
            - ``slider_thickness``          *(int)* - Slider thickness (px)
            - ``state_color``               *(tuple)* - 2-item color tuple for each state
            - ``state_text_font_size``      *(str, None)* - Font size of the state text. If ``None`` uses the widget font size
            - ``state_text_font_color``     *(tuple)* - 2-item color tuple for each font state text color
            - ``switch_border_color``       *(tuple, list)* - Switch border color
            - ``switch_border_width``       *(int)* - Switch border width
            - ``switch_height``             *(int, float)* - Height factor respect to the title font size height
            - ``switch_margin``             *(tuple, list)* - *(x, y)* margin respect to the title of the widget. X is in px, Y is relative to the height of the title
            - ``width``                     *(int, float)* - Width of the switch box (px)

        .. note::

            This method only handles two states. If you need more states (for example 3, or 4),
            prefer using :py:class:`pygame_menu.widgets.ToggleSwitch` and add it as a generic
            widget.

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        .. warning::

            Be careful with kwargs collision. Consider that all optional documented
            kwargs keys are removed from the object.

        :param title: Title of the toggle switch
        :param default: Default state index of the switch; it can be ``0 (False)`` or ``1 (True)``
        :param onchange: Callback executed when when changing the STATE
        :param toggleswitch_id: Widget ID
        :param state_text: Text of each state
        :param state_values: Value of each state of the switch
        :return: :py:class:`pygame_menu.widgets.ToggleSwitch`
        """
        if isinstance(default, (int, bool)):
            assert 0 <= default <= 1, 'default value can be 0 or 1'
        else:
            raise ValueError('invalid value type, default can be 0, False, 1, or True')

        # Filter widget attributes to avoid passing them to the callbacks
        attributes = self._filter_widget_attributes(kwargs)

        infinite = kwargs.pop('infinite', False)
        slider_color = kwargs.pop('slider_color', (255, 255, 255))
        slider_thickness = kwargs.pop('slider_thickness', 20)
        state_color = kwargs.pop('state_color', ((178, 178, 178), (117, 185, 54)))
        state_text_font_color = kwargs.pop('state_text_font_color', ((255, 255, 255), (255, 255, 255)))
        state_text_font_size = kwargs.pop('state_text_font_size', None)
        switch_border_color = kwargs.pop('switch_border_color', (40, 40, 40))
        switch_border_width = kwargs.pop('switch_border_width', 1)
        switch_height = kwargs.pop('switch_height', 1.25)
        switch_margin = kwargs.pop('switch_margin', (25, 0))
        width = kwargs.pop('width', 150)

        widget = pygame_menu.widgets.ToggleSwitch(
            default_state=default,
            infinite=infinite,
            onchange=onchange,
            slider_color=slider_color,
            slider_thickness=slider_thickness,
            state_color=state_color,
            state_text=state_text,
            state_text_font_color=state_text_font_color,
            state_text_font_size=state_text_font_size,
            state_values=state_values,
            switch_border_color=switch_border_color,
            switch_border_width=switch_border_width,
            switch_height=switch_height,
            switch_margin=switch_margin,
            title=title,
            state_width=int(width),
            toggleswitch_id=toggleswitch_id,
            **kwargs
        )
        self._configure_widget(widget=widget, **attributes)
        widget.set_default_value(default)
        self._append_widget(widget)

        return widget

    def text_input(self,
                   title: Any,
                   default: Union[str, int, float] = '',
                   copy_paste_enable: bool = True,
                   cursor_selection_enable: bool = True,
                   input_type: TextInputModeType = _locals.INPUT_TEXT,
                   input_underline: str = '',
                   input_underline_len: int = 0,
                   maxchar: int = 0,
                   maxwidth: int = 0,
                   onchange: CallbackType = None,
                   onreturn: CallbackType = None,
                   onselect: Optional[Callable[[bool, 'pygame_menu.widgets.Widget', 'pygame_menu.Menu'], Any]] = None,
                   password: bool = False,
                   tab_size: int = 4,
                   textinput_id: str = '',
                   valid_chars: Optional[List[str]] = None,
                   **kwargs
                   ) -> 'pygame_menu.widgets.TextInput':
        """
        Add a text input to the Menu: free text area and two functions
        that execute when changing the text and pressing return button
        on the element.

        The callbacks receive the current value and all unknown keyword
        arguments, where ``current_text=widget.get_value``:

        .. code-block:: python

            onchange(current_text, **kwargs)
            onreturn(current_text, **kwargs)
            onselect(selected, widget, menu)

        kwargs (Optional)
            - ``align``                     *(str)* - Widget `alignment <https://pygame-menu.readthedocs.io/en/latest/_source/create_menu.html#widgets-alignment>`_
            - ``background_color``          *(tuple, list,* :py:class:`pygame_menu.baseimage.BaseImage`) - Color of the background
            - ``background_inflate``        *(tuple, list)* - Inflate background in *(x, y)* in px
            - ``border_color``              *(tuple, list)* - Widget border color
            - ``border_inflate``            *(tuple, list)* - Widget border inflate in *(x, y)* in px
            - ``border_width``              *(int)* - Border width in px. If ``0`` disables the border
            - ``font_background_color``     *(tuple, list, None)* - Widget font background color
            - ``font_color``                *(tuple, list)* - Widget font color
            - ``font_name``                 *(str, Path)* - Widget font path
            - ``font_size``                 *(int)* - Font size of the widget
            - ``input_underline_vmargin``   *(int)* - Vertical margin of underline (px)
            - ``margin``                    *(tuple, list)* - Widget *(left, bottom)* margin in px
            - ``padding``                   *(int, float, tuple, list)* - Widget padding according to CSS rules. General shape: *(top, right, bottom, left)*
            - ``readonly_color``            *(tuple, list)* - Color of the widget if readonly mode
            - ``readonly_selected_color``   *(tuple, list)* - Color of the widget if readonly mode and is selected
            - ``selection_color``           *(tuple, list)* - Color of the selected widget; only affects the font color
            - ``selection_effect``          (:py:class:`pygame_menu.widgets.core.Selection`) - Widget selection effect
            - ``shadow``                    *(bool)* - Text shadow is enabled or disabled
            - ``shadow_color``              *(tuple, list)* - Text shadow color
            - ``shadow_position``           *(str)* - Text shadow position, see locals for position
            - ``shadow_offset``             *(int, float)* - Text shadow offset

        .. note::

            All theme-related optional kwargs use the default Menu theme if not defined.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        .. warning::

            Be careful with kwargs collision. Consider that all optional documented
            kwargs keys are removed from the object.

        :param title: Title of the text input
        :param default: Default value to display
        :param copy_paste_enable: Enable text copy, paste and cut
        :param cursor_selection_enable: Enable text selection on input
        :param input_type: Data type of the input
        :param input_underline: Underline character
        :param input_underline_len: Total of characters to be drawn under the input. If ``0`` this number is computed automatically to fit the font
        :param maxchar: Maximum length of string, if 0 there's no limit
        :param maxwidth: Maximum size of the text widget (in number of chars), if ``0`` there's no limit
        :param onchange: Callback executed when changing the text input
        :param onreturn: Callback executed when pressing return on the text input
        :param onselect: Callback executed when selecting the widget
        :param password: Text input is a password
        :param tab_size: Size of tab key
        :param textinput_id: ID of the text input
        :param valid_chars: List of authorized chars. ``None`` if all chars are valid
        :param kwargs: Optional keyword arguments
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.TextInput`
        """
        assert isinstance(default, (str, int, float))

        # Filter widget attributes to avoid passing them to the callbacks
        attributes = self._filter_widget_attributes(kwargs)
        input_underline_vmargin = kwargs.pop('input_underline_vmargin', 0)

        # If password is active no default value should exist
        if password and default != '':
            raise ValueError('default value must be empty if the input is a password')

        widget = pygame_menu.widgets.TextInput(
            copy_paste_enable=copy_paste_enable,
            cursor_color=self._theme.cursor_color,
            cursor_selection_color=self._theme.cursor_selection_color,
            cursor_selection_enable=cursor_selection_enable,
            cursor_switch_ms=self._theme.cursor_switch_ms,
            input_type=input_type,
            input_underline=input_underline,
            input_underline_len=input_underline_len,
            input_underline_vmargin=input_underline_vmargin,
            maxchar=maxchar,
            maxwidth=maxwidth,
            onchange=onchange,
            onreturn=onreturn,
            onselect=onselect,
            password=password,
            tab_size=tab_size,
            textinput_id=textinput_id,
            title=title,
            valid_chars=valid_chars,
            **kwargs
        )

        self._configure_widget(widget=widget, **attributes)
        widget.set_default_value(default)
        self._append_widget(widget)

        return widget

    def vertical_margin(self,
                        margin: NumberType,
                        margin_id: str = ''
                        ) -> 'pygame_menu.widgets.VMargin':
        """
        Adds a vertical margin to the Menu.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        :param margin: Vertical margin in px
        :param margin_id: ID of the margin
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.VMargin`
        """
        assert isinstance(margin, (int, float))
        assert margin > 0, \
            'zero margin is not valid, prefer adding a NoneWidget menu.add.none_widget()'

        attributes = self._filter_widget_attributes({'margin': (0, margin)})
        widget = pygame_menu.widgets.VMargin(widget_id=margin_id)
        self._configure_widget(widget=widget, **attributes)
        self._append_widget(widget)

        return widget

    def none_widget(self, widget_id: str = '') -> 'pygame_menu.widgets.NoneWidget':
        """
        Add none widget to the Menu.

        .. note::

            This widget is useful to fill column/rows layout without
            compromising any visuals. Also it can be used to store information
            or even to add a ``draw_callback`` function to it for being called
            on each Menu draw.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        :param widget_id: Widget ID
        :return: Widget object
        :rtype: :py:class:`pygame_menu.widgets.NoneWidget`
        """
        attributes = self._filter_widget_attributes({})

        widget = pygame_menu.widgets.NoneWidget(widget_id=widget_id)
        self._configure_widget(widget=widget, **attributes)
        self._append_widget(widget)

        return widget

    def generic_widget(self, widget: 'pygame_menu.widgets.Widget', configure_defaults: bool = False
                       ) -> 'pygame_menu.widgets.Widget':
        """
        Add generic widget to the Menu.

        .. note::

            The widget should be fully configured by the user: font, padding, etc.

        .. note::

            This is applied only to the base Menu (not the currently displayed,
            stored in ``_current`` pointer); for such behaviour apply
            to :py:meth:`pygame_menu.menu.Menu.get_current` object.

        .. warning::

            Unintended behaviours may happen while using this method, use only with caution.
            Specially while creating nested submenus with buttons.

        :param widget: Widget to be added
        :param configure_defaults: Apply defaults widget configuration (for example, theme)
        :return: The added widget
        """
        assert isinstance(widget, pygame_menu.widgets.Widget)
        if widget.get_menu() is not None:
            raise ValueError('widget to be added is already appended to another Menu')

        # Raise warning if adding button with Menu
        if isinstance(widget, pygame_menu.widgets.Button) and widget.to_menu:
            msg = 'prefer adding nested submenus using add_button method instead, unintended behaviours may occur'
            warnings.warn(msg)

        # Configure widget
        if configure_defaults:
            self._configure_widget(widget, **self._filter_widget_attributes({}))

        widget.set_menu(self._menu)
        self._menu._check_id_duplicated(widget.get_id())

        widget.set_controls(self._menu._joystick, self._menu._mouse, self._menu._touchscreen)
        self._append_widget(widget)
        return widget
