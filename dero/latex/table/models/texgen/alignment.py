import re

from dero.latex.models.mixins import ReprMixin

class ColumnAlignment(ReprMixin):
    repr_cols = ['align']

    def __init__(self, align_str: str):
        ColumnAlignment._validate_align_str(align_str)
        self.align = align_str

    def __str__(self):
        return self.align

    def __add__(self, other):
        return self.align + other.align

    def __radd__(self, other):
        return other.align + self.align

    @staticmethod
    def _validate_align_str(align_str):
        basic_pattern = re.compile(r'[lcr]')
        length_pattern = re.compile(r'[LCR]\{[\d\w\s]+\}')

        basic_match = basic_pattern.fullmatch(align_str)
        length_match = length_pattern.fullmatch(align_str)

        if not (basic_match or length_match):
            raise ValueError(f'expected alignment of l, c, r, L{{size}}, C{{size}}, or R{{size}}. Got {align_str}')


class ColumnsAlignment(ReprMixin):
    repr_cols = ['aligns']

    def __init__(self, aligns: [ColumnAlignment]= None, num_columns: int=None):

        if aligns is None and num_columns is None:
            raise ValueError('must pass aligns or num columns')

        # default align is first column left, rest centered
        if aligns is None and num_columns is not None:
            self.aligns = [ColumnAlignment('l')] + [ColumnAlignment('c')] * (num_columns - 1)

        # if we don't know how many columns, must assume passed number of aligns is correct
        if num_columns is None:
            self.aligns = aligns

        # number of alignments matches number of columns. no extra processing needed
        if len(aligns) == num_columns:
            self.aligns = aligns

        # if one alignment is passed with many columns, use that align with all columns
        if len(aligns) == 1:
            self.aligns = [aligns[0]] * num_columns
        else:
            raise ValueError(f'got {len(aligns)} alignments for {num_columns} columns. unclear how to apply')

    def __str__(self):
        return sum(self.aligns)

    def __iter__(self):
        for align in self.aligns:
            yield align


    @classmethod
    def from_alignment_str(cls, align_str: str):
        align_str_list = _full_align_str_to_align_str_list(align_str)
        aligns = [ColumnAlignment(align) for align in align_str_list]
        return cls(aligns)


def _full_align_str_to_align_str_list(align_str: str):
    split_letters = ['l', 'c', 'r', 'L', 'C', 'R']
    out_list = []
    collected_letters = ''
    split = True

    for letter in align_str:
        # beginning inside of length str. don't split while inside
        if letter == '{':
            split = False
        # end of inside of length str. turn splitting back on
        if letter == '}':
            split = True
        # if splitting, output what we've got so far and start a new item
        if split and letter in split_letters:
            out_list.append(collected_letters)
            collected_letters = ''
        # if not splitting, add to current item
        collected_letters += letter

    # Clean up list from loop. Remove first (always blank), and add last
    out_list.append(collected_letters)
    out_list = out_list[1:]

    return out_list