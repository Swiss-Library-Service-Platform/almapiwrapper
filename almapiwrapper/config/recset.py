"""This module allow to create and manage sets in Alma"""
from typing import Literal
import logging
from ..record import XmlData


class RecSet:
    """Class representing a set of records
    :ivar set_id: ID of the set
    """
    def __init__(self, set_id: str,
                 zone: str,
                 env: Literal['P', 'S'] = 'P') -> None:
        """Constructor of `RecSet`

        """
        self.area = 'Config'
        self.format = 'xml'
        self.set_id = set_id

    def _fetch_data(self):
        """

        :return:
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: set data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch bib data')
