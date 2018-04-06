import sys
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QObject, pyqtSignal, QEventLoop, QThread
import time
import pandas as pd
from datetime import datetime
from kiwooma.utils import *
import collections

class API(QObject):

    chejan_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.ocx = QAxWidget()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        """
        Kiwoom Open API 객체를 사용
        """
        self.ocx.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def get_login_info(self, tag):
        """
        로그인 계정 정보와 계좌정보를 호출하는 메소드
        """
        loginInfo = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return loginInfo

    def _set_signal_slots(self):
        """
        KiwoomAPI에서 발생시키는 이벤트를 연결해주는 메소드
        """
        self.ocx.OnEventConnect.connect(self._event_connect)
        self.ocx.OnReceiveTrData.connect(self._receive_tr_data) # OnReceiveTrData이벤트 발생시
        self.ocx.OnReceiveChejanData.connect(self._receive_chejan_data) # OnReceiveChejanData이벤트 발생시
        self.ocx.OnReceiveRealData.connect(self._receive_real_data)

    def comm_connect(self):
        """
        키움증권 API에 로그인하는 메소드
        """
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        """
        OnEventConnect 이벤트가 발생할 때 호출되는 메소드
        """
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")
            raise Exception()

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market_no):
        """
        시장별 종목코드 리스트를 리턴하는 메소드

        Parameters
        -------------------------
        market_no: integer

        Returns
        -------------------------
        codes: list
        """

        code_list = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market_no)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_master_code_name(self, code):
        """
        종목코드를 이용하여 종목명을 불러오는 메소드

        Parameters
        ---------------------
        code: str

        Returns
        ---------------------
        code_name: str
        """
        assert type(code) == str

        code_name = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        """
        연결상태를 반환하는 메소드

        Returns
        ---------------------
        state: int
            0: 미연결, 1: 연결
        """
        state = self.ocx.dynamicCall("GetConnectState()")
        return state

    def _request_order_result(self, rqname, trcode):
        ret = self._comm_get_data(trcode, "", rqname, 0, '주문번호')
        if ret == '':
            print('주문이 실패하였습니다. 보유 현금 이상으로 주문을 하셨는지, 기존에 들어가 있는 주문이 없는지 확인해주세요.')
        else:
            print('주문번호: {0} 주문 성공적으로 이루어졌습니다.'.format(ret))

    def send_order(self, rqname, screen_no, acc_no, order_class, code, quantity, price, order_type, org_order_no):
        """
        주문신호를 보내는 메소드

        Parameters
        ----------------------
        rqname: string
            요청명
        screen_no: string
            화면번호 (4자리)
        acc_no: str
            계좌번호
        order_class: integer
            거래구분 {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4, '매수정정': 5, '매도정정': 6}
        code: str
            종목코드
        quantity: integer
            주문수량
        price: integer
            주문가격
        order_type: string
            주문유형 {'지정가': '00', '시장가': '03', '조건부지정가': '05', '최유리지정가': '06', '최우선지정가': '07', '지정가IOC': '10', '시장가IOC': '13',
                     '최유리IOC': '16', '지정가FOK': '20', '시장가FOK': '23','최유리FOK': '26', '장전시간외종가': '61', '시간외단일가': '62', '장후시간외종가': '81'}
        org_order_no: string
            원주문번호
        """
        self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                     [rqname, screen_no, acc_no, order_class, code, quantity, price, order_type, org_order_no])


    def get_server_gubun(self):
        """
        실/모의 투자를 구분하기 위한 서버값을 리턴
        """
        ret = self.ocx.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    """
    --------------------------------------------
    |  TR 요청 및 데이터 반환에 관련된 메소드 모음  |
    --------------------------------------------
    """

    def set_input_value(self, item, value):
        """
        TR의 Input값을 입력하는 메소드

        Parameters
        ---------------------
        item: str
            아이템명
        value: str
            입력값
        """
        self.ocx.dynamicCall("SetInputValue(QString, QString)", item, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        """
        서버로 TR 요청을 보내는 메소드
        데이터를 받으면 이벤트 발생

        Parameters
        -----------------------
        rqname: str
            요청명
        trcode: str
        next: int
            연속조회 유무 0: 조회 / 2: 연속
        screen_no: str
            화면번호 (임의의 4자리 숫자)
        """
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)",
                            rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, trcode, real_type, rqname, index, item_name):
        """
        요청한 TR 데이터 반환 메소드

        Parameters
        -----------------------
        trcode: str
        real_type: str
            빈문자열: ''
        rqname: str
        index: int
            반복인덱스 0: 조회 / 2: 연속
        item_name: str

        Returns
        -----------------------
        data: str
        """
        data = self.ocx.dynamicCall("CommGetData(QString, QString, QString, int, QString)",
                                trcode, real_type, rqname, index, item_name)
        return data.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        """
        받은 데이터의 개수를 반환하는 메소드

        Parameters
        -----------------------
        trcode: str
        rqname: str

        Returns
        -----------------------
        cnt: int
        """
        cnt = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return cnt

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        """
        OnReceiveTrData이벤트 발생시 호출되는 메소드

        Parameters
        --------------------
        screen_no: str
        rqname: str
        trcode: str
        record_name: str
        next: 연속조회 유무 - 조회(0) / 연속(2)
        """

        if next == '2': ## 연속 데이터 조회 확인
            self.remained_data = True
        else:
            self.remained_data = False

        opt_type = {
            'price_info': ['opt10081_req', 'opt20006_req', 'opt10080_req', 'opt10082_req', 'opt10083_req', 'opt20007_req',
                            'opt20008_req' ]
        }

        tr_dict = {'opt10081_req': self._request_price_info, 'opt20006_req': self._request_price_info,
                   'opt10080_req': self._request_price_info, 'opw00001_req': self._request_deposit_detail,
                   'opw00018_req': self._request_account_balance, 'opt10075_req': self._request_unexcuted,
                   'opt10077_req': self._request_today_realized_pnl, 'opt10001_req': self._request_stock_info,
                   'opt10016_req': self._request_new_high_and_low, 'opt10017_req': self._request_limit_high_low,
                   'opt10085_req': self._request_holding_stock_pnl, 'opw00007_req': self._request_trading_info,
                   'opt10082_req': self._request_price_info, 'opt10083_req': self._request_price_info,
                   'opt20007_req': self._request_price_info, 'opt20008_req': self._request_price_info,
                   'send_order_req': self._request_order_result
                   }
        try:
            tr_dict[rqname](rqname, trcode)
        except KeyError:
            print(trcode)
            print(rqname + ' error')

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _request_holding_stock_pnl(self, rqname, trcode):
        """
        보유종목들의 손익정보 요청

        Paramenters
        ---------
        rqname: string
        trcode: string
        """

        self.holding_stocks_pnl = []

        data_cnt = self._get_repeat_cnt(trcode, rqname)

        item_list = output_list = ('일자', '종목코드', '종목명', '현재가', '매입가',
                                   '매입금액', '보유수량', '당일매도손익',
                                   '당일매도수수료', '당일매매세금', '신용구분',
                                   '대출일', '결제잔고', '청산가능수량', '신용금액',
                                   '신용이자', '만기일')

        for i in range(data_cnt):
            temp_dict = {}
            for item in output_list:
                data = self._comm_get_data(trcode, "", rqname, i, item)
                if item == '현재가':
                    if data[0] in ('+', '-'):
                        data = data[1:]
                elif item not in ('일자', '종목코드', '종목명', '신용구분', '대출일', '보유수량', '결제잔고', '만기일', '청산가능수량'):
                    data = to_float(data)
                elif item in ('보유수량', '결제잔고', '청산가능수량'):
                    data = int(data)

                temp_dict[item] = data

            self.holding_stocks_pnl.append(temp_dict)


    def _request_stock_info(self, rqname, trcode):
        """
        주식기본정보요청시 호출되는 메소드

        Parameters
        -----------------------
        rqname: string
        trcode: string
        """
        output_list = ('종목코드', '종목명', '결산월', '액면가', '자본금', '상장주식', '신용비율', '연중최고', '연중최저',
                     '시가총액', '시가총액비중', '외인소진률', '대용가', 'PER', 'EPS', 'ROE', 'PBR', 'EV', '매출액', '영업이익',
                     '당기순이익', '250최고', '250최저', '시가', '고가', '저가', '상한가', '하한가', '기준가', '예상체결가', '예상체결수량',
                     '250최고가일', '250최고가대비율', '250최저가일', '250최저가대비율', '현재가', '대비기호', '전일대비', '등락율', '거래량',
                     '거래대비', '액면가단위')

        self.stock_info = {}
        for item in output_list:
            data = self._comm_get_data(trcode, "", rqname, 0, item)
            if item in ('250최고', '250최저', '시가', '고가', '저가', '상한가', '하한가', '기준가', '연중최저', '연중최고', '예상체결가'):
                if data[0] in ('+', '-'):
                    data = data[1:]
            if item not in ('종목코드', '종목명', '결산월', '액면가단위', '250최고가일', '250최저가일'):
                data = to_float(data)
            self.stock_info[item] = data

    def _request_new_high_and_low(self, rqname, trcode):
        """
        신고/저가요청시 호출되는 메소드
        """
        if not hasattr(self, '_opt10016'): #ohlcv 필드를 가지고 있지 않으면 생성
            self._opt10016 = {'종목코드': [], '종목명': [], '현재가': [], '전일대비': [], '등락률': [], '거래량': [],
                              '전일거래량대비율': [], '매도호가': [], '매수호가': [], '고가': [], '저가': []}

        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            for key in self._opt10016.copy().keys():
                if key in ('종목코드', '종목명'):
                    self._opt10016[key].append(self._comm_get_data(trcode, "", rqname, i, key))
                else:
                    data = self._comm_get_data(trcode, "", rqname, i, key)
                    if data.startswith('+'):
                        data = data.lstrip('+')
                    self._opt10016[key].append(float(data))

    def _request_limit_high_low(self, rqname, trcode):
        """
        신고/저가요청시 호출되는 메소드
        """
        if not hasattr(self, '_opt10017'): #ohlcv 필드를 가지고 있지 않으면 생성
            self._opt10017 = {'종목코드': [], '종목명': [], '현재가': [], '전일대비': [], '등락률': [], '거래량': [],
                              '전일거래량': [], '매도호가': [], '매수호가': [], '매도잔량': [], '매수잔량': []}

        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            for key in self._opt10017.copy().keys():
                if key in ('종목코드', '종목명'):
                    self._opt10017[key].append(self._comm_get_data(trcode, "", rqname, i, key))
                else:
                    data = self._comm_get_data(trcode, "", rqname, i, key)
                    if data.startswith('+'):
                        data = data.lstrip('+')
                    self._opt10017[key].append(float(data))

    def _request_deposit_detail(self, rqname, trcode):
        """
        예수금상세현황요청시 호출되는 메소드

        Parameters
        -----------------------
        rqname: string
        trcode: string
        """

        deposit = int(change_format(self._comm_get_data(trcode, "", rqname, 0, "예수금")))
        d1_deposit = int(change_format(self._comm_get_data(trcode, "", rqname, 0, "d+1추정예수금")))
        d2_deposit = int(change_format(self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")))

        withdrawable = int(change_format(self._comm_get_data(trcode, "", rqname, 0, "출금가능금액")))
        d1_withdrawable = int(change_format(self._comm_get_data(trcode, "", rqname, 0, "d+1출금가능금액")))
        d2_withdrawable = int(change_format(self._comm_get_data(trcode, "", rqname, 0, "d+2출금가능금액")))
        self._deposit = {"예수금": deposit, "d+1추정예수금": d1_deposit, "d+2추정예수금": d2_deposit, '출금가능금액': withdrawable,
                        'd+1출금가능금액': d1_withdrawable, 'd+2출금가능금액': d2_withdrawable}

    def _request_today_realized_pnl(self, rqname, trcode):
        """
        당일실현손익상세요청시 호출되는 메소드

        Parameters
        -----------------------
        rqname: string
        trcode: string
        """

        data_cnt = self._get_repeat_cnt(trcode, rqname)
        item_list = ('종목코드', '종목명', '체결량', '매입단가', '체결가',
                    '당일매도손익', '당일매매수수료', '당일매매세금', '손익률')

        self.today_realized_pnl = self._comm_get_data(trcode, "", rqname, 0, '당일실현손익')

        self.today_realized_pnl_list = []

        for i in range(data_cnt):
            temp_dict = {}
            for item in item_list:
                if item in ['종목코드', '종목명']:
                    temp_dict[item] = self._comm_get_data(trcode, "", rqname, i, item)
                else:
                    temp_dict[item] = to_float(change_format(self._comm_get_data(trcode, "", rqname, i, item)))
            self.today_realized_pnl_list.append(temp_dict)
    
    def _request_trading_info(self, rqname, trcode):
        """
        계좌별 주문체결 내역 요청시 호출되는 메서드

        parameters
        -----------------------
        rqname: str
        trcode: str
        """
        
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        item_list = ('주문번호','종목번호','매매구분','신용구분','주문수량','주문단가','확인수량','접수구분','반대여부','주문시간',
                        '원주문','종목명','주문구분','대출일','체결수량','체결단가','주문잔량','통신구분','정정취소','확인시간')
        
        self.today_trading_info = []
        for i in range(data_cnt):
            temp_dict = {}
            for item in item_list:
                data = self._comm_get_data(trcode, "", rqname, i, item)
                temp_dict[item]=data
            self.today_trading_info.append(temp_dict)



    def _request_unexcuted(self, rqname, trcode):
        """
        실시간미체결정보요청시 호출되는 메소드

        Parameters
        -----------------------
        rqname: str
        trcode: str
        """

        data_cnt = self._get_repeat_cnt(trcode, rqname)


        item_list = ('계좌번호', '주문번호', '관리사번', '종목코드',
                     '업무구분', '주문상태', '종목명', '주문수량',
                     '주문가격', '미체결수량', '체결누계금액', '원주문번호',
                     '주문구분', '매매구분', '시간', '체결번호', '체결가',
                     '체결량',' 현재가', '매도호가', '매수호가', '단위체결가',
                     '단위체결량', '당일매매수수료', '당일매매세금', '개인투자자')

        self.current_orders = []

        for i in range(data_cnt):
            temp_dict = {}
            for item in item_list:
                if item in ['종목코드', '종목명']:
                    temp_dict[item] = self._comm_get_data(trcode, "", rqname, i, item)
                else:
                    temp_dict[item] = change_format(self._comm_get_data(trcode, "", rqname, i, item))
            self.current_orders.append(temp_dict)


    def _request_price_info(self, rqname, trcode):
        """
        주식/업종 일봉차트조회요청시 호출되는 메소드

        Parameters
        -----------------------
        rqname: str
        trcode: str
        """
        if not hasattr(self, 'ohlcv'): #ohlcv 필드를 가지고 있지 않으면 생성
            self.ohlcv = {
            'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []
            }
        
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        item_list = {'일자': 'date', '체결시간': 'date', '시가': 'open', '고가': 'high',
                     '저가': 'low', '현재가': 'close', '거래량': 'volume'}
        for i in range(data_cnt):
            for key, item in item_list.items():
                if key == '일자':
                    if not trcode == 'opt10080':
                        self.ohlcv[item].append(datetime.strptime(self._comm_get_data(trcode, "", rqname, i, key), '%Y%m%d'))
                elif key == '체결시간':
                    if trcode == 'opt10080':
                        self.ohlcv[item].append(datetime.strptime(self._comm_get_data(trcode, "", rqname, i, key), '%Y%m%d%H%M%S'))
                elif key == '일자':
                    if trcode == 'opt10082':
                        self.ohlcv[item].append(datetime.strptime(self._comm_get_data(trcode, "", rqname, i, key), '%Y%m%d'))
                elif key == '일자':
                    if trcode == 'opt10083':
                        self.ohlcv[item].append(datetime.strptime(self._comm_get_data(trcode, "", rqname, i, key), '%Y%m%d'))
                else:
                    self.ohlcv[item].append(round(float(self._comm_get_data(trcode, "", rqname, i, key)), 1))

    def _request_account_balance(self, rqname, trcode):
        """
        계좌평가잔고내역요청시 호출되는 메소드

        Parameters
        -----------------------
        rqname: str
        trcode: str

        """

        self.account_balance = {}
        item_list = ['총매입금액', '총평가금액', '총평가손익금액', '총수익률(%)', '추정예탁자산',
                        '총대출금', '총융자금액', '총대주금액', '조회건수']
        for item in item_list:
            if item == '조회건수':
                self.account_balance[item] = int(change_format(self._comm_get_data(trcode, "", rqname, 0, item)))
            else:
                self.account_balance[item] = to_float(change_format(self._comm_get_data(trcode, "", rqname, 0, item)))

        if not hasattr(self, 'portfolio_positions'):
            self.portfolio_positions = {}

        data_cnt = self._get_repeat_cnt(trcode, rqname)

        item_list = ('종목명', '보유수량', '매입가', '현재가',
                     '평가손익', '수익률(%)', '전일종가', '매매가능수량',
                     '전일매수수량', '전일매도수량', '금일매수수량', '금일매도수량',
                     '매입금액', '매입수수료', '평가금액', '평가수수료', '세금', '수수료합',
                     '보유비중(%)', '신용구분', '신용구분명', '대출일')
        for i in range(data_cnt):
            temp_dict = {}
            code = self._comm_get_data(trcode, "", rqname, i, '종목번호')[1:] #remove A
            for item in item_list:
                if item == '종목명':
                    temp_dict[item] = self._comm_get_data(trcode, "", rqname, i, item)
                else:
                    if item in ('신용구분', '신용구분명', '대출일'):
                        temp_dict[item] = self._comm_get_data(trcode, "", rqname, i, item)
                    if item in ('보유수량', '매매가능수량', '전일매수수량', '전일매도수량', '금일매수수량', '금일매도수량'):
                        temp_dict[item] = int(change_format(self._comm_get_data(trcode, "", rqname, i, item)))
                    else:
                        temp_dict[item] = to_float(change_format(self._comm_get_data(trcode, "", rqname, i, item)))
            self.portfolio_positions[code] = temp_dict


    def _get_chejan_data(self, fid):
        """
        주문 접수/확인시 체결잔고 데이터를 반환하는 메소드

        Parameters
        ---------------------
        fid: int - 체결잔고 아이템 fid

        """
        ret = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        OnReceiveChejanData이벤트 발생시 호출되는 메소드
        self.chejan에 체결정보를 업데이트함

        Parameters
        ------------------
        gubun: str
            체결구분 0:주문체결통보, 1:잔고통보, 3:특이신호
        item_cnt: int
            아이템 개수
        fid_list: str
        """

        fid_dict = collections.OrderedDict({
                    '원주문번호': 904, '주문번호': 9203 , '주문구분': 905, '종목코드': 9001, '종목명': 302,
                    '주문수량': 900, '주문가격': 901, '미체결수량': 902, '주문/체결시간': 908,'체결가': 910, 
                    '체결량': 911, '매매구분': 906
                    })

        temp_dict = {}
        for key, fid in fid_dict.items():
            if key == '주문구분':
                ordertype = self._get_chejan_data(fid).strip()
                temp_dict[key] = ordertype
            else:
                if key in ['주문수량', '미체결수량', '체결량']:
                    value = self._get_chejan_data(fid).strip()
                    if value == '':
                        value = 0

                    if '매도' in ordertype:
                        temp_dict[key] = -int(value)
                    elif '매수' in ordertype:
                        temp_dict[key] = int(value)

                elif key == '종목코드':
                    code = self._get_chejan_data(fid).strip()
                    if code.startswith('A'):
                        code = code[1:]
                        temp_dict[key] = code
                elif key in ['주문가격, 체결가']:
                    temp_dict[key] = float(self._get_chejan_data(fid).strip())
                else:
                    temp_dict[key] = self._get_chejan_data(fid).strip() # 에러날수도

        if not temp_dict['주문/체결시간'] == '':
            self.chejan_received.emit(temp_dict)



    """
    -------------------
    | 실시간조회 메소드 |
    -------------------
    """

    def request_real_data(self, codes, add_list=False):

        if add_list:
            add_list = '1'
        else:
            add_list = '0'
        self.real = RealTimeMannager(self.ocx, codes, add_list)
        self.real.start()

    def _receive_real_data(self, code, real_type, real_data):
        """
        실시간데이터를 받은 시점을 알려준다.

        입력값
        code: str
            - 종목코드
        realType: str
            - 리얼타입
        realData: str
            - 실시간 데이터전문
        """
        if real_type == '주식체결':
            if not hasattr(self, 'real_data'):
                self.real_data = {}
            temp_dict = {}
            temp_dict['체결시간'] = self._get_comm_real_data(real_type, 20)
            temp_dict['현재가'] = self._get_comm_real_data(real_type, 10)
            temp_dict['전일대비'] = self._get_comm_real_data(real_type, 11)
            temp_dict['등락율'] = self._get_comm_real_data(real_type, 12)
            temp_dict['(최우선)매도호가'] = self._get_comm_real_data(real_type, 27)
            temp_dict['(최우선)매수호가'] = self._get_comm_real_data(real_type, 28)
            temp_dict['거래량'] = self._get_comm_real_data(real_type, 15)
            temp_dict['누적거래량'] = self._get_comm_real_data(real_type, 13)
            temp_dict['누적거래대금'] = self._get_comm_real_data(real_type, 14)
            temp_dict['시가'] = self._get_comm_real_data(real_type, 16)
            temp_dict['고가'] = self._get_comm_real_data(real_type, 17)
            temp_dict['저가'] = self._get_comm_real_data(real_type, 18)
            temp_dict['전일대비기호'] = self._get_comm_real_data(real_type, 25)
            temp_dict['전일거래량대비(계약,주)'] = self._get_comm_real_data(real_type, 26)
            temp_dict['거래대금증감'] = self._get_comm_real_data(real_type, 29)
            temp_dict['전일거래량대비(비율)'] = self._get_comm_real_data(real_type, 30)
            temp_dict['거래회전율'] = self._get_comm_real_data(real_type, 31)
            temp_dict['거래비용'] = self._get_comm_real_data(real_type, 32)
            temp_dict['체결강도'] = self._get_comm_real_data(real_type, 228)
            temp_dict['시가총액(억)'] = self._get_comm_real_data(real_type, 311)
            temp_dict['장구분'] = self._get_comm_real_data(real_type, 290)
            self.real_data[code] = temp_dict
            #print(self.real_data)


    def _get_comm_real_data(self, real_type, fid):
        """
        실시간데이터를 반환하는 메소드

        Paramenters
        ------------------------
        real_type: str
        fid: int

        Returns
        ------------------------
        value: str
        """

        assert (isinstance(real_type, str)
                and isinstance(fid, int))

        value = self.ocx.dynamicCall("GetCommRealData(QString, int)", real_type, fid)

        return value

    """
     -------------------
    | 변수 초기화 메소드 |
     -------------------
    """

    def reset_ohlcv(self):
        self.ohlcv = {
        'date': [], 'open': [], 'high': [], 'low': [], 'close': [],'volume': []
        }

    def reset_opt10016(self): #신고저가
        self._opt10016 = {'종목코드': [], '종목명': [], '현재가': [], '등락률': [], '거래량': [],
                          '전일거래량대비율': [], '매도호가': [], '매수호가': [], '고가': [], '저가': []}

    def reset_opt10017(self): #상하한가
        self._opt10017 = {'종목코드': [], '종목명': [], '현재가': [], '전일대비': [], '등락률': [], '거래량': [],
                          '전일거래량': [], '매도호가': [], '매수호가': [], '매도잔량': [], '매수잔량': []}


class RealTimeMannager(QThread):

    def __init__(self, ocx, codes, add_list):
        super().__init__()
        self.ocx = ocx
        self.codes = codes
        self.add_list = add_list

    def run(self):

        if not self.ocx.dynamicCall("GetConnectState()"):
            raise Exception("서버에 연결되어있지 않습니다.")

        if isinstance(self.codes, list):
            codes = ';'.join(self.codes)

        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                         '0120', codes, '10', self.add_list)
        self.real_event = QEventLoop()
        self.real_event.exec_()

    def __del__(self):
        self.wait()
