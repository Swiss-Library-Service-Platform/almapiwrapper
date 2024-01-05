from ..record import Record, check_error, JsonData
from typing import Optional, ClassVar, Literal
import almapiwrapper.analytics as analyticslib
from lxml import etree
import pandas as pd
import logging


class AnalyticsReport(Record):
    """Class representing an Analytics report

    :cvar api_base_url_analytics: url of the analytics api
    :ivar path: path of the report
    :ivar zone: initial value: zone of the report
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.XmlData` with raw report data
    :ivar report_name: name of the report
    :ivar filter: filter of the report
"""

    api_base_url_analytics: ClassVar[str] = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/analytics/reports'

    def __init__(self,
                 path: str,
                 zone: str,
                 env: Optional[Literal['P', 'S']] = 'P',
                 filter_to_apply: Optional[str] = None) -> None:
        """Constructor of AnalyticsReport Object
        """

        super().__init__(zone, env)
        self.area = 'Analytics'
        self.format = 'xml'
        self.path = path
        self.report_name = self.path.split('/')[-1]
        self.filter = filter_to_apply

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.
        :return: str
        """
        return f"{self.__class__.__name__}('{self.path}', '{self.zone}', '{self.env}')"


    def _fetch_data(self) -> Optional[pd.DataFrame]:
        """Fetch the json data of the AnalyticsReport

        :return: pandas DataFrame"""

        # Construct params
        params = {"path": self.path,
                  "limit": 1000}
        if self.filter is not None:
            params['filter'] = self.filter

        r = self._api_call('get',
                           f'{self.api_base_url_analytics}',
                           params=params,
                           headers=self._get_headers(rights='R'))
        if r.ok is False:
            self._handle_error(r, f'{repr(self)}: unable to fetch Analytics data')
            return None

        logging.info(f'{repr(self)}: Analytics data available')

        # Resumption token are unique for analytics reports, they are the same for all queries
        resumption_field = etree.fromstring(r.content).find('.//ResumptionToken')
        if resumption_field is not None:
            params = {'limit': '1000',
                      'token': resumption_field.text}

            final_columns = [col.get('{urn:saw-sql}columnHeading') for col in
                             etree.fromstring(r.content).findall('.//{http://www.w3.org/2001/XMLSchema}element')]

            temp_columns = [f'Column{n}' for n in range(len(final_columns))]
            df = pd.DataFrame(columns=temp_columns)

            while True:
                for row in etree.fromstring(r.content).findall('.//{urn:schemas-microsoft-com:xml-analysis:rowset}Row'):
                    data = {}

                    for cell in row:
                        data[cell.tag[cell.tag.find('Column'):]] = cell.text
                    df.loc[len(df)] = data

                logging.info (f'{repr(self)}: {len(df)} rows fetched')

                if etree.fromstring(r.content).find('.//IsFinished').text == 'true':
                    break

                r = self._api_call('get',
                                   f'{self.api_base_url_analytics}',
                                   params=params,
                                   headers=self._get_headers(rights='R'))

                if r.ok is False:
                    self._handle_error(r, f'{repr(self)}: unable to fetch Analytics data')
                    return None

            df.columns = final_columns
            df.drop('0', axis=1, inplace=True)
            return df

    @check_error
    def save(self, format: Optional[Literal['json', 'csv']] = 'csv') -> 'analyticslib.AnalyticsReport':
        """save(self, format: Optional[Literal['json', 'csv']] = 'csv') -> 'analyticslib.AnalyticsReport'
        Save a user fee record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/report_<report_name>/report_<report_name>_<IZ>_<version>.xml

        :return: object :class:`almapiwrapper.analytics.AnalyticsReport`
        """
        filepath = f'records/report_{self.report_name}/report_{self.report_name}_{self.zone}.{format}'
        self._save_from_path(filepath)
        return self

if __name__ == "__main__":
    pass