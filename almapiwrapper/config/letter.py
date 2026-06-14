"""Module for managing Alma letter configuration."""

from typing import Literal, Optional, Union
import logging

from almapiwrapper.record import JsonData, XmlData, Record, check_error


class Letter(Record):
	"""Class representing a configurable Alma letter.

	:param code: Alma letter code
	:param zone: institutional zone
	:param env: environment ('P' for production, 'S' for sandbox)
	:param data: optional payload (JsonData, XmlData, dict, xml/json string)
	"""

	def __init__(self,
				 code: str,
				 zone: str,
				 env: Optional[Literal['P', 'S']] = 'P',
				 data: Optional[Union[JsonData, XmlData, dict, str]] = None):
		super().__init__(zone, env, data)
		self.area = 'Conf'
		self.letter_code = code
		self.format = 'xml'

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}('{self.letter_code}', '{self.zone}', '{self.env}')"

	def _fetch_data(self) -> Optional[Union[JsonData, XmlData]]:
		"""Fetch one letter configuration from Alma."""
		r = self.api_call('get',
						  f'{self.api_base_url}/conf/letters/{self.letter_code}',
						  headers=self._get_headers())
		if r.ok:
			logging.info(f'{repr(self)}: letter data available')
			if self.format == 'json':
				return JsonData(r.json())
			return XmlData(r.content)

		self._handle_error(r, 'unable to fetch letter data')
		return None

	@check_error
	def update(self) -> 'Letter':
		"""Update one letter configuration in Alma."""
		r = self.api_call('put',
						  f'{self.api_base_url}/conf/letters/{self.letter_code}',
						  headers=self._get_headers(),
						  data=bytes(self))
		if r.ok:
			logging.info(f'{repr(self)}: letter updated')
			self.data = XmlData(r.content)
		else:
			self._handle_error(r, 'unable to update letter data')
		return self

	@check_error
	def save(self) -> 'Letter':
		"""Save one letter configuration in Alma."""
		filepath = f'records/letters/{self.zone}_{self.code}.xml'
		self._save_from_path(filepath)
		return self

	@property
	def code(self) -> Optional[str]:
		"""Return the letter code
		:return: letter code
		"""
		if self.data is None:
			return None
		code_field = self.data.find('.//code')
		if code_field is not None:
			return code_field.text
		return None


	@property
	def enabled(self) -> bool:
		"""
		:return: boolean indicating if letter configuration is enabled
		"""
		if self.data is None:
			return False

		enable_field = self.data.find('.//enabled')

		if enable_field is None:
			return False

		if enable_field.text == 'true':
			return True
		return False

	@enabled.setter
	def enabled(self, enabled: bool) -> None:
		"""Set the letter configuration to be enabled
		:param enabled: boolean indicating if letter configuration is enabled

		:return: None"""

		if self.data is None:
			return

		enabled_field = self.data.find('.//enabled')

		if enabled_field is not None:
			enabled_field.text = 'true' if enabled else 'false'
