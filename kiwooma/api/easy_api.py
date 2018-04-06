import pandas as pd
from kiwooma.api.api import API
from PyQt5.QtWidgets import QApplication
from datetime import datetime
import threading
import sys
import time

class EasyAPI(object):

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.api = API()
        self.api.comm_connect() #연결        

    def register_account_no(self, accno):
        """
        사용할 계좌번호를 등록하는 메소드
        """
        self.accno = accno

    def get_account_no(self):
        """
        계좌번호를 리턴하는 메소드

        Returns
        ---------------------------
        accno: string, list

        """
        accno = self.api.get_login_info("ACCNO").split(';')[:-1]
        if len(accno) == 1:
            accno = accno[0]
        return accno

    def get_user_id(self):
        """
        유저 id를 리턴하는 메소드

        Returns
        -----------------------------
        userid: string
        """
        userid = self.api.get_login_info("USER_ID")
        return userid

    def send_order(self, code, quantity, price, trans_type, order_type, org_order_no=''):
        """
        주문을 보내는 메소드
        """

        if not hasattr(self, "accno"):
            raise Excepton('Please register your account_no using register_account_no method')

        order_type_dict = {
            '지정가': '00', '시장가': '03', '조건부지정가': '05', '최유리지정가': '06', '최우선지정가': '07', '지정가IOC': '10',
            '시장가IOC': '13', '최유리IOC': '16', '지정가FOK': '20', '시장가FOK': '23', '최유리FOK': '26', '장전시간외종가': '61',
            '시간외단일가': '62', '장후시간외종가': '81'
            }

        trans_type_dict = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4, '매수정정': 5, '매도정정': 6}

        self.api.send_order("send_order_req", "0011", self.accno, trans_type_dict[trans_type], code, quantity, price, order_type_dict[order_type], org_order_no)

    def get_deposit_detail(self):
        """
        계좌 상세내역을 리턴하는 메소드

        Returns
        --------------------------
        ret:
        """
        self.api.set_input_value("계좌번호", self.accno)
        self.api.comm_rq_data("opw00001_req", "opw00001", 0, "0012")

        ret = self.api._deposit
        return ret

    def get_holding_stocks_pnl(self):
        """
        보유종목들의 손익정보를 리턴하는 메소드

        Returns
        ----------
        ret: list
        """
        self.api.set_input_value("계좌번호", self.accno)
        self.api.comm_rq_data("opt10085_req", "opt10085", 0, "0345")
        ret = self.api.holding_stocks_pnl
        return ret

    def get_today_realized_pnl(self, scode = ''):
        """
        당일 실현 손익 상세 정보를 리턴하는 메소드

        Returns
        ---------------------------------
        ret: float
        """
        self.api.set_input_value("계좌번호", self.accno)
        self.api.set_input_value("비밀번호", '')
        self.api.set_input_value("종목코드", scode)
        self.api.comm_rq_data("opt10077_req", "opt10077", 0, "0013")

        ret = self.api.today_realized_pnl
        return ret

    def get_today_realized_pnl_list(self, scode = ''):
        """
        당일 실현 손익 상세 정보를 리턴하는 메소드

        Returns
        ---------------------------------
        ret: list
        """
        self.api.set_input_value("계좌번호", self.accno)
        self.api.set_input_value("비밀번호", '')
        self.api.set_input_value("종목코드", scode)
        self.api.comm_rq_data("opt10077_req", "opt10077", 0, "0013")

        ret =self.api.today_realized_pnl_list
        return ret

    def get_unexecuted(self):
        """
        실시간 미체결 정보을 리턴하는 메소드

        Returns
        ---------------------------------
        ret: list
        """
        self.api.set_input_value('계좌번호', self.accno)
        self.api.set_input_value('체결구분', 1)
        self.api.set_input_value('매매구분', 0)
        self.api.comm_rq_data("opt10075_req", "opt10075", 0, "0341")

        ret = self.api.current_orders
        return ret
    
    def get_trading_info(self):
        """
        당일 거래내역 정보를 리턴하는 메소드

        Returns
        ----------------------------------
        ret: list
        """

        self.api.set_input_value('계좌번호', self.accno)
        self.api.set_input_value('조회구분', 4)
        self.api.set_input_value('매도수구분', 0)
        self.api.comm_rq_data("opw00007_req", "opw00007", 0, "0351")    

        ret = self.api.today_trading_info    

        return ret

    def get_executed(self):
        """
        실시간 체결 정보을 리턴하는 메소드

        Returns
        ---------------------------------
        ret: list
        """
        self.api.set_input_value('계좌번호', self.accno)
        self.api.set_input_value('체결구분', 2)
        self.api.set_input_value('매매구분', 0)
        self.api.comm_rq_data("opt10075_req", "opt10075", 0, "0341")

        ret = self.api.current_orders
        return ret

    def get_account_balance(self):
        """
        계좌 평가 잔고를 리턴하는 메소드
        """
        self.api.set_input_value("계좌번호", self.accno)
        self.api.comm_rq_data("opw00018_req", "opw00018", 0, "2000")


        ret = self.api.account_balance
        return ret

    def get_portfolio_positions(self):
        """
        포트폴리오의 구성종목에 대한 정보를 불러우는 메소드
        """
        self.api.set_input_value("계좌번호", self.accno)
        self.api.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        ret = self.api.portfolio_positions
        return ret
    def get_new_high_low(self, market='all', high_or_low=1, criteria=2, condition=0, include_limit=0, period=250):
        """
        신고저가를 갱신한 종목을 리턴하는 메소드

        Parameters
        ----------
        market: string
            all, kospi, kosdaq
        high_or_low: integer
            1: 신고가, 2: 신저가
        criteria: integer
            고저종구분
            1: 고저기준, 2: 종가기준
        condition: integer
            0: 전체조회, 1: 관리종목제외, 3: 우선주제외
        include_limit: integer
            0:상하한 미포함, 1: 상하한 포함
        period: integer
            기간
        """
        if hasattr(self.api, '_opt10016'):
            self.api.reset_opt10016()

        market_dict = {'all': '000', 'kospi': '001', 'kosdaq': '101'}
        market_no = market_dict[market.lower()]
        self.api.set_input_value("시장구분", market_no)
        self.api.set_input_value("신고저구분", high_or_low)
        self.api.set_input_value("고저종구분", criteria)
        self.api.set_input_value("종목조건", condition)
        self.api.set_input_value("거래량구분", '00000')
        self.api.set_input_value("신용조건", '0')
        self.api.set_input_value("상하한포함", include_limit)
        self.api.set_input_value("기간", period)
        self.api.comm_rq_data("opt10016_req", "opt10016", 0, "0015")

        while self.api.remained_data:
            time.sleep(0.2)
            self.api.set_input_value("시장구분", market_no)
            self.api.set_input_value("신고저구분", high_or_low)
            self.api.set_input_value("고저종구분", criteria)
            self.api.set_input_value("종목조건", condition)
            self.api.set_input_value("거래량구분", '00000')
            self.api.set_input_value("신용조건", '0')
            self.api.set_input_value("상하한포함", include_limit)
            self.api.set_input_value("기간", period)
            self.api.comm_rq_data("opt10016_req", "opt10016", 0, "0015")

        ret = pd.DataFrame(self.api._opt10016, columns =['종목코드', '종목명', '현재가', '고가', '저가', '등락률', '거래량',
                          '전일거래량대비율', '매도호가', '매수호가'])
        return ret

    def get_limit_high_low(self, market='all', high_or_low=1, criteria=1, condition=0):
        """
        상한가, 하한가를 기록한 종목을 리턴하는 메소드

        Parameters
        ----------
        market: string
            all, kospi, kosdaq
        high_or_low: integer
            상하한구분
            1:상한, 2:상승, 3:보합, 4: 하한, 5:하락, 6:전일상한, 7:전일하한
        criteria: integer
            정렬구분
            1:종목코드순, 2:연속횟수순(상위100개), 3:등락률순
        condition: integer
            0:전체조회,1:관리종목제외, 3:우선주제외, 4:우선주+관리종목제외, 5:증100제외,
            6:증100만 보기, 7:증40만 보기, 8:증30만 보기, 9:증20만 보기, 10:우선주+관리종목+환기종목제외
        """
        if hasattr(self.api, '_opt10017'):
            self.api.reset_opt10016()

        market_dict = {'all': '000', 'kospi': '001', 'kosdaq': '101'}
        market_no = market_dict[market.lower()]
        self.api.set_input_value("시장구분", market_no)
        self.api.set_input_value("상하한구분", high_or_low)
        self.api.set_input_value("정렬구분", criteria)
        self.api.set_input_value("종목조건", condition)
        self.api.set_input_value("거래량구분", '00000')
        self.api.set_input_value("신용조건", '0')
        self.api.set_input_value("매매금구분",'0')
        self.api.comm_rq_data("opt10017_req", "opt10017", 0, "0016")

        while self.api.remained_data:
            time.sleep(0.5)
            self.api.set_input_value("시장구분", market_no)
            self.api.set_input_value("상하한구분", high_or_low)
            self.api.set_input_value("정렬구분", criteria)
            self.api.set_input_value("종목조건", condition)
            self.api.set_input_value("거래량구분", '00000')
            self.api.set_input_value("신용조건", '0')
            self.api.set_input_value("매매금구분",'0')
            self.api.comm_rq_data("opt10017_req", "opt10017", 0, "0016")

        ret = pd.DataFrame(self.api._opt10017, columns =['종목코드', '종목명', '현재가', '전일대비', '등락률', '거래량',
                          '전일거래량', '매도호가', '매수호가', '매도잔량', '매수잔량'])
        return ret

    def get_daily_ohlcv(self, code, repeat=0, adj_close=1):
        '''
        일봉 정보를 리턴하는 메소드

        code: string
        repeat: integer
        adj_close: boolean
            0: 실제주가, 1: 수정주가

        '''
        base_date = datetime.today().date().strftime('%Y%m%d')
        self.api.reset_ohlcv()

        ohlcv = self._request_daily_ohlcv(code, base_date, adj_close, 0)

        for i in range(repeat-1):
            time.sleep(0.25)
            if self.api.remained_data == True:
                self._request_daily_ohlcv(code, base_date, adj_close, 2)
        # Return DataFrame
        df = pd.DataFrame(self.api.ohlcv, columns=list(self.api.ohlcv.keys()))
        df.set_index('date', inplace=True)
        df.insert(0, 'code', code)
        return df.iloc[::-1]

    def _request_daily_ohlcv(self, code, base_date, adj_close, next_type):
        # Request TR and get data
        index_codes = {
            'kospi':'001', 'large':'002', 'middle':'003', 'small':'004', 'kosdaq': '101',
            'kospi200': '201', 'kostar': '302', 'krx100': '701'
            }
        if not next_type:
            self.api.set_input_value("기준일자", base_date)
        if code.lower() in index_codes.keys():
            self.api.set_input_value("업종코드", index_codes[code])
            req, trcode = "opt20006_req", "opt20006"
        else:
            self.api.set_input_value("종목코드", code)
            req, trcode = "opt10081_req", "opt10081"

        self.api.set_input_value("수정주가구분", adj_close)
        self.api.comm_rq_data(req, trcode, next_type, "0001")

    def get_weekly_ohlcv(self, code, repeat=0, adj_close=1):
        '''
        주봉 정보를 리턴하는 메소드

        code: string
        repeat: integer
        adj_close: integer
            0: 실제주가, 1: 수정주가

        '''
        base_date = datetime.today().date().strftime('%Y%m%d')
        self.api.reset_ohlcv()

        ohlcv = self._request_weekly_ohlcv(code, base_date, adj_close, 0)

        for i in range(repeat-1):
            time.sleep(0.25)
            if self.api.remained_data == True:
                self._request_weekly_ohlcv(code, base_date, adj_close, 2)
        # Return DataFrame
        df = pd.DataFrame(self.api.ohlcv, columns=list(self.api.ohlcv.keys()))
        df.set_index('date', inplace=True)
        df.insert(0, 'code', code)
        return df.iloc[::-1]


    def _request_weekly_ohlcv(self, code, base_date, adj_close, next_type):
        # Request TR and get data
        index_codes = {
            'kospi':'001', 'large':'002', 'middle':'003', 'small':'004', 'kosdaq': '101',
            'kospi200': '201', 'kostar': '302', 'krx100': '701'
            }
        if not next_type:
            self.api.set_input_value("기준일자", base_date)
        if code.lower() in index_codes.keys():
            self.api.set_input_value("업종코드", index_codes[code])
            req, trcode = "opt20007_req", "opt20007"
        else:
            self.api.set_input_value("종목코드", code)
            req, trcode = "opt10082_req", "opt10082"

        self.api.set_input_value("수정주가구분", adj_close)
        self.api.comm_rq_data(req, trcode, next_type, "0001")
        
    def get_monthly_ohlcv(self, code, repeat=0, adj_close=1):
        '''
        월봉 정보를 리턴하는 메소드

        code: string
        repeat: integer
        adj_close: integer
            0: 실제주가, 1: 수정주가

        '''
        base_date = datetime.today().date().strftime('%Y%m%d')
        self.api.reset_ohlcv()

        ohlcv = self._request_weekly_ohlcv(code, base_date, adj_close, 0)

        for i in range(repeat-1):
            time.sleep(0.25)
            if self.api.remained_data == True:
                self._request_weekly_ohlcv(code, base_date, adj_close, 2)
        # Return DataFrame
        df = pd.DataFrame(self.api.ohlcv, columns=list(self.api.ohlcv.keys()))
        df.set_index('date', inplace=True)
        df.insert(0, 'code', code)
        return df.iloc[::-1]


    def _request_monthly_ohlcv(self, code, base_date, adj_close, next_type):
        # Request TR and get data
        index_codes = {
            'kospi':'001', 'large':'002', 'middle':'003', 'small':'004', 'kosdaq': '101',
            'kospi200': '201', 'kostar': '302', 'krx100': '701'
            }
        if not next_type:
            self.api.set_input_value("기준일자", base_date)
        if code.lower() in index_codes.keys():
            self.api.set_input_value("업종코드", index_codes[code])
            req, trcode = "opt20008_req", "opt20008"
        else:
            self.api.set_input_value("종목코드", code)
            req, trcode = "opt10083_req", "opt10083"

        self.api.set_input_value("수정주가구분", adj_close)
        self.api.comm_rq_data(req, trcode, next_type, "0001")



    def get_minutely_ohlcv(self, code, tick, repeat=0, adj_close=1):
        '''
        분봉 데이터를 리턴하는 메소드

        code: string
        tick: integer
        repeat: integer
        adj_close: integer
            0: 실제주가, 1: 수정주가
        '''

        base_date = datetime.today().date().strftime('%Y%m%d')
        self.api.reset_ohlcv()

        ohlcv = self._request_minutely_ohlcv(code, tick, adj_close, 0)

        for i in range(repeat-1):
            time.sleep(0.25)
            if self.api.remained_data == True:
                self._request_minutely_ohlcv(code, tick, adj_close, 2)

        # Return DataFrame
        df = pd.DataFrame(self.api.ohlcv, columns=list(self.api.ohlcv.keys()))
        df.set_index('date', inplace=True)
        df = df.abs()
        df.insert(0, 'code', code)
        return df.iloc[::-1]

    def _request_minutely_ohlcv(self, code, tick, adj_close, next_type):
        # Request TR and get data

        self.api.set_input_value("종목코드", code)
        req, trcode = "opt10080_req", "opt10080"
        self.api.set_input_value("틱범위", tick)
        self.api.set_input_value("수정주가구분", adj_close)
        self.api.comm_rq_data(req, trcode, next_type, "0002")

    def basic_info(self, code):
        """
        주식 기본 정보를 리턴하는 메소드
        """
        self.api.set_input_value("종목코드", code)
        self.api.comm_rq_data("opt10001_req", "opt10001", 0, "0003")

        return self.api.stock_info

    def get_code_list_by_market(self, market):
        assert isinstance(market, str)
        market = market.lower()
        market_dict = {'kospi': 0, 'elw': 3, 'mutual': 4, 'sinju': 5, 'reits': 6,
                    'etf': 8, 'highyieldfund': 9, 'kosdaq': 10, '3rd': 30}

        market_no = market_dict[market]
        ret = self.api.get_code_list_by_market(market_no)
        return ret

    def get_code_name(self, code):
        ret = self.api.get_master_code_name(code)
        return ret

    def get_connect_state(self):
        ret = self.api.get_connect_state

    def request_real_data(self, codes, add_list=False):
        self.api.request_real_data(codes, add_list)



if __name__ == '__main__':
    api = EasyAPI()
    print(api.get_account_no())
    api.register_account_no(api.get_account_no())
    # print(api.get_daily_ohlcv('kospi'))
    # print(api.get_deposit_detail())
    # print(api.get_account_balance())
    print(api.get_trading_info())
   