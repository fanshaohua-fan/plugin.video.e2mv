# -*- coding: utf-8 -*-
import urllib,urllib2,re,os,xbmcplugin,xbmcgui,xbmc
import xbmcaddon
import gzip, StringIO
import cookielib

maxVideoQuality  = '720p'
__addonid__   = "plugin.video.e2mv"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__addonicon__ = os.path.join( __addon__.getAddonInfo('path'), 'icon.png' )
__profile__   = xbmc.translatePath( __addon__.getAddonInfo('profile') )

cookieFile    = __profile__ + 'cookies.e2mv'
UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

VOD_LIST = [('电视剧','/?s=vod-show-id-2.html'),
('国产剧','/?s=vod-show-id-15.html'),
('港台剧','/?s=vod-show-id-16.html'),
('欧美剧','/?s=vod-show-id-17.html'),
('韩剧','/?s=vod-show-id-18.html'),
('海外剧','/?s=vod-show-id-19.html'),
('日剧','/?s=vod-show-id-32.html'),
('电影','/?s=vod-show-id-1.html'),
('动作片','/?s=vod-show-id-8.html'),
('喜剧片','/?s=vod-show-id-9.html'),
('爱情片','/?s=vod-show-id-10.html'),
('奇幻片','/?s=vod-show-id-11.html'),
('恐怖片','/?s=vod-show-id-12.html'),
('战争片','/?s=vod-show-id-13.html'),
('故事片','/?s=vod-show-id-14.html'),
('纪录片','/?s=vod-show-id-26.html'),
('动漫','/?s=vod-show-id-3.html'),
('综艺','/?s=vod-show-id-4.html'),
('体育','/?s=vod-show-id-5.html'),
('音乐','/?s=vod-show-id-27.html'),
('其它','/?s=vod-show-id-7.html')]

##################################################################################
# Routine to fetch url site data using Mozilla browser
# - delete '\r|\n|\t' for easy re.compile
# - do not delete \s <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
##################################################################################
def getHttpData(url):
    print "getHttpData: " + url
    # setup proxy support
    proxy = __addon__.getSetting('http_proxy')
    type = 'http'

    if proxy <> '':
        ptype = re.split(':', proxy)
        if len(ptype)<3:
            # full path requires by Python 2.4
            proxy = type + '://' + proxy 
        else: type = ptype[0]
        httpProxy = {type: proxy}
    else:
        httpProxy = {}
    proxy_support = urllib2.ProxyHandler(httpProxy)
    
    # setup cookie support
    cj = cookielib.MozillaCookieJar(cookieFile)
    if os.path.isfile(cookieFile):
        cj.load(ignore_discard=False, ignore_expires=False)
    else:
        if not os.path.isdir(os.path.dirname(cookieFile)):
            os.makedirs(os.path.dirname(cookieFile))

    # create opener for both proxy and cookie
    opener = urllib2.build_opener(proxy_support, urllib2.HTTPCookieProcessor(cj))
    charset=''
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)

    try:
        response = opener.open(req)
        #response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        httpdata = e.read()
    except urllib2.URLError, e:
        httpdata = "IO Timeout Error"
    else:
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
        response.close()

    httpdata = re.sub('\r|\n|\t', '', httpdata)
    match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
    if len(match):
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')

    return httpdata

##################################################################################
def addDir(name, url, mode, pic = '', isDir = True, sn = ''):
    if sn != '': sn=str(sn)+". "
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    li=xbmcgui.ListItem(sn+name,'', pic, pic)
    li.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=li,isFolder=isDir)
    return ok

##################################################################################
# E2MV Main Menu
##################################################################################
def MainMenu():
    for v in VOD_LIST:
        name = v[0]
        url = 'http://e2mv.com' + v[1]
        addDir( name, url, '1')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def showVideoLists(url):   
    #url = 'http://e2mv.com/?s=vod-show-id-2.html'
    link = getHttpData(url)
    if link == None: return

    matchli = re.compile('<li>[\s\S]*?</li>').findall(link)
    if len(matchli):
        totalItems=len(matchli)
        for item in matchli:
            match = re.compile('<a href="(.+?)" target="_self" title="(.+?)" class="avatar play">').findall(item)
            url     = match[0][0]
            name    = match[0][1]

            thumb = ''
            m_thumb = re.compile('<img alt=".+?"  data-original="(.+?)" src="/stitc/place.gif" />').findall(item)
            if m_thumb:
                thumb = 'http://e2mv.com' + m_thumb[0]

            addDir(name, url, '9', thumb)

    # pagination
    matchli = re.compile('<a href="(\/\?s=vod-show-id-\d+?-p-\d+?.html)">(\d+)</a>').findall(link)
    for v in matchli:
        name = '第 %s 页' % v[1]
        url = 'http://e2mv.com' + v[0]
        addDir( name, url, '1')

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def showEpisodeLists(url):   
    #url = 'http://e2mv.com/?s=vod-read-id-36626.html'
    url = 'http://e2mv.com' + url
    link = getHttpData(url)
    if link == None: return

    matchli = re.compile('<div style="align:center">[\s\S]*?</div>').findall(link)
    if len(matchli):
        totalItems=len(matchli)
        for item in matchli:
            match = re.compile('<a  href="(.+?)" target="_self">(.+?)</a>').findall(item)

            url     = match[0][0]
            title   = match[0][1]

            li = xbmcgui.ListItem(title, iconImage = '', thumbnailImage = '')
            li.setInfo(type = "Video", infoLabels = {"Title":title})
            u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(title)+"&url="+urllib.quote_plus(url)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getStreamUrl(url):
    content = getHttpData(url)
    if content.find('"statusCode":410') > 0 or content.find('"statusCode":403') > 0:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30022)+' (DailyMotion)!,5000)')
        return ""
    else:
        matchFullHD = re.compile('"1080":(.+?)"url":"(.*?)"}\]', re.DOTALL).findall(content)
        matchHD = re.compile('"720":(.+?)"url":"(.*?)"}\]', re.DOTALL).findall(content)
        matchHQ = re.compile('"480":(.+?)"url":"(.*?)"}\]', re.DOTALL).findall(content)
        matchSD = re.compile('"380":(.+?)"url":"(.*?)"}\]', re.DOTALL).findall(content)
        matchLD = re.compile('"240":(.+?)"url":"(.*?)"}\]', re.DOTALL).findall(content)
        url = ""
        if matchFullHD and maxVideoQuality == "1080p":
            url = urllib.unquote_plus(matchFullHD[0][1]).replace("\\", "")
        elif matchHD and (maxVideoQuality == "720p" or maxVideoQuality == "1080p"):
            url = urllib.unquote_plus(matchHD[0][1]).replace("\\", "")
        elif matchHQ:
            url = urllib.unquote_plus(matchHQ[0][1]).replace("\\", "")
        elif matchSD:
            url = urllib.unquote_plus(matchSD[0][1]).replace("\\", "")
        elif matchLD:
            url = urllib.unquote_plus(matchLD[0][1]).replace("\\", "")
        return url

def getVideoUrl(url):

    url = 'http://e2mv.com' + url
    link = getHttpData(url)
    if link == None: return ''
    
    match = re.compile('<iframe frameborder="0" [\s\S]*? src="(.+?)"></iframe>').findall(link)

    # http://www.dailymotion.com/embed/video/ktKXT5y0V1nlwSa5uI7?autoplay=1&logo=0&hideInfos=1&start=0&syndication=148844?autoPlay=1
    url = match[0]

    return getStreamUrl(url.split('?')[0])

def playVideo(name,url):
    videoplaycont = __addon__.getSetting('video_vplaycont')
    
    playlist=xbmc.PlayList(1)
    playlist.clear()

    
    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    pDialog.update(0)
        
    li = xbmcgui.ListItem(name, iconImage = '', thumbnailImage = '')
    li.setInfo(type = "Video", infoLabels = {"Title":name})

    v_url = getVideoUrl(url)

    xbmc.log("fanshaohua.fan: %s" % v_url)
    playlist.add(v_url, li)

    pDialog.close() 
    xbmc.Player(1).play(playlist)

##################################################################################
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

##################################################################################

params=get_params()
url=None
mode=None
name=None

try:
    mode=int(params["mode"])
except:
    pass
try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
ctl = {
            None : ('MainMenu()'),
            1    : ('showVideoLists(url)'),

            9    : ('showEpisodeLists(url)'),
            10   : ('playVideo(name,url)'),
      }
exec(ctl[mode])
