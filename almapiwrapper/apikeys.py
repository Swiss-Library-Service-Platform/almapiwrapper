import json
import os
from typing import Dict, Any, List, Optional, Literal


class ApiKeys:
    """This class help to manage multiple API Keys

    .. note:: The API keys should be stored in a json file. The path to
        this file has to be in `alma_api_keys` environment variable.

    :Example:

    >>> from almapiwrapper import ApiKeys
    >>> k = ApiKeys()
    >>> api_key_1 = k.get_key('NZ', 'Users', 'RW', 'P')

    Will get an API key for Network Zone with
    read and write rights on users
    in productive environment

    >>> api_key_2 = k.get_key('UBS', 'Bibs', 'RW', 'S')

    Will get an API key for UBS IZ with
    read and write rights on bibliographic data
    in productive environment.
    """
    def __init__(self) -> None:
        """
        Constructor: read the keys file and store it in the private attribute _keys.
        The path to the file should be in an environment variable "alma_api_keys"

        Since the version 0.16, the IZ codes can now be translated with the API keys
        json file. The two format are accepted. The new format is with new level: "zones"
        and "apikeys". The old format is with only directly the IZ codes.
        """
        keys = self._read_keys_file()
        if 'apikeys' in keys:
            self._keys = keys['apikeys']
            self._zones = keys['zones']
        else:
            self._keys = keys

    @staticmethod
    def _read_keys_file() -> Dict[str, Any]:
        """
        Read the json file with API keys.
        :return: data with the api keys
        """
        if os.getenv('alma_api_keys') is None:
            return {}

        with open(os.getenv('alma_api_keys')) as f:
            return json.load(f)

    def get_key(self,
                zone: str,
                area: str,
                permissions: str,
                env: str = 'P') -> str:
        """Return the API key according to the requested parameters

        :param zone: abbreviated form of the IZ or of the NZ
        :param area: area of the API for example "Users"
        :param permissions: read or read/write. It accepts only "R" and "RW"
        :param env: production or sandbox environment, defaults to "P"
        :return: API key

        :raise: KeyError: exception is risen when no corresponding key is found
        """

        # If the zone is not in the keys, it can be a zone alias
        if zone not in self._keys and hasattr(self, _zones) and zone in self._zones:
            zone = self._zones[zone]

        # Fetch the key
        for k in self._keys[zone]:
            for api in k['Supported_APIs']:
                if api['Area'] == area and \
                    api['Permissions'] == permissions and \
                        api['Env'] == env:
                    return k['API_Key']
        raise KeyError(f'No corresponding API key found: zone "{zone}", area "{area}",'
                       f' permission "{permissions}", environment "{env}".')

    def get_iz_codes(self, env: Optional[Literal['P', 'S']] = 'P') -> List[str]:
        """
        Return the list of all IZ abbreviations
        :param env: "P" for production, "S" for sandbox. Default is production
        :return: Code of all IZ
        :rtype: str
        """
        if env == 'P':
            return [k for k in self._keys.keys() if k != 'NZ' or k.endswith('-Prod')]
        else:
            sb_izs = set()
            for zone in self._keys.keys():
                if zone != 'NZ':
                    for k in self._keys[zone]:
                        for api in k['Supported_APIs']:
                            if api['Env'] == 'S':
                                sb_izs.add(zone)
        return list(sb_izs)


if __name__ == "__main__":
    pass
