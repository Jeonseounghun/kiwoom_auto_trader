import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *


class Kiwoom_port(QAxWidget):
    def __init__(self):
        super().__init__()
        
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.detail_account_info_event_loop = QEventLoop()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self.trdata_slot)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        for idx, code in enumerate(code_list):

            self.dynamicCall("DisconnectRealData(QString)","4000" )
            print("%s / %s : KOSDAQ Stock Code : %s updating..." % (idx + 1, len(code_list), code))
            self.day_kiwoom_db(code=code)

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        QTest.qWait(5000)

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("CommRqData(QString, QString, int, QString)" ,"주식현재가", "opt10001", 0, "4000")

        self.detail_account_info_event_loop.exec_()

    
    
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if "주식현재가" == sRQName:
            try:    
                stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "현재가")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목명")
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
                trade = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "거래량")
                
                stock_price = abs(int(stock_price))
                code_name = code_name.strip()
                code = code.strip()
                trade = int(trade)

                if (5000>= stock_price and stock_price>=500) and (trade > 100000):
                    
                    stock_price= str(stock_price)
                    f = open("500~5000.txt", "a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code_name,stock_price, code))
                    f.close()

                    print("입력완료")
                    self.detail_account_info_event_loop.exit()
            except:
                pass
            # elif (3000>= stock_price and stock_price>=2001) and (trade > 100000):
                
            #     stock_price= str(stock_price)
            #     f = open("2000.txt", "a", encoding="utf8")
            #     f.write("%s\t%s\t%s\n" % (code_name,stock_price, code))
            #     f.close()

            #     print("입력완료")
            #     self.detail_account_info_event_loop.exit()

            # elif (4000>= stock_price and stock_price>=3001) and (trade > 100000):
                
            #     stock_price= str(stock_price)
            #     f = open("3000.txt", "a", encoding="utf8")
            #     f.write("%s\t%s\t%s\n" % (code_name,stock_price, code))
            #     f.close()

            #     print("입력완료")
            #     self.detail_account_info_event_loop.exit()

            # elif (9000>= stock_price and stock_price>= 4001) and (trade > 100000):
                
            #     stock_price= str(stock_price)
            #     f = open("4000.txt", "a", encoding="utf8")
            #     f.write("%s\t%s\t%s\n" % (code_name,stock_price, code))
            #     f.close()

            #     print("입력완료")
            #     self.detail_account_info_event_loop.exit()


            else:
                print("pass")
                pass
                self.detail_account_info_event_loop.exit()


 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom_port()
    kiwoom.comm_connect()
    
    code_list = kiwoom.get_code_list_by_market('10')
    code_list = kiwoom.get_code_list_by_market('0')
    