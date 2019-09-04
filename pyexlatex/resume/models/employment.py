from pyexlatex.models.item import Item
from pyexlatex.models.containeritem import ContainerItem
from pyexlatex.models.lists.item import ListItem


class Employment(ContainerItem, Item):
    name = 'employment'

    def __init__(self, contents, company_name: str, employed_dates: str, job_title: str, location: str):
        self.company_name = company_name
        self.employed_dates = employed_dates
        self.job_title = job_title
        self.location = location

        self.add_data_from_content([
            contents,
            company_name,
            employed_dates,
            job_title,
            location
        ])

        if not isinstance(contents, (list, tuple)):
            contents = [contents]

        contents = [ListItem(content) for content in contents]

        super().__init__(
            self.name,
            contents,
            env_modifiers=self._modifier_str
        )

    @property
    def _modifier_str(self) -> str:
        output = ''
        for item in [self.company_name, self.employed_dates, self.job_title, self.location]:
            output += self._wrap_with_braces(item)
        return output