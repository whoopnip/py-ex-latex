from typing import Optional
from dero.latex.models.item import Item
from dero.mixins.repr import ReprMixin
from dero.latex.logic.format.contents import format_contents as fmt
from dero.latex.logic.builder import _build
from dero.latex.models.documentitem import DocumentItem
from dero.latex.models.label import Label
from dero.latex.logic.extract.filepaths import get_filepaths_from_items
from dero.latex.logic.extract.binaries import get_binaries_from_items


class TextAreaBase(DocumentItem, Item, ReprMixin):
    name = 'textarea'
    repr_cols = ['title', 'contents']
    next_level_down_class = None  # once subclassed, will be overridden with the next level down text area class

    def __init__(self, name, contents, label: Optional[str] = None, **kwargs):
        self.filepaths = get_filepaths_from_items(contents)
        self.binaries = get_binaries_from_items(contents)
        contents = self.format_contents(contents)
        if label is not None:
            label = Label(label)
            contents = _build([contents, label])
        super().__init__(name, contents, **kwargs)

    def format_contents(self, contents):
        if isinstance(contents, (list, tuple)):
            return _build([self.format_contents(c) for c in contents])
        elif isinstance(contents, dict):
            subcontents = []
            for title, content in contents.items():
                subcontents.append(
                    str(self.next_level_down_class(content, title=title))
                )
            return _build(subcontents)
        else:
            # Not an iterable
            return self._format_content(contents)


    def _format_content(self, content):
        if isinstance(content, str):
            return fmt(content)
        else:
            # Class is responsible for formatting. This may be a latex class or some
            # other harmless conversion such as int. It may also be an issue if the __str__
            # method of the class is not valid latex
            return str(content)




class SectionBase(TextAreaBase):
    name = 'section'
    repr_cols = ['title', 'short_title', 'contents']

    def __init__(self, contents, title: str, short_title: Optional[str] = None, **kwargs):
        self.title = title
        self.short_title = short_title
        super().__init__(self.name, contents, env_modifiers=self.env_modifiers, **kwargs)

    @property
    def env_modifiers(self):
        modifier_str = ''
        if self.short_title is not None:
            modifier_str += f'[{fmt(self.short_title)}]'

        modifier_str += f'{{{fmt(self.title)}}}'

        return modifier_str


class ParagraphBase(TextAreaBase):
    name = 'paragraph'
    repr_cols = ['title', 'contents']

    def __init__(self, contents, title: Optional[str] = None, **kwargs):
        self.title = title
        super().__init__(self.name, contents, env_modifiers=self.env_modifiers, **kwargs)

    @property
    def env_modifiers(self):
        if self.title is not None:
            return f'{{{self.title}}}'

        return None