from typing import Union, AnyStr, List

import numpy as np
import pandas as pd

from dero.latex.models.mixins import ReprMixin
from dero.latex.table.logic.panels.combine import (
    common_column_labels,
    common_row_labels,
    remove_label_collections_from_grid
)
from dero.latex.table.logic.panels.letters import panel_string
from dero.latex.table.logic.panels.topleft import _set_top_left_corner_labels
from dero.latex.table.models.labels.table import LabelTable, LabelCollection
from dero.latex.table.models.panels.panel import Panel
from dero.latex.table.models.panels.panel import PanelGrid, GridShape
from dero.latex.table.models.spacing.columntable import ColumnPadTable
from dero.latex.table.models.spacing.rowtable import RowPadTable
from dero.latex.table.models.table.section import TableSection


class PanelCollection(ReprMixin):
    repr_cols = ['name', 'panels']

    def __init__(self, panels: [Panel], label_consolidation: str='object', enforce_label_order=True,
                 top_left_corner_labels: Union[LabelTable, LabelCollection, List[AnyStr], AnyStr]=None,
                 pad_rows: int=1, pad_columns: int=1, name: str=None):
        """

        :param panels: list of Panels, which represent a full set of rows of the table. for multiple
                        sections in one set of rows, create DataTables for each section and pass to Panels.
        :param label_consolidation: pass 'object' to compare object equality for label consolidation, 'str'
                                    for converting all labels to strings then comparing equality. Use 'object'
                                    for more control over consolidation.
        :param enforce_label_order: pass False to allow consolidating lower labels even if upper labels do not match.
                                    e.g. if labels on one table are [['Top1'], ['Bot1', 'Bot2']], then labels on the other
                                    table are [['Top2'], ['Bot1', 'Bot2']], consolidated labels when passing False will be
                                    ['Bot1', 'Bot2'], while when passing True, no labels will be consolidated. Under True,
                                    will start from the top label, then stop consolidating once it has a mismatch.
        :param top_left_corner_labels: additional labels to place in the top left corner. pass a single string
                                       or a list of strings for convenience. a list of strings will be create labels
                                       which span the gap horizontally and go downwards, one label per row. pass
                                       LabelCollection or LabelTable for more control.
        :param pad_rows: horizontal spacing to put between panels
        :param pad_columns: vertical spacing to put between TableSections
        :param name: name that will be used to construct caption in output
        """
        self.name = name
        self.panels = panels
        self.label_consolidation = label_consolidation.lower().strip() \
            if isinstance(label_consolidation, str) else label_consolidation
        self.enforce_label_order = enforce_label_order
        self.top_left_corner_labels = _set_top_left_corner_labels(top_left_corner_labels)
        self.pad_rows = pad_rows
        self.pad_columns = pad_columns

        self.consolidate_labels()
        self.pad_grid()

    def iterpanels(self):
        """
        First panel is headers. Then each original panel

        self.grid includes all panels as well as labels. Need to separate back out to
        get each panel
        :return:
        :rtype:
        """

        if self.has_column_labels:
            orig_panel_index = -2
        else:
            orig_panel_index = -1
        name_used = False

        for row in self.rows:
            if not row.is_spacer: # don't increment original panel index when going through inserted spacing
                orig_panel_index += 1
                name_used = False # need to reset to use name again
            if orig_panel_index < 0 or name_used or self.panels[orig_panel_index].name is None:
                # column labels panel, no matching name. Or no name for user supplied panel
                yield Panel(PanelGrid([row]))
            else: # user passed panel, may have matching name
                full_name = panel_string(orig_panel_index) + self.panels[orig_panel_index].name
                yield Panel(PanelGrid([row]), name=full_name)
                name_used = True # only allow name to be used once

    @property
    def rows(self):
        try:
            return self._rows
        except AttributeError:
            self._rows = self._create_panel_rows()

        return self._rows

    @property
    def num_columns(self) -> int:
        try:
            return self._num_columns
        except AttributeError:
            self._num_columns = max([row.num_columns for row in self.rows])

        return self._num_columns

    def _create_panel_rows(self):
        rows: [TableSection] = []

        for panel_row in self.grid:
            new_row = None
            for i, section in enumerate(panel_row):
                if i == 0:
                    new_row = section
                else:
                    new_row = new_row + section
            if new_row:
                rows.append(new_row)

        try:
            num_columns = self._num_columns
        except AttributeError:
            num_columns = max([row.num_columns for row in rows])

        # Now pad rows
        for row in rows:
            row.pad(num_columns, direction='right')

        return rows


    @property
    def grid(self):
        try:
            return self._grid
        except AttributeError:
            self._grid = np.concatenate([panel.panel_grid for panel in self.panels]).view(GridShape)

        return self._grid

    def consolidate_labels(self):

        if self.label_consolidation is None:
            return

        if self.label_consolidation == 'object':
            use_object_equality = True
        elif self.label_consolidation in ('string', 'str', True):
            use_object_equality = False
        else:
            raise ValueError(f'must pass object, string, or None to label consolidation. Got {self.label_consolidation}')

        column_labels: [LabelTable] = common_column_labels(
            self.grid,
            use_object_equality=use_object_equality,
            enforce_label_order=self.enforce_label_order
        )

        row_labels: [LabelTable] = common_row_labels(
            self.grid,
            use_object_equality=use_object_equality,
            enforce_label_order=self.enforce_label_order
        )

        self._add_column_labels(column_labels)

        # After adding column labels, there is an additional row at the top of the grid
        # Therefore we will need one additional LabelTable for the first row, which is the row of column labels
        # If top_left_corner_labels was passed on object creation, use that as LabelTable. Otherwise use a blank one
        if self.has_column_labels:
            all_row_labels = [self.top_left_corner_labels] + row_labels
        else:
            all_row_labels = row_labels
        self._add_row_labels(all_row_labels)

        # Remove from the original tables the labels that were just consolidated
        remove_label_collections_from_grid(
            self.grid,
            column_labels=column_labels,
            row_labels=row_labels,
            use_object_equality=use_object_equality
        )

    def pad_grid(self):
        row_pad = RowPadTable()

        grid_rows: [GridShape] = []
        for n_row, grid_row in enumerate(self.grid):
            # Add first elem
            new_row = np.array([grid_row[0]]).view(GridShape).reshape(1,1)
            # Add following elems
            for n_elem, elem in enumerate(grid_row[1:]):
                # Add pads between following elems
                if self.pad_columns and not (n_elem == 0 and self.has_row_labels): # only skip first if there are row labels
                    new_row = np.append(new_row, np.array([ColumnPadTable(self.pad_columns)])).view(GridShape)
                new_row = np.append(new_row, elem).view(GridShape)
                new_row = new_row.reshape((1, new_row.shape[0])) # reorganize into row
            grid_rows.append(new_row)
            # add row padding on every loop except last
            if n_row != self.grid.shape[0] - 1:
                # no need to add padding after column labels
                if n_row == 0 and self.has_column_labels:
                    continue
                for i in range(self.pad_rows):
                    grid_rows.append(
                        np.array([row_pad]).view(GridShape).reshape(1,1)
                    )

        # Before combining rows, must have same number of elements. Pad right with empty label tables
        num_grid_columns = max(row.shape[1] for row in grid_rows) # find max number of columns
        out_grid_rows = []
        for row in grid_rows:
            pad_number = num_grid_columns - row.shape[1]
            assert pad_number >= 0
            new_row = np.append(row, np.array([row_pad] * pad_number)).view(GridShape)
            new_row = new_row.reshape((1, new_row.shape[0]))  # reorganize into row
            out_grid_rows.append(new_row)

        new_grid = np.concatenate(out_grid_rows).view(GridShape)
        self._grid = new_grid
        self._rows = self._create_panel_rows() # need to recreate rows with new grid


    def _add_column_labels(self, column_labels: [LabelTable]):
        assert len(column_labels) == self.grid.shape[1]

        if all(table.is_empty for table in column_labels):
            # if no consolidated labels, no need to add
            self.has_column_labels = False
            return

        self.has_column_labels = True

        # Form PanelGrid from labels
        column_label_grid = PanelGrid(column_labels, shape=(1,len(column_labels)))

        # Combine label PanelGrid and existing PanelGrid
        self._grid = np.concatenate([column_label_grid, self._grid]).view(GridShape)

    def _add_row_labels(self, row_labels: [LabelTable]):
        assert len(row_labels) == self.grid.shape[0]

        if all(table.is_empty for table in row_labels):
            # if no consolidated labels, no need to add
            self.has_row_labels = False
            return

        self.has_row_labels = True

        # Form PanelGrid from labels
        row_label_grid = PanelGrid(row_labels, shape=(len(row_labels), 1))

        # Combine label PanelGrid and existing PanelGrid
        self._grid = np.concatenate([row_label_grid, self._grid], axis=1).view(GridShape)

    @classmethod
    def from_list_of_lists_of_dfs(cls, df_list_of_lists: [[pd.DataFrame]], *args,
                                  panel_args=tuple(), panel_kwargs={}, **kwargs):
        """
        To create a single panel table, pass a single list within
        a list of DataFrames, e.g. [[df1, df2]] then shape will specify how the DataFrames will
        be organized in the Panel. If you pass two lists within the outer list, then shape will
        apply to each Panel. So [[df1, df2], [df3, df4]] with shape=(1,2) create a two Panel table
        with two tables placed within each panel going horizontally, so that the overall shape is (2,2).

        Note: convenience method for if not much control over table is needed.
        To apply different options to each panel, construct them individually using
        Panel.from_df_list

        :param df_list_of_lists:
        :param args: args to pass to PanelCollection constructor
        :param panel_args: Panel.from_df_list args. Same args will be passed to all panels
        :param panel_kwargs: Panel.from_df_list kwargs. Same kwargs will be passed to all panels
        :param kwargs: kwargs to pass to PanelCollection constructor

        :return: PanelCollection
        """
        panels = []
        for df_list in df_list_of_lists:
            panels.append(
                Panel.from_df_list(df_list, *panel_args, **panel_kwargs)
            )

        label_consolidation = kwargs.pop('label_consolidation', 'string')

        return cls(
            panels,
            *args,
            label_consolidation=label_consolidation,
            **kwargs
        )

    def to_tex(self, mid_rule=True):
        from dero.latex.table.logic.table.build import build_tabular_content_from_panel_collection
        return build_tabular_content_from_panel_collection(self, mid_rule=mid_rule)

