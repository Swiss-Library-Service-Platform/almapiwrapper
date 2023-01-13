"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional
import logging
from ..record import XmlData, Record, check_error
from ..inventory import IzBib, NzBib
from ..users import User


class RecSet(Record):
    """Class representing a set of records

    :ivar set_id: initial value: ID of the set
    :ivar zone: initial value: zone of the fee
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    """
    def __init__(self,
                 set_id: str,
                 zone: str,
                 env: Literal['P', 'S'] = 'P') -> None:
        """Constructor of `RecSet`
        """
        super().__init__(zone, env)
        self.area = 'Conf'
        self.format = 'xml'
        self.set_id = set_id
        self._members = None

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

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.set_id}', '{self.zone}', '{self.env}')"

    @check_error
    def get_members_number(self) -> int:
        """get_members_number(self) -> int
        Return the number of members

        :return: int with the number of records

        .. note::
            If the record encountered an error, this
            method will be skipped."""
        return int(self.data.find('.//number_of_members').text)

    @check_error
    def get_set_type(self) -> str:
        """get_set_type(self) -> str
        Return the type of the set

        :return: str indicating the type of the set

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        return self.data.find('.//type').text

    @check_error
    def get_content_type(self) -> str:
        """get_content_type(self) -> str
        Return the type of the set

        :return: str indicating the type of the set

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        return self.data.find('.//content').text

    @check_error
    def delete(self) -> None:
        """Delete a set

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        r = self._api_call('delete',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: set deleted')
            return
        else:
            print(r.text)
            self._handle_error(r, f'unable to delete the set')

    @check_error
    def get_members(self) -> list[Record]:
        """get_members(self) -> list[Record]
        Return a list with all the records of the set

        :return: list of records depending on the type of the set

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        # Prevent to fetch data twice, if already available
        if self._members is not None:
            return self._members

        self._members = []
        while len(self._members) < self.get_members_number():
            r = self._api_call('get',
                               f'{self.api_base_url}/conf/sets/{self.set_id}/members',
                               params={'limit': '100', 'offset': str(len(self._members))},
                               headers=self._get_headers())
            if r.ok is False:
                self._handle_error(r, f'{repr(self)}: unable to fetch set members')
                return self._members
            else:
                rec_ids = [rec_id.text for rec_id in XmlData(r.content).content.findall('.//member/id')]

                # Build members -> IZ mms_id
                if self.get_content_type() in ['BIB_MMS', 'IEP'] and self.zone != 'NZ':
                    self._members += [IzBib(rec_id, self.zone, self.env) for rec_id in rec_ids]

                # Build members -> IZ mms_id
                elif self.get_content_type() in ['BIB_MMS'] and self.zone == 'NZ':
                    self._members += [NzBib(rec_id, self.env) for rec_id in rec_ids]

                # Build members -> users
                elif self.get_content_type() == 'USER':
                    self._members += [User(rec_id, self.zone, self.env) for rec_id in rec_ids]

                # Type of content not integrated
                else:
                    self._members += rec_ids
                    logging.warning(f'{repr(self)}: "{self.get_content_type()}" not integrated, only id are returned.')

                logging.info(f'{repr(self)}: {len(self._members)} / {self.get_members_number()} members fetched')

        return self._members
