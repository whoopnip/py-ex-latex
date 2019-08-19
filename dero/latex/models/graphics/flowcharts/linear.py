from typing import Sequence, Union, Optional, List
from copy import deepcopy
from dero.latex.models.item import ItemBase
from dero.latex.models.containeritem import ContainerItem
from dero.latex.models.graphics.tikz.node.node import Node
from dero.latex.models.graphics.arrow import Arrow
from dero.latex.models.graphics.tikz.node.position.directions import Right, Below, DirectionBase


class LinearFlowchart(ContainerItem, ItemBase):

    def __init__(self, steps: Sequence[Union[Node, str]], horizontal: bool = True,
                 node_options: Optional[Sequence[str]] = None):
        self.steps = steps
        self.horizontal = horizontal
        self.node_options = node_options
        self.add_data_from_content(steps)
        self.nodes = self._get_nodes()
        self.contents = self._get_contents()

    def __str__(self) -> str:
        from dero.latex.logic.builder import _build
        return _build(self.contents)

    def _get_contents(self) -> List[Union[Node, Arrow]]:
        nodes = self.nodes
        contents = deepcopy(nodes)
        for i, node in enumerate(nodes):
            if i == 0:
                continue
            contents.append(Arrow(nodes[i - 1], nodes[i]))
        self.add_data_from_content(contents)
        return contents

    def _get_nodes(self) -> List[Node]:
        out_nodes = []
        for i, item in enumerate(self.steps):
            if hasattr(item, 'is_Node') and item.is_Node:
                item: Node
                if i == 0:
                    out_nodes.append(item)
                    continue
                # If beyond the first element, need to create a new node with the same info, but with
                # position relative to the last element
                new_node = Node(
                    contents=item.contents,
                    location=self.direction(of=out_nodes[i - 1]),
                    label=item.label,
                    options=item.options,
                    overlay=item.overlay
                )
                new_node.add_data_from_content(item)
                out_nodes.append(
                    new_node
                )
            else:
                # Treat as str passed, need to create node with str and node options
                out_nodes.append(
                    Node(
                        contents=item,
                        location=self.direction(of=out_nodes[i - 1]) if i > 0 else None,
                        options=self.node_options
                    )
                )
        return out_nodes

    @property
    def direction(self) -> type:
        if self.horizontal:
            return Right
        else:
            return Below