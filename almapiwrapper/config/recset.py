"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional
import logging
from ..record import XmlData, Record


class RecSet(Record):
    """Class representing a set of records
    :ivar set_id: initial value: ID of the set
    :ivar zone: initial value: zone of the fee
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    """
    def __init__(self, set_id: str,
                 zone: str,
                 env: Literal['P', 'S'] = 'P') -> None:
        """Constructor of `RecSet`
        """
        super().__init__(zone, env)
        self.area = 'Config'
        self.format = 'xml'
        self.set_id = set_id

    def _fetch_data(self) -> Optional[XmlData]:
        """This method fetch the data describing the set.

        :return: :class:`almapiwrapper.record.XmlData`
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: set data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch set data')

    def get_members(self):
        pass
