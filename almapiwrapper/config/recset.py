"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional, Union
import logging
from ..record import XmlData, Record, check_error
from ..inventory import IzBib, NzBib
from ..users import User
from lxml import etree


class RecSet(Record):
    """Class representing a set of records

    To get a set it is possible to provide either the set id or the name of the set.

    :ivar set_id: initial value: ID of the set
    :ivar zone: initial value: zone of the fee
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar name: initial value: name of the set
    """
    def __init__(self,
                 set_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 name: Optional[str] = None,
                 data: Optional[XmlData] = None) -> None:
        """Constructor of `RecSet`
        """
        super().__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'xml'
        self._name = name
        self.set_id = set_id
        self._members = None

    def _fetch_data(self) -> Optional[XmlData]:
        """This method fetch the data describing the set.

        It is possible to fetch the data of a set by providing the set_id or the name of the set.

        :return: :class:`almapiwrapper.record.XmlData`
        """
        # set_id is not provided. We try to fetch it from the name.
        if self.set_id is None and self._name is not None:
            r = self._api_call('get',
                               f'{self.api_base_url}/conf/sets',
                               params={'q': f'name~{self._name}'},
                               headers=self._get_headers())
            if r.ok is True and XmlData(r.content).content.find('.//set') is not None:
                logging.info(f'{repr(self)}: set data available')
                set_data = XmlData(r.content).content.find('.//set')

                # We store the set_id for fetching the complete data
                self.set_id = set_data.find('.//id').text

            else:
                logging.error(f'{repr(self)}: unable to fetch set data')
                self.error = True
                return None

        # set_id is provided. We fetch the data.
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: set data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch set data')

    @property
    def name(self) -> str:
        """Property returning the name of the set.

        :return: str containing set name
        """
        if self._name is None:
            name = self.data.find('.//name')
            if name is not None:
                self._name = name.text

        return self._name

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        if self.set_id is not None:
            return f"{self.__class__.__name__}('{self.set_id}', '{self.zone}', '{self.env}')"
        else:
            return f"{self.__class__.__name__}(name='{self.name}', zone='{self.zone}', env='{self.env}')"

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
        """delete(self) -> None
        Delete a set

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

class NewRecSet(RecSet):
    """Class representing a set of records

    To create a new set, it is possible to provide directly the XML data or
    to give all the required parameters.

    :ivar zone: initial value: zone of the set
    :ivar env: initial value: environment of the set: 'P' for production and 'S' for sandbox

    :param name: name of the set
    :param description: description of the set
    :param query: query to build the set
    :param created_by: user who created the set
    :param private: set as private or not
    :param data: :class:`almapiwrapper.record.XmlData` object, can be used instead of the XML data of the set
    """
    def __init__(self,
                 zone: str,
                 env: Literal['P', 'S'] = 'P',
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 query: Optional[str] = None,
                 created_by: Optional[str] = None,
                 private: Optional[bool] = False,
                 data: Optional[XmlData] = None) -> None:
        """Constructor of `NewRecSet`
        """
        super(RecSet, self).__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'xml'
        self._members = None
        if self._data is None and name is not None and query is not None and created_by is not None:
            self._data = self._create_data(name, query, description, created_by, private)
        else:
            logging.error('NewRecSet: missing parameters to create a new set')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.zone}', '{self.env}', '{self.data.find('name').text}', " \
               f"'{self.data.find('description').text}', '{self.data.find('query').text}', " \
               f"'{self.data.find('created_by').text}', {self.data.find('private').text=='true'})"

    @staticmethod
    def _create_data(name, query, description, created_by, private):
        """Create the XML data for a new set

        :param name: name of the set
        :param query: query of the set
        :param description: description of the set
        :param created_by: user who created the set
        :param private: bool indicating if set is private or public
        :return: XML data
        """
        content = query.split()[0]
        root = etree.Element('set')
        etree.SubElement(root, 'name').text = name
        etree.SubElement(root, 'type').text = 'LOGICAL'
        etree.SubElement(root, 'content').text = content
        etree.SubElement(root, 'description').text = description
        etree.SubElement(root, 'query').text = query
        etree.SubElement(root, 'created_by').text = created_by
        etree.SubElement(root, 'private').text = str(private).lower()
        return XmlData(etree.tostring(root))

    @check_error
    def create(self) -> Union['RecSet', 'NewRecSet']    :
        """Create the set

        :return: `RecSet`
        """
        r = self._api_call('post',
                           f'{self.api_base_url}/conf/sets',
                           headers=self._get_headers(),
                           data=bytes(self))
        if r.ok is True:
            logging.info(f'{repr(self)}: set created')
            self._data = XmlData(r.content)
            self.set_id = self.data.find('.//id').text
            return RecSet(self.set_id, self.zone, self.env, data=self._data)
        else:
            self._handle_error(r, f'unable to create the set')
            return self
