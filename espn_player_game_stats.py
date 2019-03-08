
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import re
import time as time
import warnings as warn

warn.filterwarnings('ignore')

# to do: build a scraper to gather NBA player list
players = pd.read_csv('./github_matthewsaaronj/espn_nba_stats/NBA_Players.csv')


for x in range(0, players.shape[0]):
    
    pid = players.URL[x].split('/')[-1]
    name = players.NAME[x]
    
    url = 'http://www.espn.com/nba/player/gamelog/_/id/' + pid
    
    html = urlopen(url)
    bsObj = BeautifulSoup(html)
    
    # get stat headers
    stat_headers = []
    for attr in bsObj.find_all('table')[1].find_all('td', title=re.compile('[A-Z]')):
        if not attr.get_text() in stat_headers:
            stat_headers.append(attr.get_text())
            
    stat_headers_reorg = []
    r = re.compile('[A-Z0-9]+[-]+[A-Z0-9]')
    
    for x in stat_headers:
        if r.match(x):
            m_a = x.split('-')
            stat_headers_reorg.append(m_a[0])
            stat_headers_reorg.append(m_a[1])
        else:
            stat_headers_reorg.append(x)
            
    # create an OrderedDict to dynamically create the 
    # data frame
            
    from collections import OrderedDict
    
    stat_dict = OrderedDict()
    
    for x in range(0, len(stat_headers_reorg)):
        stat_dict[stat_headers_reorg[x]] = []
        stat_dict[stat_headers_reorg[x]].append(x)
        
    # code needs to be smart enough to know where it's at in the page
    # as tables begin and end without explicit rules
    # thus, using regular expressions to determine where we are and then
    # pull in stats
    h = re.compile("[0-9]+[-]+[0-9]+[' ']+[\.A-Z]") # identify when we've moved between season types
    s = re.compile("[WL]+[' ']+[0-9/.]")
    p = re.compile('[0-9]+[-]+[0-9]')
    
    n_stats = len(stat_headers_reorg)
    get_stats = False
    stat_cnt = 0
    
    stat_dict = OrderedDict([('SEASON', [])])
    
    for x in range(0, n_stats):
        stat_dict[stat_headers_reorg[x]] = []
    
    for tag in bsObj.find_all('table')[1].findAll('td'):
        if h.match(tag.get_text()):
            header = tag.get_text()
        if s.match(tag.get_text()):
            get_stats = True
            continue
        if get_stats == True:
            if stat_cnt < n_stats:
                if stat_cnt == 0:
                    stat_dict['SEASON'].append(header)
                if p.match(tag.get_text()):
                    stat_split = tag.get_text().split('-')
                    stat_dict[stat_headers_reorg[stat_cnt]].append(stat_split[0])
                    stat_dict[stat_headers_reorg[stat_cnt + 1]].append(stat_split[1])
                    stat_cnt += 2
                      
                else:
                    stat_dict[stat_headers_reorg[stat_cnt]].append(tag.get_text())
                    stat_cnt += 1
            else:
                get_stats = False
                stat_cnt = 0
          
    stat_table = pd.DataFrame(stat_dict)
    
    # get left hand attributes
    
    # opponent
    c = re.compile('\xa0[a-zA-Z]')
    team = []
    
    for tag in bsObj.find_all('table')[1].find_all('li', {'class': 'team-name'}):
        if c.match(tag.get_text()):
            team.append(tag.get_text().replace(u'\xa0', u''))
        else:
            team.append(tag.get_text())
            
    # location
    loc = []

    for tag in bsObj.find_all('table')[1].find_all('li', {'class': 'game-location'}):
        if tag.get_text() == '@ ':
            loc.append('AWAY')
        elif tag.get_text() == 'vs':
            loc.append('HOME')
            
    # game dates
    dates = []

    r = re.compile("[MonTueWedThuFriSatSun]+[' ']+[0-9]+[/]+[0-9]")
    for obj in bsObj.find_all('table')[1].findAll('td', style=''):
        
        if r.match(obj.get_text()):
            dates.append(obj.get_text())
            
    # win-loss, team and opponent score
    win_loss = []
    team_score = []
    opp_score = []
    
    r = re.compile("[WL]+[' ']+[0-9]+[-]+[0-9]")
    for obj in bsObj.find_all('table')[1].findAll('td', style=''):
        
        if r.match(obj.get_text()):
            win_loss.append(obj.get_text().split(' ')[0])
            team_score.append(obj.get_text().split(' ')[1].split('-')[0])
            opp_score.append(obj.get_text().split(' ')[1].split('-')[1])
            
    lh_table = pd.DataFrame(
            {'DATE': dates,
             'LOCATION': loc,
             'OPPONENT': team,
             'WIN_LOSS': win_loss,
             'TEAM_SCORE': team_score,
             'OPP_SCORE': opp_score})
    
    stat_table = pd.concat([lh_table, stat_table], axis=1)
    
    
    
    