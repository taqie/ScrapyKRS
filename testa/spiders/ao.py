# -*- coding: utf-8 -*-
import scrapy
import unicodedata
import urllib2
from fake_useragent import UserAgent
from scrapy.http.request import Request
import sqlite3
import time
import MySQLdb
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
class AoSpider(scrapy.Spider):

    name = "ao"
    allowed_domains = ["krs-online.com.pl","taqie.udl.net"]
    start_urls = ['http://www.krs-online.com.pl/phu-wodomax-krs-7440569.html']
    urls = []
    urls_used = []
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    listaMain = []
    iterator = 0

    def __init__(self):
        self.fileUrls = open('urls.txt','r+')
        self.fileUrlsUsed = open('urlsUsed.txt','r+')

        self.readUrslFromFile()
        self.db = MySQLdb.connect(host="***",user="***",passwd="**",db="***")
        self.cursor = self.db.cursor()
        self.createTables(self.cursor)
        # self.conn = sqlite3.connect('data.db')
        # self.c = self.conn.cursor()
        # self.c.execute('''CREATE TABLE IF NOT EXISTS firmy
        #                      (ID INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, nip INTEGER, regon INTEGER)''')
        # self.c.execute('''CREATE TABLE IF NOT EXISTS osoby
        #                              (ID INTEGER PRIMARY KEY AUTOINCREMENT, nip INTEGER, dane TEXT, stanowisko TEXT)''')

    def readUrslFromFile(self):
        self.urls = self.fileUrls.read().split(" ")
        self.urls_used = self.fileUrlsUsed.read().split(" ")
        self.fileUrls.close()
        self.fileUrlsUsed.close()

    def close(self,spider, reason):
        self.fileUrlsw = open('urls.txt', 'w')
        self.fileUrlsUsedw = open('urlsUsed.txt', 'w')
        for links in self.urls:
            self.fileUrlsw.write(str(links+" "))
            # self.fileUrls.write(str("\n"))

        for links in self.urls_used:
            self.fileUrlsUsedw.write(str(links+" "))
            # self.fileUrlsUsed.write(str("\n"))

        self.fileUrlsw.close()
        self.fileUrlsUsedw.close()


    def hasNipOrRegon(self,dict):
        if dict.has_key("nip:"):
            if dict.has_key("regon:"):
                pass
            else:
                dict["regon:"] = 0
        else:
            if dict.has_key("regon:"):
                dict["nip:"]=0
            else:
                dict["nip:"] = 0
                dict["regon:"] = 0
                self.logger.debug("brak klucza regon oraz nip")

    def selectIdCompanies(self,nip,regon,cursor):
        cursor.execute("SELECT * FROM companies WHERE nip="+str(nip)+" OR regon="+str(regon)+"")
        rows = cursor.fetchall()
        for row in rows:
            self.logger.debug("id company = "+str(row[0]))
            return row[0]
    def companyExist(self,nip, regon, cursor):
        cursor.execute("SELECT * FROM companies WHERE nip=" + str(nip) + "")
        rows = cursor.fetchall()
        for row in rows:
            self.logger.debug("ROWWWWWWWWWWWWWWWWWWWWWWWWWw"+str(row[1]))
            if row[1] == int(nip) or row[2] == int(regon):
                return True
            else:
                return False

    def addRekordsToMembers(self,dictCompanie, cursor):
        idCompanies = self.selectIdCompanies(dictCompanie["nip:"],dictCompanie["regon:"],cursor)
        for i in dictCompanie["members"]:
            if i["nazwisko"] == "brak danych":
                pass
            else:
                listPersonalData = i["nazwisko"].split(" ")
                if len(listPersonalData) >=3:
                    pass
                else:
                    listPersonalData.append(" ")

                cursor.execute("INSERT INTO members (idCompanies,name,midName,surName,jobFunction) VALUES ('"+str(idCompanies)+"','"+str(listPersonalData[1])+"','"+str(listPersonalData[2])+"','"+str(listPersonalData[0])+"','"+str(i["funkcja"])+"')")
                self.db.commit()

    def addRekordsToCompanies(self, dictCompanie, cursor):
        isExist = self.companyExist(dictCompanie["nip:"],dictCompanie["regon:"],cursor)
        if isExist:
            pass
        else:
            cursor.execute("INSERT INTO companies (nip,regon,nameCompanies) VALUES ('"+str(dictCompanie["nip:"])+"',"
                           "'"+str(dictCompanie["regon:"])+"',"
                           "'"+str(dictCompanie["firma"])+"')")
            self.db.commit()
            self.addRekordsToMembers(dictCompanie, self.cursor)

    def createTables(self, cursor):
        cursor.execute("CREATE TABLE IF NOT EXISTS companies (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY ,"
                       "nip BIGINT NOT NULL,"
                       "regon BIGINT NOT NULL,"
                       "nameCompanies VARCHAR(1000) NOT NULL)")

        cursor.execute("CREATE TABLE IF NOT EXISTS members (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY ,"
                       "idCompanies INT NOT NULL,"
                       "name VARCHAR(100) NOT NULL,"
                       "midName VARCHAR(100),"
                       "surName VARCHAR(100) NOT NULL,"
                       "jobFunction VARCHAR(500) NOT NULL )")



    def gowno(self):
        self.logger.debug("jestesm w gownie")
        return Request(self.urls[self.iterator], callback=self.parsetwo)
    def parse(self, response):
        self.logger.debug(response.xpath('//body/text()'))
        time.sleep(61)
        self.logger.debug("Ilosc url w liscie "+str(len(self.urls)))
        for ulsl in self.urls:
            self.logger.debug(ulsl)
        self.urls_used.append(self.urls[0])
        return Request(self.urls[0], callback=self.parsetwo,dont_filter=True)


    def parsetwo(self, response):
        self.logger.debug("Asdsaadas")
        strHead = "http://www.krs-online.com.pl/"
        links = response.xpath('//body/div[2]/div[4]/ul[2]/li')
        for li in links.xpath('.//a/@href'):
            link = ''+str(strHead+li.extract())+''
            self.urls.append(link)
            # self.logger.debug(link)

        repList = self.urls
        repList.extend(self.urls_used)
        tempUrls = list(set(repList))

        self.urls = list(set(self.urls_used) ^ set(tempUrls))
        trsft = response.xpath('//body/div[2]/div[5]/div[4]/table[1]')
        dict = {}
        for tr in trsft.xpath('.//tr'):
            i=0

            temp=[]
            for td in tr.xpath('.//td/text()'):
                if i==1:
                    dict[temp[0]]=unicodedata.normalize('NFKD', td.extract().lower()).replace(u'ł', 'l').encode('ascii', 'ignore')
                    temp.pop(0)
                    i=0
                else:
                    temp.append(td.extract().lower())
                    i = i+1
                # self.logger.debug(td.extract())

            for th in tr.xpath('.//th/b/text()'):
                thlow = th.extract().lower()
                dict["firma"] = unicodedata.normalize('NFKD', thlow).replace(u'ł', 'l').encode('ascii', 'ignore')
                # self.logger.debug(th.extract())

        trsst = response.xpath('//body/div[2]/div[5]/div[4]/table[2]')
        namedict = []
        membersComp = []
        dictMem={}
        for tr in trsst.xpath('.//tr'):

            for th in tr.xpath('.//th/text()'):
                thlow = th.extract().lower()
                thSplit = thlow.split(" ")
                thWOPC = unicodedata.normalize('NFKD', thSplit[0]).replace(u'ł', 'l').encode('ascii', 'ignore')
                if(len(thWOPC) > 4):
                    namedict.append(thWOPC)
                else:
                    pass
            i=0
            for td in tr.xpath('.//td/text()'):

                tdlow = td.extract().lower()
                tdWOPC = unicodedata.normalize('NFKD', tdlow).replace(u'ł', 'l').encode('ascii', 'ignore')
                dictMem[namedict[i]]=tdWOPC
                i = i+1
            if bool(dictMem):
                membersComp.append(dictMem)
            else:
                pass
            dictMem={}

        dict["members"] = membersComp


        self.logger.debug(namedict)
        self.logger.debug(dict)
        self.hasNipOrRegon(dict)
        self.logger.debug(dict["nip:"])
        self.addRekordsToCompanies(dict,self.cursor)



        self.iterator = self.iterator+1

        return Request('http://taqie.udl.net/'+str(self.iterator)+'/',dont_filter=True)

















    #     #
    #     # self.logger.debug(response.xpath('//table[@class="tabela"]/tbody/tr[9]/td[1]/text()').extract()[0])
    #     # self.logger.debug(response.xpath('//table[@class="tabela"]/tbody/tr[9]/td[2]/text()').extract()[0])
    #     # # self.start_urls.append(response.xpath('//ul[@class="lista lista4 tlo_biel li_2"]/li/a/@href').extract())
    #     # listaurl = response.xpath('//ul[@class="lista lista4 tlo_biel li_2"]/li/a/@href').extract()
    #     # for link in listaurl:
    #     #     self.logger.debug(link)
    #     #     self.start_urls.append(link)
    #     # # self.logger.debug(response.xpath('//body/div[2]/div[5]/div[5]/div/text()'))
    #
    #     if 'NIP' in str(self.listaMain):
    #         self.logger.debug("jest")
    #         # self.logger.debug(self.listaMain)
    #
    #     # self.logger.debug(self.listaMain)
    #     pass
    #
    # def removePlText(self, stringInp):
    #     napis = ""
    #     if type(stringInp) is list:
    #         listaEl = stringInp
    #         for i in xrange(0,len(listaEl),1):
    #             napis =napis+" "+str(unicodedata.normalize('NFKD', stringInp[i]).encode('ascii', 'ignore'))
    #
    #         return napis.replace(" ","")
    #     elif type(stringInp) is tuple:
    #         pass
    #     else:
    #         pass
    #
    #     napis =  str(unicodedata.normalize('NFKD', stringInp).encode('ascii', 'ignore'))
    #     napis = napis.replace(" ","")
    #     napis = napis.lower()
    #     return napis
    #
    # def paraseTr(self,response,i):
    #     responseTr = response.xpath(
    #         'normalize-space(//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[1]/text())').extract()[0]
    #     return self.removePlText(responseTr)
    #
    # def paraseTd(self,response,i):
    #     responseTd = response.xpath( '//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[2]/text()').extract()
    #     return self.removePlText(responseTd)
    #
    # def paraseAhrefTd(self,response,i):
    #     countAhref = len(response.xpath('//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[2]/a'))
    #     self.logger.debug("ile a "+str(countAhref))
    #     listHref =[]
    #     if countAhref > 0:
    #         for j in xrange(0,countAhref,1):
    #             listHref.append(self.removePlText(response.xpath(
    #                 'normalize-space(//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[2]/a[' + str(j) + ']/text())').extract()))
    #
    #         return listHref
    #     else:
    #         return False
    #
    #     pass
    #
    # def isList(self, list):
    #     if type(list) is list:
    #         return True
    #     else:
    #         return False
    #
    #
    # def parsetwo(self, response):
    #     dataDict={}
    #     nameDict=""
    #     valueDict=[]
    #
    #
    #
    #
    #
    #     dlTr = len(response.xpath('//table[@class="tabela"]/tbody/tr'))
    #     dlTd = len(response.xpath('//table[@class="tabela"]/tbody/tr/td'))
    #
    #
    #     for i in xrange(0,dlTr,1):
    #         try:
    #             nameDict = self.paraseTr(response,i)
    #             if self.paraseAhrefTd(response,i) == False:
    #                 valueDict += self.paraseTd(response, i)
    #             else:
    #                 valueDict +=self.paraseAhrefTd(response,i)
    #                 valueDict +=self.paraseTd(response,i)
    #         except IndexError:
    #             pass
    #
    #         dataDict[nameDict]=valueDict
    #         valueDict=[]
    #
    #     for key, value in dataDict.iteritems():
    #
    #         string  = ""
    #
    #         if key == "osobyzarzadzajace":
    #             for x in value:
    #                 string +=x
    #             for z in string.split("-"):
    #                  self.logger.debug("Nazwa słownika " + str(key) + " wartosc " + str(z))
    #
    #
    #     for key, value in dataDict.iteritems():
    #         strings = value
    #         # liczni = 0
    #         # while(True):
    #         #     if self.isList(strings):
    #         #
    #         #     else:
    #     #     for x in xrange(0,len(strings),1):
    #     #         if len(strings[x]) == 0:
    #     #             # if len(strings[x]) ==1:
    #     #             #     if len(strings[x][0]) == 0:
    #     #             #         strings.pop[x]
    #     #             strings.pop(x)
    #     #         else:
    #     #             pass
    #     #         value = strings
    #     # for key, value in dataDict.iteritems():
    #     #     if key == "osobyzarzadzajace":
    #     #         for x in value:
    #     #             self.logger.debug("Nazwa : "+str(x))
    #     #     # self.logger.debug("Nazwa słownika "+str(key)+" wartosc "+str(value))
    #
    #
    #
    #
    #
    #         # if type(strings) is list:
    #         #     dlList =len(strings)
    #         #     for i in xrange(0,dlList,1):
    #         #         self.logger.debug("dlugosc ele listy  : "+str(len(strings[i]))+" "+str(strings[i])+" "+str(len(strings[i][0])))
    #         #         # self.logger.debug(strings)
    #         #         if len(strings[i][0]) == 0:
    #         #             strings.pop(i)
    #         #         else:
    #         #             str_list = [x.strip() for x in strings[i] if x.strip()]
    #         # elif type(x) is tuple:
    #         #     print 'a tuple'
    #         # else:
    #         #     str_list = [x.strip() for x in strings if x.strip()]
    #         # self.logger.debug(str_list)
    #
    #
    #
    #
    #     #
    #     #
    #     #
    #     #
    #     #
    #     #
    #     #
    #     #
    #     #
    #     # for i in xrange(0,dlTr,1):
    #     #     try:
    #     #
    #     #
    #     #
    #     #         nameDict =
    #     #         nameDict =
    #     #         # for j in xrange(0, len(nameDict),1):
    #     #
    #     #
    #     #         iloscA = len(response.xpath('//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[2]/a'))
    #     #         self.logger.debug(iloscA)
    #     #         if iloscA != 0:
    #     #             for z in xrange(0, iloscA, 1):
    #     #                 try:
    #     #                     wartzA.append(map(unicode.strip,response.xpath(
    #     #                         '//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[2]/a[' + str(
    #     #                             z) + ']/text()').extract()
    #     #                                     ))
    #     #                 except IndexError:
    #     #                     pass
    #     #
    #     #             listares =
    #     #             listares.append(wartzA)
    #     #
    #     #
    #     #         # wartDict.append(map(unicode.strip,listares))
    #     #
    #     #         # wartDict = wartDict
    #     #
    #     #
    #     #
    #     #
    #     #     except IndexError:
    #     #         pass
    #     # self.logger.debug(listares)
    #     # dict[nameDict] = wartDict
    #     # self.logger.debug(dict)
    #     # test = map(unicode.strip,dict["osobyzarzadzajace"][2])
    #     # self.logger.debug(test)
    #     # testlen = len(test)
    #     # napisend = ""
    #     #
    #     # for i in xrange(0,testlen,1):
    #     #     if test[i]:
    #     #         napisend += test[i]
    #     #     else:
    #     #         napisend +=" "
    #
    #     # self.logger.debug(napisend)
    #
    #     # self.logger.debug(dict)
    #
    #
    #
    #
    #
    #
    #
    #     #
    #     #
    #     # for i in xrange(0,dlTr,1):
    #     #     dict[response.xpath(
    #     #                     '//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[' + str(j) + ']/text()').extract()]
    #     #
    #     #     for j in xrange(0,dlTd,1):
    #     #         iloscA=len(response.xpath('//table[@class="tabela"]/tbody/tr/td/a'))
    #     #
    #     #         for z in xrange(0,3,1):
    #     #             try:
    #     #                 templita = response.xpath(
    #     #                     '//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[' + str(j) + ']/text()').extract()[z]
    #     #                 if not templita:
    #     #                     pass
    #     #                 else:
    #     #                     if len(templita) == 1:
    #     #                         lista.append(templita)
    #     #                     else:
    #     #                         lista.append(templita)
    #     #
    #     #                 # lista.append()
    #     #                 # self.logger.debug(lista)
    #     #             except IndexError:
    #     #                 pass
    #     #         if iloscA != 0:
    #     #             for z in xrange(0,iloscA,1):
    #     #                 try:
    #     #                     templita = response.xpath(
    #     #                         '//table[@class="tabela"]/tbody/tr[' + str(i) + ']/td[' + str(
    #     #                             j) + ']/a['+str(z)+']/text()').extract()
    #     #                     if not templita:
    #     #                         pass
    #     #                     else:
    #     #                         if len(templita) == 1:
    #     #                             lista.append(templita)
    #     #                         else:
    #     #                             lista.append(templita)
    #     #                 except IndexError:
    #     #                     pass
    #     #
    #     #             # self.logger.debug("empty")
    #     # self.listaMain = lista
    #     # self.logger.debug(lista)
    #     # list2 = filter(None, lista)
    #     # for i in xrange(0,len(list2),1):
    #     #     self.logger.debug(list2[i])
    #     #     # self.logger.debug(lista[i+1])
    #
    #     # self.logger.debug(response.xpath('//table[@class="tabela"]/tbody/tr[9]/td[1]/text()').extract()[0])
    #     # self.logger.debug()
    #     # self.logger.debug(response.xpath('//table[@class="tabela"]/tbody/tr[last()]/td[2]/text()').extract()[0])
    #     # for nodes in response.xpath('///table[@class="tabela"]/tbody/tr'):
    #     #     for i in nodes.xpath('td'):
    #     #         print i.xpath('text()').extract()
    #     #         print i.xpath('following-sibling::dd[1]/text()').extract()
    #     # # self.start_urls.append(response.xpath('//ul[@class="lista lista4 tlo_biel li_2"]/li/a/@href').extract())
    #     listaurl = response.xpath('//ul[@class="lista lista4 tlo_biel li_2"]/li/a/@href').extract()
    #     # for link in listaurl:
    #     #     self.logger.debug(link)
    #     #     self.start_urls.append(link)
    #     # self.logger.debug(response.xpath('//body/div[2]/div[5]/div[5]/div/text()'))
