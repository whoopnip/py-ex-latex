from typing import Sequence, List
from pyexlatex.models.lists.item import ListItem
from pyexlatex.models.lists.base import VerticalFillMixin
from pyexlatex.models.format.text.color import TextColor
from pyexlatex.presentation.beamer.overlay import Overlay
from pyexlatex.presentation.beamer.overlay import UntilEnd
from pyexlatex.presentation.beamer.overlay import NextWithIncrement, NextWithoutIncrement
from pyexlatex.models.containeritem import ContainerItem
from pyexlatex.models.item import ItemBase


class DimAndRevealListItem(ListItem):

    def __init__(self, contents, dim: bool = True, opacity: float = 0.3, **kwargs):
        self.dim = dim
        dim_ov = Overlay([UntilEnd(NextWithoutIncrement(1))])
        next_ov = Overlay([UntilEnd(NextWithIncrement())])

        if dim:
            contents = TextColor(contents, 'black', opacity=opacity, overlay=dim_ov)

        super().__init__(contents, overlay=next_ov, **kwargs)

    def convert_to_regular_item(self):
        if self.dim:
            contents = self.contents.content  # get from inside TextColor
        else:
            contents = self.contents
        item = ListItem(contents)
        self.__dict__.update(item.__dict__)
        self.__class__ = ListItem
        del self.is_DimAndRevealListItem
        del self.dim


class DimAndRevealListItems(VerticalFillMixin, ContainerItem, ItemBase):
    name = '<dim and reveal container, should not enter latex output>'

    def __init__(self, contents: Sequence, dim_last_item: bool = False, opacity: float = 0.3,
                 vertical_fill: bool = False, dim_earlier_items: bool = True, **item_kwargs):
        self.orig_contents = contents
        self.dim_last_item = dim_last_item
        self.dim_earlier_items = dim_earlier_items
        self.opacity = opacity
        self.item_kwargs = item_kwargs
        self.vertical_fill = vertical_fill
        self.add_data_from_content(contents)
        self.contents = self._get_contents()

    def _get_contents(self) -> List[DimAndRevealListItem]:
        output = [
            DimAndRevealListItem(
                item,
                opacity=self.opacity,
                dim=self.dim_earlier_items,
                **self.item_kwargs
            ) for item in self.orig_contents
        ]
        if not self.dim_last_item:
            output[-1] = DimAndRevealListItem(
                self.orig_contents[-1], dim=False, opacity=self.opacity, **self.item_kwargs
            )
        output = self.vertically_space_content(output)

        return output

    def __str__(self) -> str:
        from pyexlatex.logic.builder import _build
        if isinstance(self.contents, str):
            return self.contents
        return _build(self.contents)


def eliminate_dim_reveal(content):
    """
    Eliminates dim/reveal from nested content. Modifies in place by using regular list items
    """
    if hasattr(content, 'content'):
        eliminate_dim_reveal(content.content)
    if hasattr(content, 'contents'):
        eliminate_dim_reveal(content.contents)
    if hasattr(content, 'is_DimAndRevealListItem') and content.is_DimAndRevealListItem:
        content.convert_to_regular_item()
    if isinstance(content, (list, tuple)):
        [eliminate_dim_reveal(c) for c in content]