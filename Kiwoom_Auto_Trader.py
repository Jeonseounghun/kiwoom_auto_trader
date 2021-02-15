from PyQt5.QtTest import *
import os
from config.kiwoomType import *
import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import threading
import time
from portfoilo import *


class Mainwindow(QMainWindow):

    ##### 메인화면 영역
    ##########################################################################
    def __init__(self, parent=None):
        super(Mainwindow, self).__init__(parent)
        #### 잔고 및 매매용 계좌 리스트
        self.item_output = []
        self.portfolio_stock_dict = {}
        self.account_stock_dict = {}
        self.profit_stock = []
        self.jango_dict = {}
        self.deposit = 0

        self.realtype = RealType()
        self.today_day = datetime.today()
        self.make_profit_list()

        #### 이벤트 루프
        self.detail_account_info_event_loop = QEventLoop()

        ##### 상태표시줄 생성
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        #### 스크린번호
        self.my_screen_info = "2000"
        self.screen_calculation_stock = "4000"
        self.screen_real_stock = "5000"  # 종목별로 할당할 스크린 번호
        self.screen_meme_stock = "6000"  # 종목별 할당할 주문용 스크린 번호
        self.screen_start_stop_num = "1000"
        #####################################

        ##### 위젯 창 연결

        self.mywidget = MyWindow(self)
        self.setCentralWidget(self.mywidget)
        self.mywidget.button_1.clicked.connect(self.portfolio_exe)

        ##### 메인창 이름설정 및 크기설정
        self.setWindowTitle("Kiwoom_Auto_Trader")
        self.setGeometry(300, 300, 1000, 600)

        ##### 메인창을 중앙에 위치 == 아래에 함수로 정의 되어있음
        self.center()

        ##### 타이머 설정 1 - 상태표시줄 현재시간
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        #####################################

        #### 키움API 가동
        self.kiwoom()

    def portfolio_exe(self):
        # os.startfile('portfolio.bat')
        self.item_output = []
        self.detail_account_info1()
        self.detail_account_info2()

    #### 수익 종목을 담을 파일 생성
    def make_profit_list(self):
        self.f = open("./data/profit.txt", "a", encoding="utf8")
        self.f.close()

        self.f = open("./data/jango.txt", "a", encoding="utf8")
        self.f.close()

        f = open("./data/jango.txt", "r", encoding="utf8")
        lines = f.readlines()
        for line in lines:
            scode = line.split("\n")[0]
            self.jango_dict.update({scode: {}})

        f.close()

    #### 화면을 중앙에 배치
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    #### 스크림번호 셋팅
    def screen_number_setting(self):
        current_time = QTime.currentTime()
        screen_overwrite = []

        # 계좌에 있는 종목
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 조건 만족 종목
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린번호 할당
        cnt = 0

        for code in screen_overwrite:
            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update(
                    {"스크린번호": str(self.screen_real_stock)}
                )
                self.portfolio_stock_dict[code].update(
                    {"주문용스크린번호": str(self.screen_meme_stock)}
                )

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update(
                    {
                        code: {
                            "스크린번호": str(self.screen_real_stock),
                            "주문용스크린번호": str(self.screen_meme_stock),
                        }
                    }
                )

            cnt += 1

    #### 포트폴리오를 읽어오기
    def read_code(self):
        if os.path.exists("./data/portfolio.txt"):
            f = open("./data/portfolio.txt", "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")

                    code_name = ls[0]

                    stock_price = ls[1]
                    scode = ls[2].split("\n")[0]

                    self.portfolio_stock_dict.update(
                        {scode: {"종목명": code_name, "현재가": stock_price}}
                    )
            f.close()

    #### 창을 닫을떄 호출하는 부분
    def closeEvent(self, QCloseEvent):
        re = QMessageBox.question(
            self, "종료 확인", "종료 하시겠습니까?", QMessageBox.Yes | QMessageBox.No
        )

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()

    ##### 상태표시줄에 들어갈 현재시간
    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        self.current_time = text_time
        time_msg = "현재시간 : " + text_time

        self.statusbar.showMessage("서버 연결 중 | " + time_msg)

    def timeout2(self):
        self.kiwoom.OnEventConnect.connect(self.detail_account_info1)  # 예수금 정보 요청
        self.kiwoom.OnEventConnect.connect(self.detail_account_info2)  # 잔고정보 요청

    ##########################################################################
    ##### openAPI구동 영역
    ##########################################################################
    def kiwoom(self):
        ##### 로그인 영역
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.logon()

        ##### 이벤트실행 실행
        self.kiwoom.OnEventConnect.connect(self.event_connect)  # 로그인
        self.kiwoom.OnReceiveTrData.connect(self.trdata_slot)  # 예수금 및잔고 정보 수신
        self.kiwoom.OnReceiveRealData.connect(self.realdata_slot)
        self.kiwoom.OnReceiveChejanData.connect(self.chejan_slot)
        self.kiwoom.OnEventConnect.connect(self.account)  # 계좌정보
        self.kiwoom.OnEventConnect.connect(self.detail_account_info1)  # 예수금 정보 요청
        self.kiwoom.OnEventConnect.connect(self.detail_account_info2)  # 잔고정보 요청

    #### 로그인하는 부분
    def logon(self):
        self.kiwoom.dynamicCall("CommConnect()")

    ##### CommConnect()호출 후 반환값이 리턴 되면 UI에 text_edit 표출
    def event_connect(self, err_code):
        if err_code == 0:
            print("로그인성공")
            self.mywidget.text_edit.append("로그인 성공")

        else:
            self.mywidget.text_edit.append("로그인 실패")

    ##### 계좌정보 가저오는 함수
    def account(self):
        account_list = self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"])
        self.mywidget.text_edit.append("계좌번호: " + account_list.rstrip(";"))
        self.account_num = account_list.split(";")[0]

    ##### 예수금 정보 요청 함수
    def detail_account_info1(self, sPrevNext="0"):
        self.kiwoom.dynamicCall(
            "SetInputValue(QString, QString)", "계좌번호", self.account_num
        )
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.kiwoom.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "예수금상세현황요청",
            "opw00001",
            sPrevNext,
            self.my_screen_info,
        )

        self.detail_account_info_event_loop.exec_()

    ##### 계좌평가잔고 정보 요청 함수
    def detail_account_info2(self, sPrevNext="0"):
        self.kiwoom.dynamicCall(
            "SetInputValue(QString, QString)", "계좌번호", self.account_num
        )
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.kiwoom.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "계좌평가잔고내역요청",
            "opw00018",
            sPrevNext,
            self.my_screen_info,
        )

        ### 루프 생성
        self.detail_account_info_event_loop.exec_()

    ##### 계좌 정보 수신 함수
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

        ##### 예수금 및 출금가능금액
        if sRQName == "예수금상세현황요청":
            ##### 예수금 데이터 반환
            self.deposit = self.kiwoom.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                sTrCode,
                sRQName,
                0,
                "예수금",
            )

            ##### 출금가능 데이터 반환
            output_deposit = self.kiwoom.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                sTrCode,
                sRQName,
                0,
                "출금가능금액",
            )

            ##### 예수금에 필요없는 숫자 삭제하고 원화 표출양식으로 변환
            self.deposit = self.change_format(self.deposit)
            output_deposit = self.change_format(output_deposit)

            ##### 결과값 표출
            deposit = QTableWidgetItem(self.deposit)
            deposit.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 0, deposit)
            output_deposit = QTableWidgetItem(output_deposit)
            output_deposit.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 6, output_deposit)

            self.detail_account_info_event_loop.exit()

        ##### 매입금액 등 현황 수신
        elif sRQName == "계좌평가잔고내역요청":

            ##### 잔고현황 반환
            total_purchsase = self.kiwoom.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                sTrCode,
                sRQName,
                0,
                "총매입금액",
            )
            total_eval_price = self.kiwoom.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                sTrCode,
                sRQName,
                0,
                "총평가금액",
            )
            total_eval_profit_loss = self.kiwoom.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                sTrCode,
                sRQName,
                0,
                "총평가손익금액",
            )
            total_earning_rate = str(
                (
                    float(
                        self.kiwoom.dynamicCall(
                            "GetCommData(QString, QString, int, QString)",
                            sTrCode,
                            sRQName,
                            0,
                            "총수익률(%)",
                        )
                    )
                )
                / 100
            )
            estimated_deposit = self.kiwoom.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                sTrCode,
                sRQName,
                0,
                "추정예탁자산",
            )

            self.buy_money = round(int(estimated_deposit) * 0.006)

            ##### 잔고현황 결과값 숫자형태 변환
            total_purchsase = self.change_format(total_purchsase)
            total_eval_price = self.change_format(total_eval_price)
            total_eval_profit_loss = self.change_format(total_eval_profit_loss)
            total_earning_rate = self.change_format(total_earning_rate)
            estimated_deposit = self.change_format(estimated_deposit)

            ##### 테이블위젯에 결과값 넣기
            total_purchsase = QTableWidgetItem(total_purchsase)
            total_purchsase.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 2, total_purchsase)

            total_eval_price = QTableWidgetItem(total_eval_price)
            total_eval_price.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 3, total_eval_price)

            total_eval_profit_loss = QTableWidgetItem(total_eval_profit_loss)
            total_eval_profit_loss.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 4, total_eval_profit_loss)

            total_earning_rate = QTableWidgetItem(total_earning_rate)
            total_earning_rate.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 5, total_earning_rate)

            estimated_deposit = QTableWidgetItem(estimated_deposit)
            estimated_deposit.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 1, estimated_deposit)
            ###############################################################

            ##### 종목현황 반환
            rows = self.kiwoom.dynamicCall(
                "GetRepeatCnt(QString, QString)", sTrCode, sRQName
            )

            ##### 종목현황 반환된 값에서 원하는 값 추출
            for i in range(rows):

                code = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "종목번호",
                )
                code = code.strip()[1:]
                print(code)

                self.account_stock_dict.update({code: {}})

                code_name = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "종목명",
                )
                stock_quantity = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "보유수량",
                )
                buy_price = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "매입가",
                )
                learn_rate = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "수익률(%)",
                )
                current_price = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "현재가",
                )
                total_chegual_price = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "매입금액",
                )
                possible_quantity = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "매매가능수량",
                )
                eval_profit_loss = self.kiwoom.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    sTrCode,
                    sRQName,
                    i,
                    "평가손익",
                )

                code_name = code_name.strip()
                if stock_quantity == "":
                    pass
                else:
                    stock_quantity = int(stock_quantity)
                    self.account_stock_dict[code].update({"보유수량": stock_quantity})
                if buy_price == "":
                    pass
                else:
                    buy_price = int(buy_price)
                    self.account_stock_dict[code].update({"매입가": buy_price})
                if learn_rate == "":
                    pass
                else:
                    learn_rate = (float(learn_rate)) / 100
                    self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                if current_price == "":
                    pass
                else:
                    current_price = int(current_price.strip())
                    self.account_stock_dict[code].update({"현재가": current_price})
                if eval_profit_loss == "":
                    pass
                else:
                    eval_profit_loss = int(eval_profit_loss)
                    self.account_stock_dict[code].update({"평가손익": eval_profit_loss})
                if total_chegual_price == "":
                    pass
                else:
                    total_chegual_price = int(total_chegual_price)
                    self.account_stock_dict[code].update({"매입금액": total_chegual_price})

                if possible_quantity == "":
                    pass
                else:
                    possible_quantity = int(possible_quantity)
                    self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

                self.account_stock_dict[code].update({"종목명": code_name})
                self.item_output.append(
                    [
                        code_name,
                        str(stock_quantity),
                        str(buy_price),
                        str(current_price),
                        str(eval_profit_loss),
                        str(learn_rate),
                    ]
                )
            ###############################################################
            ##### 종목을 UI에 띄우기
            ##### item의 갯수세고 띄워줄 테이블에 로우를 만듬
            item_count = len(self.item_output)
            self.mywidget.tableWidget_item.setRowCount(item_count)
            for j in range(0, item_count):
                for i, k in enumerate(self.item_output[j]):
                    rate = float(self.item_output[j][5])
                    item = QTableWidgetItem(k)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    self.mywidget.tableWidget_item.setItem(j, i, item)
                    if rate > 0:
                        item.setForeground(QBrush(QColor("red")))
                    else:
                        item.setForeground(QBrush(QColor("blue")))

            if sPrevNext == "2":  # 값이 "2"이면 다음 조회항목이 있다는 뜻으로 종목조회 계속
                self.detail_account_info2(sPrevNext="2")

            else:

                #### 저장된 종목 불러오기
                self.read_code()
                self.screen_number_setting()  # 스크린 번호를 할당
                self.kiwoom.dynamicCall(
                    "SetRealReg(QString,QString,QString,QString)",
                    self.screen_start_stop_num,
                    "",
                    self.realtype.REALTYPE["장시작시간"]["장운영구분"],
                    "0",
                )
                cnt = 1

                #### 실시간 스크린번호 배분
                for code in self.portfolio_stock_dict.keys():
                    screen_num = self.portfolio_stock_dict[code]["스크린번호"]
                    fids = self.realtype.REALTYPE["주식체결"]["체결시간"]
                    if code:
                        self.kiwoom.dynamicCall(
                            "SetRealReg(QString,QString,QString,QString)",
                            screen_num,
                            code,
                            fids,
                            "1",
                        )
                        print(
                            "스크린번호 배분 완료 %s[코드 : %s, 번호 : %s]" % (cnt, code, screen_num)
                        )

                        cnt += 1
                    else:
                        pass

                ##### 로그현황에 결과 띄우기
                self.mywidget.text_edit.append("잔고현황 실시간조회 실행")

                ##### 루프 종료
                self.detail_account_info_event_loop.exit()

    #### 리얼 데이터를 받아 주식 매수 & 매도하는 슬롯
    def realdata_slot(self, sCode, sRealType, sRealData):

        #### 서버시간을 받아 장 시작 유무를 호출
        if sRealType == "장시작시간":

            fid = self.realtype.REALTYPE[sRealType]["장운영구분"]
            value = self.kiwoom.dynamicCall("GetCommRealData(QString,int)", sCode, fid)

            if value == "0":
                self.mywidget.text_edit.append("장 시작 전")

            elif value == "3":
                self.mywidget.text_edit.append("장 시작 ")

            elif value == "2":
                self.mywidget.text_edit.append("장  종료 종가매매시작")
                os.remove("./data/jango.txt")
                os.remove("./data/profit.txt")

            elif value == "4":

                self.mywidget.text_edit.append("종가매매 종료")

        #### 틱체결이 이루어지면 종목을 호출
        elif sRealType == "주식체결":

            current_time = QTime.currentTime()
            text_time = current_time.toString("hh:mm:ss")

            a = self.kiwoom.dynamicCall(
                "GetCommRealData(QString,int)",
                sCode,
                self.realtype.REALTYPE[sRealType]["체결시간"],
            )
            b = self.kiwoom.dynamicCall(
                "GetCommRealData(QString,int)",
                sCode,
                self.realtype.REALTYPE[sRealType]["현재가"],
            )
            b = abs(int(b))
            c = self.kiwoom.dynamicCall(
                "GetCommRealData(QString,int)",
                sCode,
                self.realtype.REALTYPE[sRealType]["전일대비"],
            )
            c = abs(int(c))
            d = self.kiwoom.dynamicCall(
                "GetCommRealData(QString,int)",
                sCode,
                self.realtype.REALTYPE[sRealType]["등락율"],
            )
            d = float(d)

            if sCode not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({sCode: {}})

            self.portfolio_stock_dict[sCode].update({"체결시간": a})
            self.portfolio_stock_dict[sCode].update({"현재가": b})
            self.portfolio_stock_dict[sCode].update({"전일대비": c})
            self.portfolio_stock_dict[sCode].update({"등락률": d})

            if sCode in self.account_stock_dict.keys():
                self.account_stock_dict[sCode].update({"현재가": b})

            #### 매도조건
            if (
                sCode in self.account_stock_dict.keys()
                and self.account_stock_dict[sCode]["매입가"] > 0
            ):

                meme = self.account_stock_dict[sCode]

                meme_rate = ((b - meme["매입가"]) / meme["매입가"]) * 100
                meme_rate = round(meme_rate, 2)

                stock_order = (self.buy_money * 0.2) // b

                if meme["매매가능수량"] > 0 and (meme_rate > 3.0):

                    order_sucess = self.kiwoom.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [
                            "매도요청",
                            self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                            self.account_num,
                            2,
                            sCode,
                            meme["매매가능수량"],
                            0,
                            self.realtype.SENDTYPE["거래구분"]["시장가"],
                            "",
                        ],
                    )

                    if order_sucess == 0:
                        self.mywidget.text_edit3.append(
                            "[매도주문]["
                            + text_time
                            + "][수익률 : %s] %s 매도주문 성공"
                            % (meme_rate, self.account_stock_dict[sCode]["종목명"])
                        )

                        self.f = open("./data/profit.txt", "a", encoding="utf8")
                        info = "%s\t%s\n" % (
                            self.account_stock_dict[sCode]["종목명"],
                            meme_rate,
                        )
                        self.f.write(info)
                        self.f.close()

                        self.f = open("./data/profit.txt", "r", encoding="utf8")
                        lines = self.f.readlines()
                        for line in lines:
                            if line != "":
                                ls = line.split("\t")

                                code_name = ls[0]
                                meme_rate = ls[1].strip()
                                if [
                                    str(code_name),
                                    str(meme_rate),
                                ] in self.profit_stock:
                                    pass
                                else:
                                    self.profit_stock.append(
                                        [str(code_name), str(meme_rate)]
                                    )
                                    profit_count = len(self.profit_stock)
                                    for j in range(profit_count):
                                        for i, k in enumerate(self.profit_stock[j]):
                                            item = QTableWidgetItem(k)
                                            item.setTextAlignment(
                                                Qt.AlignVCenter | Qt.AlignLeft
                                            )
                                            self.mywidget.tableWidget_item2.setItem(
                                                j, i, item
                                            )
                        self.f.close()
                        del self.account_stock_dict[sCode]

                        QTest.qWait(500)

                    else:
                        self.mywidget.text_edit2.append("매도주문 실패" + text_time)
                        QTest.qWait(500)

                elif (
                    meme["매매가능수량"] > 0
                    and meme_rate < -50.0
                    and sCode not in self.jango_dict.keys()
                ):

                    order_sucess = self.kiwoom.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [
                            "매도요청",
                            self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                            self.account_num,
                            2,
                            sCode,
                            1,
                            0,
                            self.realtype.SENDTYPE["거래구분"]["시장가"],
                            "",
                        ],
                    )

                    if order_sucess == 0:
                        self.mywidget.text_edit3.append(
                            "[매도주문]["
                            + text_time
                            + "][수익률 : %s] %s 매도주문 성공"
                            % (meme_rate, self.account_stock_dict[sCode]["종목명"])
                        )

                        self.jango_dict.update({sCode: {}})
                        self.f = open("./data/profit.txt", "a", encoding="utf8")
                        info = "%s\t%s\n" % (
                            self.account_stock_dict[sCode]["종목명"],
                            meme_rate,
                        )
                        self.f.write(info)
                        self.f.close()

                        self.f = open("./data/profit.txt", "r", encoding="utf8")
                        lines = self.f.readlines()
                        for line in lines:
                            if line != "":
                                ls = line.split("\t")

                                code_name = ls[0]
                                meme_rate = ls[1].strip()
                                if [
                                    str(code_name),
                                    str(meme_rate),
                                ] in self.profit_stock:
                                    pass
                                else:
                                    self.profit_stock.append(
                                        [str(code_name), str(meme_rate)]
                                    )
                                    profit_count = len(self.profit_stock)
                                    for j in range(profit_count):
                                        for i, k in enumerate(self.profit_stock[j]):
                                            item = QTableWidgetItem(k)
                                            item.setTextAlignment(
                                                Qt.AlignVCenter | Qt.AlignLeft
                                            )
                                            self.mywidget.tableWidget_item2.setItem(
                                                j, i, item
                                            )
                        self.f.close()

                        QTest.qWait(500)

                    else:
                        self.mywidget.text_edit2.append("매도주문 실패" + text_time)
                        QTest.qWait(500)

                #### 추가매수 조건

                elif (
                    meme_rate < -10
                    and (
                        self.account_stock_dict[sCode]["매입가"]
                        * self.account_stock_dict[sCode]["매매가능수량"]
                    )
                    < self.buy_money
                    and sCode not in self.jango_dict.keys()
                ):

                    order_succes = self.kiwoom.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [
                            "매수요청",
                            self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                            self.account_num,
                            1,
                            sCode,
                            stock_order,
                            0,
                            self.realtype.SENDTYPE["거래구분"]["시장가"],
                            "",
                        ],
                    )
                    if order_succes == 0:
                        self.mywidget.text_edit2.append(
                            "[매수주문]%s : 추가 매수주문 성공"
                            % self.account_stock_dict[sCode]["종목명"]
                            + text_time
                        )

                        f = open("./data/jango.txt", "a", encoding="utf8")
                        info = "%s\n" % sCode
                        f.write(info)
                        f.close()
                        self.jango_dict.update({sCode: {}})

                        QTest.qWait(500)
                    else:
                        self.mywidget.text_edit2.append("매수주문 실패" + text_time)
                        QTest.qWait(500)

            #### 매수조건

            elif (
                d < 0
                and sCode in self.portfolio_stock_dict.keys()
                and sCode not in self.account_stock_dict.keys()
                and sCode not in self.jango_dict.keys()
                and self.buy_money * 0.2 > self.portfolio_stock_dict[sCode]["현재가"]
            ):
                stock_order = (self.buy_money * 0.20) // b
                order_succes = self.kiwoom.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    [
                        "매수요청",
                        self.portfolio_stock_dict[sCode]["주문용스크린번호"],
                        self.account_num,
                        1,
                        sCode,
                        stock_order,
                        0,
                        self.realtype.SENDTYPE["거래구분"]["시장가"],
                        "",
                    ],
                )
                if order_succes == 0:
                    self.mywidget.text_edit2.append(
                        "[매수주문]%s : 1차 매수주문 성공"
                        % self.portfolio_stock_dict[sCode]["종목명"]
                        + text_time
                    )

                    if sCode not in self.jango_dict.keys():
                        f = open("./data/jango.txt", "a", encoding="utf8")
                        info = "%s\n" % sCode
                        f.write(info)
                        f.close()

                        self.jango_dict.update({sCode: {}})

                    QTest.qWait(500)

                else:
                    self.mywidget.text_edit2.append("매수주문 실패" + text_time)

                    QTest.qWait(500)

    ##### 숫자 표출형식 변환 1
    def change_format(self, data):
        strip_data = data.lstrip("-0")
        if strip_data == "" or strip_data == ".00":
            strip_data = "0"
        try:
            format_data = format(int(strip_data), ",d")
        except:
            format_data = format(float(strip_data))
        if data.startswith("-"):
            format_data = "-" + format_data

        return format_data

    ##### 수익률 표출형식 변환 2
    def change_format2(self, data):
        strip_data = data.lstrip("-0")

        if strip_data == "":
            strip_data = "0"

        if strip_data.startswith("."):
            strip_data = "0" + strip_data

        if data.startswith("-"):
            strip_data = "-" + strip_data

        return strip_data

    def chejan_slot(self, sGubun, nItemCnt, sFIDList):
        if int(sGubun) == 1:

            sCode = self.kiwoom.dynamicCall(
                "GetChejanData(int)", self.realtype.REALTYPE["잔고"]["종목코드"]
            )[1:]
            stock_quan = self.kiwoom.dynamicCall(
                "GetChejanData(int)", self.realtype.REALTYPE["잔고"]["보유수량"]
            )
            stock_quan = int(stock_quan)

            buy_price = self.kiwoom.dynamicCall(
                "GetChejanData(int)", self.realtype.REALTYPE["잔고"]["매입단가"]
            )
            buy_price = abs(int(buy_price))
            stock_name = self.kiwoom.dynamicCall(
                "GetChejanData(int)", self.realtype.REALTYPE["잔고"]["종목명"]
            )
            stock_name = stock_name.strip()
            self.deposit = self.kiwoom.dynamicCall(
                "GetChejanData(int)", self.realtype.REALTYPE["잔고"]["예수금"]
            )
            self.deposit = self.change_format(self.deposit)

            self.account_stock_dict.update({sCode: {}})
            self.account_stock_dict[sCode].update({"매매가능수량": stock_quan})
            self.account_stock_dict[sCode].update({"매입가": buy_price})
            self.account_stock_dict[sCode].update({"종목명": stock_name})


##########################################################################
class MyWindow(QWidget):
    def __init__(self, parent):
        super(MyWindow, self).__init__()

        ##### openAPI에서 발생하는 이벤트를 표출할 영역 생성
        self.text_edit = QTextEdit(self)
        self.text_edit.setEnabled(False)
        self.text_edit.setFixedHeight(100)

        #### 매수 및 매도 이벤트를 표출할 영역
        self.text_edit2 = QTextEdit(self)
        self.text_edit2.setEnabled(True)
        self.text_edit2.setFixedHeight(400)
        self.text_edit2.setStyleSheet("color:red;")

        self.text_edit3 = QTextEdit(self)
        self.text_edit3.setEnabled(True)
        self.text_edit3.setFixedHeight(400)
        self.text_edit3.setStyleSheet("color:blue;")

        ##### 잔고표출 영역생성
        self.tableWidget_balance = QTableWidget(self)
        balance = ["예수금(d+2)", "추정예탁자산", "총매입금", "총평가", "총손익", "총수익률", "출금가능금액"]
        #
        self.tableWidget_balance.setRowCount(1)  # 행의 갯수
        self.tableWidget_balance.setColumnCount(len(balance))

        self.tableWidget_balance.setHorizontalHeaderLabels(balance)

        self.tableWidget_balance.resizeRowsToContents()  # 행의 사이즈를 내용에 맞추어설정
        self.tableWidget_balance.setFixedWidth(700)
        self.tableWidget_balance.setFixedHeight(100)  # 위젯크기 고정
        self.tableWidget_balance.setColumnWidth(0, 100)  # 0에 위치한것 크기조정(원하는사이즈로 수정가능)
        self.tableWidget_balance.setColumnWidth(1, 100)
        self.tableWidget_balance.setColumnWidth(2, 100)
        self.tableWidget_balance.setColumnWidth(3, 100)
        self.tableWidget_balance.setColumnWidth(4, 100)
        self.tableWidget_balance.setColumnWidth(5, 100)
        self.tableWidget_balance.setColumnWidth(6, 100)

        ##### 보유종목현황 영역생성
        self.tableWidget_item = QTableWidget(self)

        item = ["종목명", "보유량", "매입가", "현재가", "평가손익", "수익률"]

        self.tableWidget_item.setColumnCount(len(item))
        self.tableWidget_item.setHorizontalHeaderLabels(item)
        # self.tableWidget_item.resizeColumnsToContents()
        self.tableWidget_item.resizeRowsToContents()

        self.tableWidget_item2 = QTableWidget(self)
        item2 = ["종목명", "수익률(%)"]
        self.tableWidget_item2.setColumnCount(len(item2))
        self.tableWidget_item2.setHorizontalHeaderLabels(item2)

        self.tableWidget_item2.resizeRowsToContents()
        self.tableWidget_item2.setRowCount(200)  # 행의 갯수

        self.tableWidget_item2.setFixedHeight(780)  # 위젯크기 고정
        self.tableWidget_item2.setColumnWidth(0, 80)  # 0에 위치한것 크기조정(원하는사이즈로 수정가능)
        self.tableWidget_item2.setColumnWidth(1, 80)  # 1에 위치한것 크기조정
        self.tableWidget_item2.setColumnWidth(1, 80)

        ##### layout 영역
        #####################################################################
        # groupbox1_1 = QGroupBox('종목현황')
        # condition1_1 = QVBoxLayout()
        # condition1_1.addWidget(self.listWidget)
        # groupbox1_1.setLayout(condition1_1)
        # groupbox1_1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        groupbox1_2 = QGroupBox("로그현황")
        condition1_2 = QVBoxLayout()
        condition1_2.addWidget(self.text_edit)

        groupbox1_2.setLayout(condition1_2)
        groupbox1_2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        groupbox1_3 = QGroupBox("수익 현황")
        condition1_3 = QVBoxLayout()

        condition1_3.addWidget(self.tableWidget_item2)
        groupbox1_3.setLayout(condition1_3)
        # groupbox1_3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        groupbox1 = QVBoxLayout()
        # groupbox1.addWidget(groupbox1_1)
        groupbox1.addWidget(groupbox1_2)
        groupbox1.addWidget(groupbox1_3)

        groupbox2 = QGroupBox("잔고 및 보유종목현황")

        condition2 = QVBoxLayout()

        condition2.addWidget(self.tableWidget_balance)
        condition2.addWidget(self.tableWidget_item)

        groupbox2.setLayout(condition2)

        groupbox4 = QGroupBox("매수 및 매도")
        condition4 = QVBoxLayout()

        self.button_1 = QPushButton("조회", self)
        self.button_1.setEnabled(True)

        condition4.addWidget(self.text_edit2)
        condition4.addWidget(self.text_edit3)
        condition4.addWidget(self.button_1)
        groupbox4.setLayout(condition4)

        sub_layout1 = QVBoxLayout()
        sub_layout1.addLayout(groupbox1)
        sub_layout1.addStretch(1)

        sub_layout2 = QVBoxLayout()
        sub_layout2.addWidget(groupbox2)

        sub_layout4 = QVBoxLayout()
        sub_layout4.addWidget(groupbox4)

        main_layout2 = QHBoxLayout()
        main_layout = QHBoxLayout()
        main_layout.addLayout(sub_layout1)
        main_layout.addLayout(sub_layout2)
        main_layout.addLayout(sub_layout4)
        main_layout.setStretchFactor(sub_layout1, 0)
        main_layout.setStretchFactor(sub_layout2, 1)
        main_layout.setStretchFactor(sub_layout4, 2)

        self.setLayout(main_layout)


##########################################################################


if __name__ == "__main__":
    data_list = ["2021-01"]
    today_day = datetime.today()
    if today_day.strftime("%Y-%m") in data_list:
        app = QApplication(sys.argv)
        mywindow = Mainwindow()
        mywindow.showMaximized()
        app.exec_()