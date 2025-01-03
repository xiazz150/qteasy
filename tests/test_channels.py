# coding=utf-8
# ======================================
# File:     test_channels.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-12-25
# Desc:
#   Testing download data from different
# data channels for every possible data
# table in the test datasource.
# ======================================

import unittest

from qteasy.database import DataSource
from qteasy.data_channels import (
    TUSHARE_API_MAP,
    EASTMONEY_API_MAP,
    AKSHARE_API_MAP,
    fetch_history_table_data,
    fetch_realtime_price_data,
    _parse_list_args,
    _parse_datetime_args,
    _parse_trade_date_args,
    _parse_quarter_args,
    _parse_month_args,
    _parse_table_index_args,
    _parse_additional_time_args,
    _parse_data_fetch_args,
    _parse_tables_to_fetch,
)


class TestChannels(unittest.TestCase):

    def setUp(self):
        from qteasy import QT_CONFIG
        self.ds = DataSource(
            'db',
            host=QT_CONFIG['test_db_host'],
            port=QT_CONFIG['test_db_port'],
            user=QT_CONFIG['test_db_user'],
            password=QT_CONFIG['test_db_password'],
            db_name=QT_CONFIG['test_db_name']
        )
        print('test datasource created.')

    def test_channel_tushare(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # tables into which to download data are from TABLE_MASTERS,
        # but in the future, tables should be from data_channels
        all_tables = TUSHARE_API_MAP.keys()

        self.assertIsInstance(self.ds, DataSource)

        # if there already are tables existing in the datasource, drop them
        print('dropping tables in the test database...')
        for table in all_tables:
            if table == 'real_time':
                continue
            if self.ds.table_data_exists(table):
                # these data can be retained for further testing
                self.ds.drop_table_data(table)
                print(f'table {table} dropped.')
        print('tables dropped.')

        for table in all_tables:
            if table == 'real_time':
                continue

            # get all tables in the API mapping
            api_name = TUSHARE_API_MAP[table][0]
            arg_name = TUSHARE_API_MAP[table][1]
            arg_type = TUSHARE_API_MAP[table][2]
            arg_range = TUSHARE_API_MAP[table][3]

            print(f'downloading data for table: {table} with api: {api_name} and arg: {arg_name}')

            # parse the filling args and pick the first filling arg value from the range
            if arg_name == 'none':
                arg_name = None
                arg_value = None
            else:
                if arg_type == 'list':
                    from qteasy.utilfuncs import str_to_list
                    range_list = str_to_list(arg_range)
                    arg_value = range_list[0]
                elif arg_type == 'datetime':
                    arg_value = '20210226'
                elif arg_type == 'trade_date':
                    arg_value = '20210226'  # 这个交易日是特意选择的，因为它既是一个交易日，也同时是一周/一月内的最后一个交易日
                elif arg_type == 'quarter':
                    arg_value = '2020Q4'
                elif arg_type == 'month':
                    arg_value = '202102'
                elif arg_type == 'table_index' and arg_range == 'stock_basic':
                    arg_value = '000651.SZ'
                elif arg_type == 'table_index' and arg_range == 'index_basic':
                    arg_value = '000001.SH'
                elif arg_type == 'table_index' and arg_range == 'fund_basic':
                    arg_value = '531300.SH'
                elif arg_type == 'table_index' and arg_range == 'future_basic':
                    arg_value = 'IF2009.CCFX'
                elif arg_type == 'table_index' and arg_range == 'opt_basic':
                    arg_value = '10001234.SH'
                elif arg_type == 'table_index' and arg_range == 'ths_index_basic':
                    arg_value = '700031.TI'
                else:
                    raise ValueError('unexpected arg type:', arg_type)

            # build the args dict
            if arg_name is not None:
                kwargs = {arg_name: arg_value}
            else:
                kwargs = {}

            # add retry parameters to shorten test time
            kwargs['retry_count'] = 1

            try:
                dnld_data = fetch_history_table_data(table, channel='tushare', **kwargs)
                print(f'{len(dnld_data)} rows of data downloaded:\n{dnld_data.head()}')
            except Exception as e:
                print(f'error downloading data for table {table}: {e}')
                continue

            # clean up the data, making it ready to be written to the datasource
            from qteasy.database import get_built_in_table_schema, set_primary_key_frame
            columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
            ready_data = set_primary_key_frame(dnld_data, primary_keys, pk_dtypes)

            # write data to datasource
            self.ds.update_table_data(table, ready_data, merge_type='update')
            print('data written to database.')

    def test_arg_parsing(self):
        """testing parsing of filling args"""

        print('testing parsing list type args')
        arg_range = 'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z'
        list_arg_filter = 'A, B, E'

        res = list(_parse_list_args(arg_range, list_arg_filter))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'E'])

        list_arg_filter = ['A', 'B', 'E']
        res = list(_parse_list_args(arg_range, ['A', 'B', 'E'], reversed_par_seq=True))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['E', 'B', 'A'])

        list_arg_filter = 'A:E'
        res = list(_parse_list_args(arg_range, 'A:E', reversed_par_seq=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C', 'D', 'E'])

        list_arg_filter = 'D:A'
        res = list(_parse_list_args(arg_range, 'D:A', reversed_par_seq=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C', 'D'])

        list_arg_filter = None
        res = list(_parse_list_args(arg_range, None, reversed_par_seq=True))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['Z', 'Y', 'X', 'W', 'V', 'U', 'T', 'S', 'R', 'Q', 'P', 'O', 'N', 'M', 'L', 'K',
                               'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        )

        list_arg_filter = 'A:C:P'
        res = list(_parse_list_args(arg_range, 'A:C:P', reversed_par_seq=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C'])

        # testing error handling:
        with self.assertRaises(Exception):
            list(_parse_list_args(arg_range, ['A:Z:1'], reversed_par_seq=False))
            list(_parse_list_args(arg_range, 35, reversed_par_seq=False))

        print('testing parsing datetime type args')
        arg_range = '20210101'

        start, end = '20210201', '20210210'
        res = _parse_datetime_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210201', '20210202', '20210203', '20210204', '20210205', '20210206',
                               '20210207', '20210208', '20210209', '20210210'])

        start, end = '20201220', '20210105'
        res = _parse_datetime_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210101', '20210102', '20210103', '20210104', '20210105'])

        start, end = '20201220', '20210105'
        res = _parse_datetime_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210105', '20210104', '20210103', '20210102', '20210101'])

        start, end = '20210110', '20210105'
        res = _parse_datetime_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210110', '20210109', '20210108', '20210107', '20210106', '20210105'])

        start, end, freq = '20210101', '20210201', 'W'
        res = _parse_datetime_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210101', '20210108', '20210115', '20210122', '20210129'])

        start, end, freq = '20210101', '20210401', 'M'
        res = _parse_datetime_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210131', '20210228', '20210331'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_datetime_args(arg_range, 'not_a_date', '20201231')
            _parse_datetime_args(arg_range, '20210101', 20201231)

        print('testing parsing trade_date args')
        arg_range = '20210101'

        start, end = '20210201', '20210210'
        res = _parse_trade_date_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210201', '20210202', '20210203', '20210204', '20210205',
                               '20210208', '20210209', '20210210'])

        start, end = '20201220', '20210105'
        res = _parse_trade_date_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210104', '20210105'])

        start, end = '20201220', '20210105'
        res = _parse_trade_date_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210105', '20210104'])

        start, end = '20210110', '20210105'
        res = _parse_trade_date_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210108', '20210107', '20210106', '20210105'])

        start, end, freq = '20210101', '20210201', 'W'
        res = _parse_trade_date_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20201231', '20210108', '20210115', '20210122', '20210129'])

        start, end, freq = '20210101', '20210401', 'M'
        res = _parse_trade_date_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210129', '20210226', '20210331'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_trade_date_args(arg_range, 'not_a_date', '20201231')
            _parse_trade_date_args(arg_range, '20210101', 20201231)

        print('testing parsing table index args')

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ:000660.SZ')
        print(f'symbols: 000651.SZ:000660.SZ:\n{res}')
        self.assertEqual(res, ['000651.SZ', '000652.SZ', '000655.SZ', '000656.SZ', '000657.SZ', '000659.SZ'])

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ:000660.SZ', reversed_par_seq=True)
        print(f'symbols: 000651.SZ:000660.SZ:\n{res}')
        self.assertEqual(res, ['000659.SZ', '000657.SZ', '000656.SZ', '000655.SZ', '000652.SZ', '000651.SZ'])

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ,000659.SZ, 600000.SH, 600004.SH')
        print(f'symbols: 000651.SZ,000660.SZ, 600001.SH, 600002.SH:\n{res}')
        self.assertEqual(res, ['000651.SZ', '000659.SZ', '600000.SH', '600004.SH'])

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ,000659.SZ, 600000.SH, 600004.SH',
                                      allowed_code_suffix='SZ')
        print(f'symbols: 000651.SZ,000659.SZ, 600000.SH, 600004.SH:\n{res}')
        self.assertEqual(res, ['000651.SZ', '000659.SZ'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_table_index_args(arg_range, symbols=651,
                                    allowed_code_suffix='SZ,SH')
            _parse_table_index_args(arg_range, symbols=['000651.SZ:000660.SZ'],
                                    allowed_code_suffix='SZ,SH')

        print('testing parsing quarter and month args')

        arg_range = '2020Q1'
        res = _parse_quarter_args(arg_range, '20200101', '20200930')
        print(f'start, end: 20200101, 20200930:\n{res}')
        self.assertEqual(res, ['2020Q1', '2020Q2', '2020Q3'])

        arg_range = '2020Q1'
        res = _parse_quarter_args(arg_range, '20200101', '20201031')
        print(f'start, end: 20200101, 20201031:\n{res}')
        self.assertEqual(res, ['2020Q1', '2020Q2', '2020Q3', '2020Q4'])

        res = _parse_quarter_args(arg_range, '20210331', '20191021', reversed_par_seq=True)
        print(f'start, end: 2021Q1, 2019Q3:\n{res}')
        self.assertEqual(res, ['2021Q1', '2020Q4', '2020Q3', '2020Q2', '2020Q1'])

        arg_range = '20210101'
        res = _parse_month_args(arg_range, '20210101', '20210331')
        print(f'start, end: 20210101, 20210331:\n{res}')
        self.assertEqual(res, ['202101', '202102', '202103'])

        arg_range = '20200901'
        res = _parse_month_args(arg_range, '20200101', '20210530', reversed_par_seq=True)
        print(f'start, end: 20200101, 20210530:\n{res}')
        self.assertEqual(res, ['202105', '202104', '202103', '202102', '202101',
                               '202012', '202011', '202010', '202009'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_quarter_args(arg_range, '202001', '2020030')
            _parse_month_args(arg_range, '20200101', 20200930)

        print('testing parsing additional start/end args')
        arg_range = 15
        res = _parse_additional_time_args(arg_range, '20210101', '20210321')
        print(f'start, end: 20210101, 20210321:\n{res}')
        self.assertEqual(
                res,
                [
                    {'end': '20210116', 'start': '20210101'},
                    {'end': '20210131', 'start': '20210116'},
                    {'end': '20210215', 'start': '20210131'},
                    {'end': '20210302', 'start': '20210215'},
                    {'end': '20210317', 'start': '20210302'},
                    {'end': '20210321', 'start': '20210317'},
                ]
        )

    def test_table_arg_parsing(self):
        """ testing parsing complete table download args """

        table = 'stock_basic'

        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = _parse_data_fetch_args(table=table,
                                      channel='tushare',
                                      symbols='000651.SZ:000660.SZ',
                                      start_date='20210101',
                                      end_date='20210321',
                                      freq='d',
                                      list_arg_filter=None,
                                      reversed_par_seq=False,
                                      )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args, [{'exchange': 'SSE'}, {'exchange': 'SZSE'}, {'exchange': 'BSE'}])

        table = 'stock_daily'
        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = _parse_data_fetch_args(table=table,
                                      channel='tushare',
                                      symbols='000651.SZ:000660.SZ',
                                      start_date='20210101',
                                      end_date='20210110',
                                      freq='d',
                                      list_arg_filter=None,
                                      reversed_par_seq=False,
                                      )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args, [{'trade_date': '20210104'},
                                {'trade_date': '20210105'},
                                {'trade_date': '20210106'},
                                {'trade_date': '20210107'},
                                {'trade_date': '20210108'}])

        table = 'index_daily'
        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = _parse_data_fetch_args(table=table,
                                      channel='tushare',
                                      symbols='000001.SH, 000011.SH, 000016.SH, 000300.OTHER',
                                      start_date='20210101',
                                      end_date='20210110',
                                      freq='d',
                                      list_arg_filter=None,
                                      reversed_par_seq=False,
                                      )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args, [{'ts_code': '000001.SH', 'start': '20210101', 'end': '20210110'},
                                {'ts_code': '000016.SH', 'start': '20210101', 'end': '20210110'}])

    def test_parse_table_names(self):
        """ test function _parse_tables_to_fetch"""
        tables = ['all']
        print(f'testing parsing table names {tables}')
        res = _parse_tables_to_fetch('tushare', tables, )
        print(f'fetching all tables: \n{res}')
        print('tables under expected',[table for table in TUSHARE_API_MAP.keys() if table not in res])
        print('tables more than expected', [table for table in res if table not in TUSHARE_API_MAP.keys()])
        self.assertTrue(all(table in res for table in TUSHARE_API_MAP.keys()))
        self.assertTrue(all(table in TUSHARE_API_MAP.keys() for table in res))

        tables = ['stock_basic', 'stock_daily', 'index_daily']
        res = _parse_tables_to_fetch('tushare', tables=tables)
        print(f'fetching tables: stock_basic, stock_daily, index_daily: \n{res}')
        expected_tables = ['stock_basic', 'stock_daily', 'index_daily', 'index_basic']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['basics']
        res = _parse_tables_to_fetch('tushare', tables=tables)
        print(f'fetching tables: basics: \n{res}')
        expected_tables = ['stock_basic', 'index_basic', 'fund_basic', 'future_basic', 'opt_basic', 'ths_index_basic',
                           'stock_company', 'new_share','sw_industry_basic']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['events']
        res = _parse_tables_to_fetch('tushare', tables=tables)
        print(f'fetching tables: events: \n{res}')
        expected_tables = ['stock_suspend', 'dividend', 'hs_top10_stock', 'block_trade', 'stock_holder_trade',
                           'stock_names', 'margin_detail', 'stock_basic', 'hk_top10_stock', 'stk_managers',
                           'fund_basic', 'top_list', 'fund_manager', 'top_inst']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['mins']
        res = _parse_tables_to_fetch('tushare', tables=tables)
        print(f'fetching tables: mins: \n{res}')
        expected_tables = ['fund_15min', 'future_15min', 'opt_basic', 'index_basic', 'fund_1min', 'options_1min',
                           'stock_15min', 'future_basic', 'index_5min', 'stock_hourly', 'options_5min', 'stock_30min',
                           'options_hourly', 'future_1min', 'index_15min', 'stock_basic', 'fund_30min', 'future_hourly',
                           'fund_hourly', 'future_30min', 'options_15min', 'options_30min', 'stock_5min',
                           'index_hourly', 'future_5min', 'stock_1min', 'index_30min', 'index_1min', 'fund_5min',
                           'fund_basic']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['mins', 'events']
        freq = ['h']
        expected_tables = ['fund_hourly', 'future_hourly', 'options_hourly', 'stock_hourly', 'index_hourly',
                           'future_basic', 'index_basic', 'opt_basic', 'fund_basic', 'stock_basic']
        res = _parse_tables_to_fetch('tushare', tables=tables, freqs=freq)
        print(f'fetching tables: mins, events: \n{res}')
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['stock_basic', 'stock_daily', 'index_daily']
        freq = ['d']
        dtypes = ['close']
        expected_tables = ['index_basic', 'stock_daily', 'index_daily']
        res = _parse_tables_to_fetch('tushare', tables=tables, freqs=freq, dtypes=dtypes)
        print(f'fetching tables: stock_basic, stock_daily, index_daily: \n{res}')
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

    def test_realtime_data(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # test acquiring real time data

        table = 'real_time'
        # get all tables in the API mapping
        print('downloading data for table:', table)
        dnld_data = fetch_realtime_price_data(channel='tushare', qt_code='000001.SZ')


if __name__ == '__main__':
    unittest.main()