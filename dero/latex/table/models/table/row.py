from typing import Union, Iterable

from dero.latex.models.mixins import ReprMixin
from dero.latex.table.models.data.dataitem import DataItem
from dero.latex.table.models.labels.collection import LabelCollection
from dero.latex.table.models.labels.label import Label
from dero.latex.table.models.mixins.addvalues.row import RowAddMixin
from dero.latex.texparser.clean import _remove_backslashes
from dero.latex.table.models.spacing.cell import CellSpacer


class Row(ReprMixin, RowAddMixin):
    repr_cols = ['values']

    def __init__(self, values: Union[Iterable[DataItem], LabelCollection]):

        # Don't allow nested rows. If the only values passed to a Row are a Row, then use the values of that
        # row rather than the row itself as values
        if isinstance(values, Row):
            self.values = values.values
        else:
            self.values = values

    def __len__(self):
        return len(self.values)

    def __str__(self):
        str_list = []
        for value in self.values:
            # Handle other forms of blanks
            if isinstance(value, Iterable) and len(value) == 1 and str(value[0]).strip() == '':
                str_list.append(' ')
            # The usual case, just join string representation of items
            else:
                str_list.append(str(value))

        return ' & '.join(str_list)

    def __iter__(self):
        for value in self.values:
            yield value

    def pad(self, length: int, direction='right'):
        """
        Expand row out to the right or left with blanks, until it is length passed
        :param length:
        :return:
        """
        num_values_to_add = length - len(self)
        direction = direction.lower().strip()

        if num_values_to_add == 0:
            return

        if direction == 'right':
            self.values += [CellSpacer()] * num_values_to_add
        elif direction == 'left':
            self.values = [CellSpacer()] * num_values_to_add + self.values
        else:
            raise ValueError(f'must pass left or right for direction. got {direction}')

    @classmethod
    def from_latex_row_str(cls, latex_row_str):
        latex_row_str = _remove_backslashes(latex_row_str)
        str_values = latex_row_str.split(' & ')
        values = [DataItem(value) for value in str_values]
        return cls(values)

    @property
    def is_spacer(self):
        booleans = []
        for item in self.values:
            if isinstance(item, CellSpacer):
                result = True
            elif isinstance(item, (Label, DataItem)):
                result = str(item.value).strip() == ''
            elif isinstance(item, str):
                result = item.strip() == ''
            else:
                raise ValueError(f'cannot check whether {item} of type {type(item)} is a spacer or not')
            booleans.append(result)
        return all(booleans)