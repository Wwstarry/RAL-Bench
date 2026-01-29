# -*- coding: utf-8 -*-

from lib.core import data
from lib.core.settings import VERSION, DESCRIPTION

class OptionStore:
    """Container for configuration options"""
    
    def __init__(self):
        # Target options
        self.url = None
        self.directConnection = None
        self.logFile = None
        self.bulkFile = None
        self.requestFile = None
        self.sessionFile = None
        self.googlePage = 1
        self.configFile = None
        
        # Request options
        self.method = None
        self.data = None
        self.paramDel = None
        self.cookie = None
        self.cookieDel = None
        self.liveCookies = None
        self.loadCookies = None
        self.dropSetCookie = False
        self.user = None
        self.password = None
        self.auth = None
        self.authType = None
        self.authFile = None
        self.ignoreCode = None
        self.ignoreProxy = False
        self.ignoreRedirects = False
        self.ignoreTimeouts = False
        self.proxy = None
        self.proxyCreds = None
        self.proxyFile = None
        self.tor = False
        self.torPort = "SOCKS5://localhost:9050"
        self.torType = "SOCKS5"
        self.checkTor = False
        self.delay = 0
        self.timeout = 30
        self.retries = 3
        self.randomAgent = False
        self.userAgent = None
        self.host = None
        self.referer = None
        self.headers = None
        self.authorizationHeader = None
        self.hpp = False
        self.mobile = False
        self.pageRank = False
        self.sitemap = None
        self.crawlDepth = 2
        self.crawlExclude = None
        self.csvDel = ","
        self.charset = None
        self.dumpFormat = "CSV"
        self.encoding = None
        self.eta = False
        self.flushSession = False
        self.forms = False
        self.freshQueries = False
        self.googleDork = None
        self.harFile = None
        self.hexConvert = False
        self.outputDir = None
        self.parseErrors = False
        self.postprocess = None
        self.preprocess = None
        self.repair = False
        self.saveConfig = None
        self.scope = None
        self.testFilter = None
        self.testSkip = None
        self.webRoot = None
        
        # Optimization options
        self.keepAlive = False
        self.nullConnection = False
        self.threads = 1
        
        # Injection options
        self.technique = None
        self.timeSec = 5
        self.uCols = None
        self.uChar = None
        self.uFrom = None
        self.dnsDomain = None
        self.secondUrl = None
        self.secondReq = None
        
        # Detection options
        self.level = 1
        self.risk = 1
        self.string = None
        self.notString = None
        self.regexp = None
        self.code = None
        self.smart = False
        self.textOnly = False
        self.titles = False
        
        # Database options
        self.db = None
        self.tbl = None
        self.col = None
        self.exclude = None
        self.user = None
        self.excludeSysDbs = False
        self.whereDump = None
        self.startCol = None
        self.stopCol = None
        self.firstChar = None
        self.lastChar = None
        self.query = None
        self.sqlQuery = None
        self.sqlShell = False
        self.sqlFile = None
        
        # File system options
        self.fileRead = None
        self.fileWrite = None
        self.fileDest = None
        
        # OS access options
        self.osCmd = None
        self.osShell = False
        self.osPwn = False
        self.osSmb = False
        self.osBof = False
        self.privEsc = False
        self.msfPath = None
        self.tmpPath = None
        
        # Windows registry options
        self.regRead = False
        self.regAdd = False
        self.regDel = False
        self.regKey = None
        self.regVal = None
        self.regData = None
        self.regType = None
        
        # General options
        self.trafficFile = None
        self.answers = None
        self.batch = False
        self.base64Parameter = None
        self.base64Safe = False
        self.binaryFields = None
        self.checkInternet = False
        self.crawl = 0
        self.crawlExclude = None
        self.dependencies = False
        self.disablePrecon = False
        self.encoding = None
        self.eta = False
        self.flushSession = False
        self.forms = False
        self.freshQueries = False
        self.googleDork = None
        self.harFile = None
        self.hexConvert = False
        self.identifyWaf = False
        self.listTampers = False
        self.offline = False
        self.pageRank = False
        self.parseErrors = False
        self.postprocess = None
        self.preprocess = None
        self.repair = False
        self.saveConfig = None
        self.scope = None
        self.testFilter = None
        self.testSkip = None
        self.webRoot = None
        self.wizard = False
        
        # Miscellaneous options
        self.alert = None
        self.beep = False
        self.offline = False
        self.dependencies = False
        self.disablePrecon = False
        self.listTampers = False
        self.wizard = False
        self.verbose = 0
        
        # Hidden options
        self.checkWaf = False
        self.crawlDepth = 2
        self.crawlExclude = None
        self.dependencies = False
        self.disablePrecon = False
        self.identifyWaf = False
        self.listTampers = False
        self.offline = False
        self.pageRank = False
        self.parseErrors = False
        self.postprocess = None
        self.preprocess = None
        self.repair = False
        self.saveConfig = None
        self.scope = None
        self.testFilter = None
        self.testSkip = None
        self.webRoot = None
        self.wizard = False

def init(options):
    """Initialize options from command-line parsed options"""
    conf = OptionStore()
    
    # Copy all attributes from options to conf
    for key in dir(options):
        if not key.startswith('_'):
            try:
                value = getattr(options, key)
                if not callable(value):
                    setattr(conf, key, value)
            except AttributeError:
                pass
    
    data.dataStore.conf = conf
    return conf

def initOptions():
    """Initialize default options"""
    return OptionStore()