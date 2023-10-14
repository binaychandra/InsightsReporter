from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import *
from glob import glob
import os
from PIL import Image
from itertools import product
import random
#import pdfkit

us_state_abbrev = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
        'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana',
        'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts',
        'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
        'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
        'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia', 'MP': 'Northern Mariana Islands',
        'PW': 'Palau', 'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'AA': 'Armed Forces Americas (Except Canada)',
        'AE': 'Armed Forces Africa/Canada/Europe/Middle East', 'AP': 'Armed Forces Pacific'
    }

def ptagwrap(observationlist : list) -> str:
    """[The function is used to wrap the observation list in the paragraph tag]

    Args:
        observationlist (list): [The list of observations in the data]

    Returns:
        [str]: [The observations wrapped in the paragraph tag]
    """    
    ptemplate = """<li><p style="margin: 0; font-size: 16px; line-height: 1.2; word-break: break-word; margin-top: 5px; margin-bottom: 5px;">
                            <span style="font-size: 16px;">{placeholder}</span></p></li>"""
    placeholder = [ptemplate.format(placeholder=x) for x in observationlist]
    return ''.join(placeholder)

def bookingcomparison_year2019(qmodel_df : pd.DataFrame()) -> str:
    """[The function used to perform booking comparison on the data with 2019 bookings]

    Args:
        qmodel_df ([pd.DataFrame]): [The dataframe containing the bookings data]

    Returns:
        [str]: [The observations in the data wrappedin a paragraph]
    """    
    latestmodel = qmodel_df[(qmodel_df.Model_creation_date == qmodel_df.Model_creation_date.max())][['Date','state_code', 'ActualBooking', 'forecast_avg_bqfb']]
    #enddate = np.datetime64(qmodel_df.Model_creation_date.max()) -2
    # Assuming qmodel_df.Model_creation_date.max() returns the date string '11-10-2023'
    date_string = qmodel_df.Model_creation_date.max()

    # Convert the date string to datetime object
    datetime_obj = datetime.strptime(date_string, "%Y-%m-%d")

    # Convert datetime object to np.datetime64
    enddate = np.datetime64(datetime_obj) - np.timedelta64(2, 'D')
    startdate = enddate - 6
    
    thisweekbookings = latestmodel[(latestmodel.Date >= startdate) & (latestmodel.Date <= enddate)][['state_code', 'ActualBooking']]
    thisweekbookings = thisweekbookings.groupby(['state_code']).sum().reset_index().rename(columns={'ActualBooking':'thisWeekActualBooking'})
    
    year2019bookings = latestmodel[(latestmodel.Date >= startdate - np.timedelta64(2 * 365 + 1,'D')) & (latestmodel.Date <= enddate - np.timedelta64(2 * 365 + 1, 'D' ))][['state_code', 'ActualBooking']]
    year2019bookings = year2019bookings.groupby(['state_code']).sum().reset_index().rename(columns={'ActualBooking':'year2019ActualBooking'})
    thisweekvsyear2019 = pd.merge(thisweekbookings, year2019bookings, how = 'left', left_on='state_code', right_on='state_code')
    thisweekvsyear2019['percentchangefrom2019'] = (thisweekvsyear2019.thisWeekActualBooking - thisweekvsyear2019.year2019ActualBooking) * 100/ thisweekvsyear2019.year2019ActualBooking
    thisweekvsyear2019 = thisweekvsyear2019.sort_values(by='percentchangefrom2019')
    thisweekvsyear2019['percentchangefrom2019'] = thisweekvsyear2019['percentchangefrom2019'] + 10
    thisweekvsyear2019 = np.round(thisweekvsyear2019, 1)
    thisweekvsyear2019['CalcRange'] = thisweekvsyear2019['percentchangefrom2019'].apply(lambda x: 'high' if x > 5 else ('medium' if (-5 <= x <= 5) else 'low'))

    fig = px.choropleth(thisweekvsyear2019, locations='state_code',
                    #color='CalcRange', color_discrete_map={'low':'red', 'medium':'Yellow','high':'Green'},
                    color='CalcRange', color_discrete_map={'low':'rgb(150, 15, 11)', 'medium':'rgb(235, 158, 35)','high':'rgb(10, 125, 33)'},
                    hover_name='state_code', locationmode='USA-states', scope='usa')
    fig.add_scattergeo(locations=thisweekvsyear2019['state_code'], locationmode='USA-states', text=thisweekvsyear2019['percentchangefrom2019'],
                        mode='text', textfont=dict(family="Arial",size=10))
    fig.update_layout({'plot_bgcolor': 'grey','paper_bgcolor': 'rgba(0, 0, 0, 0)'})
    fig.update_layout(coloraxis_showscale=True)
    fig.update_layout(geo=dict(showlakes=False, lakecolor = 'rgba(0,0,0,0)', bgcolor= 'rgba(0,0,0,0)'))
    fig.update_layout(geo=dict(scope='usa', showlakes=False))
    fig.update_traces(showlegend=True)
    fig.write_image("./static/images/usmap_percentchangefrmyear2019.png", engine='kaleido',format='png')
    # resize the image to fit in the cell
    im = Image.open('./static/images/usmap_percentchangefrmyear2019.png')
    width, height = im.size
    im1 = im.crop((100, 100, 600, 390)) #set the crop coordinates (x,y, x+width, y+height)
    im1.save('./static/images/usmap_percentchangefrmyear2019.png')

    # Gather observations ___________
    observations_thisweekvsyear2019 = ["The overall bookings this week {isincreased} compared to 2019 by {percentincordec}%".format(isincreased = 'increased' if thisweekvsyear2019.percentchangefrom2019.sum() > 0 else 'decreased', percentincordec = round(abs(thisweekvsyear2019.percentchangefrom2019.mean()), 2))]
    
    lowstatelist = thisweekvsyear2019[thisweekvsyear2019.percentchangefrom2019 < 0].sort_values('percentchangefrom2019', ascending=True).head().state_code.tolist()
    lowstatelist = ', '.join([us_state_abbrev[x] for x in lowstatelist])
    last_char_index = lowstatelist.rfind(",")
    lowstatestr = lowstatelist[:last_char_index] + " and" + lowstatelist[last_char_index+1:]
    
    strlowstates = "The States {liststates_low} record lowest percentage bookings as compared to year 2019.".format(liststates_low = lowstatestr)
    observations_thisweekvsyear2019.append(strlowstates)
    
    stateswithhighpercentchange = thisweekvsyear2019[thisweekvsyear2019.percentchangefrom2019 > 0].sort_values('percentchangefrom2019', ascending=False).head().state_code.tolist()
    stateswithhighpercentchange = ', '.join([us_state_abbrev[x] for x in stateswithhighpercentchange])
    last_char_index = stateswithhighpercentchange.rfind(",")
    stateswithhighstatestr = stateswithhighpercentchange[:last_char_index] + " and" + stateswithhighpercentchange[last_char_index+1:]
    strhighstates = "The States {liststates_high} record maximum percentage increase in booking as compared to 2019.".format(liststates_high = stateswithhighstatestr)
    observations_thisweekvsyear2019.append(strhighstates)
    
    wrappedinptag = ptagwrap(observations_thisweekvsyear2019)

    return observations_thisweekvsyear2019, wrappedinptag

def bookingcomparison_previousweek(qmodel_df: pd.DataFrame()) -> str:
    """[The function compares the bookings of the previous week to the bookings of the current week]

    Args:
        qmodel_df (pd.DataFrame): [The dataframe that contains the booking data]

    Returns:
        str: [The observations of the bookings wrapped in a paragraph tag]
    """    
    """ This function is used to compare the booking count of the previous week with the booking count of the current week and returns the percentage change."""
    latestmodel = qmodel_df[(qmodel_df.Model_creation_date == qmodel_df.Model_creation_date.max())][['Date','state_code', 'ActualBooking', 'forecast_avg_bqfb']]
    # Assuming qmodel_df.Model_creation_date.max() returns the date string '11-10-2023'
    date_string = qmodel_df.Model_creation_date.max()

    # Convert the date string to datetime object
    datetime_obj = datetime.strptime(date_string, "%Y-%m-%d")

    # Convert datetime object to np.datetime64
    enddate = np.datetime64(datetime_obj) - np.timedelta64(2, 'D')
    
    startdate = enddate - np.timedelta64(6, 'D')

    thisweekbookings = latestmodel[(latestmodel.Date >= startdate) & (latestmodel.Date <= enddate)][['state_code', 'ActualBooking']]
    thisweekbookings = thisweekbookings.groupby(['state_code']).sum().reset_index().rename(columns={'ActualBooking':'thisWeekActualBooking'})
    
    print("last week booking stats")
    print("startdate_prev", startdate - np.timedelta64(7, 'D'))
    print("enddate_prev", enddate - np.timedelta64(7, 'D'))
    lastweekbookings = latestmodel[(latestmodel.Date >= startdate - np.timedelta64(7, 'D')) & (latestmodel.Date <= enddate - np.timedelta64(7, 'D'))][['state_code', 'ActualBooking']]
    lastweekbookings = lastweekbookings.groupby(['state_code']).sum().reset_index().rename(columns={'ActualBooking':'lastWeekActualBooking'})
    
    thisweekvslastweek = pd.merge(thisweekbookings, lastweekbookings, how = 'left', left_on='state_code', right_on='state_code')
    thisweekvslastweek['percentchangefromlastweek'] = (thisweekvslastweek.thisWeekActualBooking - thisweekvslastweek.lastWeekActualBooking) * 100/ thisweekvslastweek.lastWeekActualBooking
    thisweekvslastweek['percentchangefromlastweek'] = thisweekvslastweek['percentchangefromlastweek'] + 10
    thisweekvslastweek = thisweekvslastweek.sort_values(by='percentchangefromlastweek')
    thisweekvslastweek = np.round(thisweekvslastweek, 1)
    #addition today
    thisweekvslastweek['CalcRange'] = thisweekvslastweek['percentchangefromlastweek'].apply(lambda x: 'high' if x > 5 else ('medium' if (-5 <= x <= 5) else 'low'))
    print("Printing thisweekvs lastweek")
    print(thisweekvslastweek)
    fig = px.choropleth(thisweekvslastweek, locations='state_code',
                    #color='CalcRange', color_discrete_map={'low':'red', 'medium':'Yellow','high':'Green'},
                    color='CalcRange', color_discrete_map={'low':'rgb(150, 15, 11)', 'medium':'rgb(235, 158, 35)','high':'rgb(10, 125, 33)'},
                    hover_name='state_code', locationmode='USA-states', scope='usa')
    fig.add_scattergeo(locations=thisweekvslastweek['state_code'], locationmode='USA-states', text=thisweekvslastweek['percentchangefromlastweek'],
                        mode='text', textfont=dict(family="Arial",size=9))
    fig.update_layout({'plot_bgcolor': 'grey','paper_bgcolor': 'rgba(0, 0, 0, 0)'})
    fig.update_layout(coloraxis_showscale=False)
    fig.update_layout(geo=dict(showlakes=False, lakecolor = 'rgba(0,0,0,0)', bgcolor= 'rgba(0,0,0,0)'))
    fig.update_layout(geo=dict(scope='usa', showlakes=False))
    fig.write_image("./static/images/usmap_percentchangefrmlastweek.png", engine='kaleido',format='png')
    
    im = Image.open('./static/images/usmap_percentchangefrmlastweek.png')
    width, height = im.size
    im1 = im.crop((100, 100, 600, 390)) #set the crop coordinates (x,y, x+width, y+height)
    im1.save('./static/images/usmap_percentchangefrmlastweek.png')

    # Gather observations ___________
    observations_thisweekvslastweek = ["The overall bookings this week {isincreased} from the previous week by {percentincordec}%".format(isincreased = 'increased' if thisweekvslastweek.percentchangefromlastweek.sum() > 0 else 'decreased', percentincordec = round(thisweekvslastweek.percentchangefromlastweek.mean(), 2))]
    
    lowstatelist = thisweekvslastweek[thisweekvslastweek.percentchangefromlastweek < 0].sort_values('percentchangefromlastweek', ascending=True).head().state_code.tolist()
    lowstatelist = ', '.join([us_state_abbrev[x] for x in lowstatelist])
    last_char_index = lowstatelist.rfind(",")
    lowstatestr = lowstatelist[:last_char_index] + " and" + lowstatelist[last_char_index+1:]

    strlowstates = "{liststates_low} record lowest percentage bookings as compared to last week.".format(liststates_low = lowstatestr)
    observations_thisweekvslastweek.append(strlowstates)
    
    stateswithhighpercentchange = thisweekvslastweek[thisweekvslastweek.percentchangefromlastweek > 0].sort_values('percentchangefromlastweek', ascending=False).head().state_code.tolist()
    stateswithhighpercentchange = ', '.join([us_state_abbrev[x] for x in stateswithhighpercentchange])
    last_char_index = stateswithhighpercentchange.rfind(",")
    highstatestr = stateswithhighpercentchange[:last_char_index] + " and" + stateswithhighpercentchange[last_char_index+1:]
    strhighstates = "{liststates_high} record highest percentage bookings as compared to last week.".format(liststates_high = highstatestr)
    #observations_thisweekvslastweek.append(strhighstates)strhighstates = "The States {liststates_high} record maximum percentage increase in booking as compared to last week.".format(liststates_high = ', '.join(stateswithhighpercentchange))
    observations_thisweekvslastweek.append(strhighstates)
    
    wrappedinptag = ptagwrap(observations_thisweekvslastweek)

    return observations_thisweekvslastweek, wrappedinptag

def actualbookingstats(qmodel_df : pd.DataFrame()) -> str:
    """[The function extracts the actual booking stats and returns the html wrapped in a paragraph tag]

    Args:
        qmodel_df (pd.DataFrame): [The dataframe containing the actual booking data]

    Returns:
        str: [The observation string wrapped in a paragraph tag]
    """
    qmodel_df.Date = pd.to_datetime(qmodel_df.Date, dayfirst=False)
    dlatest = qmodel_df[qmodel_df.Model_creation_date == qmodel_df.Model_creation_date.max()]
    dlatest = dlatest[['Date', 'ActualBooking']].dropna(how='any')
    dlatest = dlatest.groupby('Date').sum().reset_index()
    dlatest.Date = pd.to_datetime(dlatest.Date)
    dlatest = dlatest.sort_values('Date')
    dlatest['year'] = dlatest.Date.dt.year
    dlatest['Date'] = dlatest.Date.dt.strftime('%d-%b')
    dlatest19 = dlatest[dlatest.year == 2019]
    dlatest20 = dlatest[dlatest.year == 2020]
    dlatest21 = dlatest[dlatest.year == 2021]
    dlatest21copy = dlatest21.copy()
    #Anomaly Detection
    rangemin = int(dlatest21copy.ActualBooking.mean() - 1.96 * dlatest21copy.ActualBooking.std())
    rangemax = int(dlatest21copy.ActualBooking.mean() + 1.96 * dlatest21copy.ActualBooking.std())
    dlatest21copy['isAnomaly'] = dlatest21copy.ActualBooking.apply(lambda x: False if x in range(rangemin, rangemax) else True)
    dlatest21copy = dlatest21copy[dlatest21copy.isAnomaly]
    print(dlatest21copy.head())
    #print(dlatest21copy)
    fig = go.Figure()
    print("fig go created ")
    fig.add_trace(go.Scatter(x=dlatest20.Date, y=dlatest20.ActualBooking, mode='lines',
        line=dict(color='rgb(212, 141, 133)', width=2.5), connectgaps=True, name = "2020"))
    print("added traced one")
    fig.add_trace(go.Scatter(x=dlatest19.Date, y=dlatest19.ActualBooking, mode='lines',
            line=dict(color="rgb(232, 221, 74)", width=2), connectgaps=True, name = "2019"))
    fig.add_trace(go.Scatter(x=dlatest21.Date, y=dlatest21.ActualBooking, mode='lines',
            line=dict(color="rgb(75, 130, 128)", width=3), connectgaps=True, name='2021'))
    fig.add_trace(go.Scatter(x=dlatest21copy.Date, y=dlatest21copy.ActualBooking, mode='markers', marker_symbol='x',
                            marker_line_color="rgb(0, 0, 0)", marker_color="rgb(255,0,0)",
                            marker_line_width=1, marker_size=10,
            line=dict(color="rgb(168, 54, 50)", width=2.5), connectgaps=True, name='Anomaly'))
    fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)'}, xaxis = dict(tickmode = 'linear', tickangle = -45, tick0 = dlatest.Date[0],
            dtick = 30), legend=dict(orientation="h", yanchor="bottom", y=0.85, xanchor="left", x=0.05, font = dict(size=10)))
    print("Layout updated ")
    fig.write_image(r"./static/images/dailybooking_lineplot.png", engine='kaleido',format='png', height=400, width = 600)
    # resize the image to fit in the cell - plot_bgcolor = "rgba(211, 245, 244,0.5)", 
    print("image written")
    im = Image.open('./static/images/dailybooking_lineplot.png')
    width, height = im.size
    im1 = im.crop((50, 75, 570, 390)) #set the crop coordinates (x,y, x+width, y+height)
    im1.save('./static/images/dailybooking_lineplot.png')
    bookingstats = []
    bookingstats.append("The average number of booking per day is {perdaybooking2021} which is {percentdiff20n21:.1f}% {highorlow20n21} than 2020 {andorbut} {percentdiff21n19:.1f}% {highorlow21n19} than year 2019."\
                        .format(perdaybooking2021= format(int(dlatest21.ActualBooking.mean()), ','),
                                percentdiff20n21 = (abs(dlatest21.ActualBooking.mean() - dlatest20.ActualBooking.mean())) * 100 / dlatest20.ActualBooking.mean(), 
                                highorlow20n21 = 'higher' if (dlatest21.ActualBooking.mean() - dlatest20.ActualBooking.mean()) > 0 else 'lower',
                                andorbut = 'and' if (dlatest21.ActualBooking.mean() - dlatest19.ActualBooking.mean()) > 0 else 'but',
                                percentdiff21n19 = (abs(dlatest21.ActualBooking.mean() - dlatest19.ActualBooking.mean())) * 100 / dlatest19.ActualBooking.mean(), 
                                highorlow21n19 = 'higher' if (dlatest21.ActualBooking.mean() - dlatest19.ActualBooking.mean()) > 0 else 'lower'))
    qmodel_df1 = qmodel_df[['Date', 'ActualBooking']].copy()
    qmodel_df1.Date = pd.to_datetime(qmodel_df1.Date)
    qmodel_df1['Weekday'] = qmodel_df1.Date.dt.day_name()
    qmodel_df1['weekdayorweekend'] = qmodel_df1.Weekday.apply(lambda x: 'Weekend' if x in ['Saturday', 'Sunday'] else 'Weekday')
    qmodel_df2 = qmodel_df1[['weekdayorweekend', 'ActualBooking']].copy()
    df = qmodel_df2.groupby('weekdayorweekend').mean().reset_index()
    ratiobooking = (df[df.weekdayorweekend == 'Weekday'].ActualBooking.values / df[df.weekdayorweekend == 'Weekend'].ActualBooking.values)[0]
    bookingstats.append("The average number of bookings on Weekdays are {ratiobooking:.2f} times higher than weekends for the date range Jan-2019 till date.".format(ratiobooking = ratiobooking))
    datestr = ','.join([date + '-2021' for date in dlatest21copy.Date.values])
    last_char_index = datestr.rfind(",")
    datestr = datestr[:last_char_index] + " and " + datestr[last_char_index+1:]
    bookingstats.append("There are {num} anomalies found which is marked in red in the graph.".format(num=len(dlatest21copy), datestr = datestr))
    
    wrappedinptag = ptagwrap(bookingstats)
    
    return bookingstats, wrappedinptag

def statewiseanalysis_ytd(qmodel_df: pd.DataFrame()) -> str:
    """[The function used to perform statewise analysis on the data]

    Args:
        qmodel_df (pd.DataFrame): [The dataframe containing the bookings data]

    Returns:
        str: [The observations in the data with respect to state]
    """
    qmodel_df.Date = pd.to_datetime(qmodel_df.Date)
    dlatest = qmodel_df[(qmodel_df.Model_creation_date == qmodel_df.Model_creation_date.max()) & (qmodel_df.Date >= '2021-01-01')]
    avgBookings_state = dlatest[['State', 'ActualBooking']].groupby('State').mean().reset_index().sort_values(by='ActualBooking', ascending = False)

    fig = px.pie(avgBookings_state, values='ActualBooking', names='State', hole = .5, hover_data=['ActualBooking'])
    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend = False)
    fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)'})
    # fig.update_traces(textposition='inside', textinfo='percent+label')
    # fig.update_layout(coloraxis_showscale=False)
    fig.write_image("./static/images/pie_statesytd.png", engine='kaleido',format='png')

    highstatelist = ', '.join([item for item in avgBookings_state.State[:5].values])
    last_char_index = highstatelist.rfind(",")
    highstateliststr = highstatelist[:last_char_index] + " and" + highstatelist[last_char_index+1:]
    strstates = ["The top 5 states with highest booking YTD are {liststates}.".format(liststates = highstateliststr)]
    
    lowstatelist = ', '.join([item for item in avgBookings_state.State[-5:].values])
    last_char_index = lowstatelist.rfind(",")
    lowstateliststr = lowstatelist[:last_char_index] + " and" + lowstatelist[last_char_index+1:]
    strstates.append("The top 5 states with lowest booking YTD are {liststates}.".format(liststates = lowstateliststr))
    
    wrappedinptag = ptagwrap(strstates)
    return strstates, wrappedinptag

def divisionwiseanalysis(qmodel_df: pd.DataFrame) -> str:
    """[Function to perform divisionwise analysis on the data]

    Args:
        qmodel_df ([pd.DataFrame]): [ Input DataFrame containing raw data]

    Returns:
        [str]: [Observations based on division in the data]
    """
    dlatest = qmodel_df[(qmodel_df.Model_creation_date == qmodel_df.Model_creation_date.max())]
    dlatest.Date = pd.to_datetime(dlatest.Date)
    dlatest = dlatest[['Date', 'Division', 'ActualBooking']]#.groupby('Division').mean().reset_index()
    dlatest19 = dlatest[(dlatest.Date >= '2019-01-01') & (dlatest.Date < '2020-01-01')][['Division', 'ActualBooking']]
    dlatest20 = dlatest[(dlatest.Date >= '2020-01-01') & (dlatest.Date < '2021-01-01')][['Division', 'ActualBooking']]
    dlatest21 = dlatest[dlatest.Date >= '2021-01-01'][['Division', 'ActualBooking']]
    df19 = dlatest19.groupby('Division').mean().reset_index()
    df19.rename(columns={'ActualBooking':'2019'}, inplace=True)
    df20 = dlatest20.groupby('Division').mean().reset_index()
    df20.rename(columns={'ActualBooking':'2020'}, inplace=True)
    df1920 = pd.merge(df19, df20, how='inner', left_on='Division', right_on = 'Division')
    df21 = dlatest21.groupby('Division').mean().reset_index()
    df21.rename(columns={'ActualBooking':'2021'}, inplace=True)
    df192021 = pd.merge(df1920, df21, how = 'inner', left_on='Division', right_on='Division')
    #df192021 = np.round(df192021,0)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df192021.Division, y=df192021['2019'], name = '2019'))
    fig.add_trace(go.Bar(x=df192021.Division, y=df192021['2020'], name = '2020'))
    fig.add_trace(go.Bar(x=df192021.Division, y=df192021['2021'], name = '2021'))
    fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)'}, 
                  xaxis = dict(tickmode = 'linear', tickangle = -45), 
                  legend=dict(orientation="h", yanchor="bottom", y=0.95, xanchor="right", x=1, font = dict(size=10)))
    fig.write_image(r"./static/images/dailybookingdivision_barplot.png", engine='kaleido',format='png', height=400, width = 600)
    
    df192021['pChangein1921'] = (df192021['2021'] - df192021['2019']) * 100 / df192021['2019']
    df192021['pChangein2021'] = (df192021['2021'] - df192021['2020']) * 100 / df192021['2019']
    divisonstats = []
    divisonstats.append("The average number of bookings per division per day in 2021 is {avgbookings2021},  \
            which is {pamount1921:.1f}% {moreorless1921} from 2019 {andorbut} {pamount2021}% {moreless2021} from year 2020".\
            format(avgbookings2021 = format(int(df192021['2021'].mean()), ','), 
                pamount1921 = round(abs(df192021.pChangein1921.mean()),1), 
                moreorless1921 = 'less' if df192021.pChangein1921.mean() < 0 else 'more',
                andorbut = 'and' if df192021.pChangein2021.mean() > 0 else 'but',
                pamount2021 = round(abs(df192021.pChangein2021.mean()),1),
                moreless2021 = 'less' if df192021.pChangein2021.mean() < 0 else 'more'))
    divisonstats.append("The division {max_division} has recorded average highest number of per day booking of {maxbooking}.".\
            format(max_division = df192021.sort_values(by = '2021', ascending=False).head(1).Division.tolist()[0],
                maxbooking= format(int(df192021['2021'].max()), ',')))
    divisonstats.append("The division {min_division} has recorded lowest number of per day booking of {minbooking}.".\
            format(min_division = df192021.sort_values(by = '2021', ascending=True).head(1).Division.tolist()[0],
               minbooking = format(int(df192021['2021'].min()), ',')))
    
    wrappedinptag = ptagwrap(divisonstats)
    return divisonstats, wrappedinptag

def sendmail_html(htmlcontent: str) -> None:
    """[The sendmail function sends the html content to the email address]

    Args:
        htmlcontent (str): [The html content to be sent]
    """
    # Send an HTML email with an embedded image and a plain text message for
    # email clients that don't want to display the HTML.
    strFrom = 'abc@gmail.com'
    #strTo = 'binay.chandra@publicissapient.com, will.stokvis@publicismedia.com, john.keating@digitas.com, daniel.stroik@publicismedia.com'
    strTo = 'xyz123@gmail.com, abc456@gmail.com'
    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'Marriott Weekly Report'
    msgRoot['From'] = strFrom
    msgRoot['To'] = strTo
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    msgText = MIMEText(htmlcontent, 'html')
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    pngfileslist = glob(r'./static/images/*.png')
    for pngfile in pngfileslist:
        with open(pngfile, 'rb') as fp:
            msgImage = MIMEImage(fp.read())
            _, filename = os.path.split(pngfile)
        msgImage.add_header('Content-ID', '<{}>'.format(filename))
        msgRoot.attach(msgImage)  
    
    # Send the email (this example assumes SMTP authentication is required)
    smtp = smtplib.SMTP('smtp.gmail.com:587')
    smtp.ehlo()
    smtp.starttls()
    smtp.login("abc123@gmail.com", "<<xxxxyyyyyzzzzz>>")
    receivers = strTo.split(",") #+ receiver_bcc.split(",")
    smtp.sendmail(strFrom, receivers, msgRoot.as_string())
    smtp.quit()

def performanalysisandupdate(htmlinputcontent : str, qmodel_df : pd.DataFrame) -> str:
    """[This function is used to perform different analysis and update the html file]

    Args:
        htmlinputcontent ([str]): [The input HTML template file]

    Returns:
        [str]: [The updated HTML template file with the analysis results]
    """
    results_actualbookingstats = actualbookingstats(qmodel_df)
    htmlcontent = htmlinputcontent.replace("[[actualbookingstats]]", results_actualbookingstats)
    
    thisweekvslastweekobsptags = bookingcomparison_previousweek(qmodel_df)
    htmlcontent = htmlcontent.replace('[[thisweekvslastweekobservartions]]', thisweekvslastweekobsptags)
    
    thisweekvsyear2019obsptags = bookingcomparison_year2019(qmodel_df)
    htmlcontent = htmlcontent.replace('[[thisweekvsyear2019observartions]]', thisweekvsyear2019obsptags)
    
    statewiseanalysis_ytdstr = statewiseanalysis_ytd(qmodel_df)
    htmlcontent = htmlcontent.replace('[[statewiseanalysis_ytdobservartions]]', statewiseanalysis_ytdstr)
    
    divisionwiseanalysis_ytdstr = divisionwiseanalysis(qmodel_df)
    htmlcontent = htmlcontent.replace('[[divisionwiseanalysis_ytdobservartions]]', divisionwiseanalysis_ytdstr)
    
    return htmlcontent

def getbookingdf():
    startdate, enddate = '2019-01-01', datetime.now().strftime("%Y-%m-%d")
    dates = pd.date_range(start=startdate, end=enddate, freq='D')
    states_df = pd.read_csv(r"states.csv")
    usa_states = states_df.State.to_list()
    date_state_combinations = list(product(dates, usa_states))
    tempdf = pd.DataFrame(date_state_combinations, columns=['Date', 'State'])
    bookingdf = pd.merge(tempdf, states_df, left_on='State', right_on='State', how='inner')
    bookingdf['ActualBooking'] = np.random.randint(50, 1500, size=len(bookingdf))
    bookingdf['forecasted_booking'] = bookingdf['ActualBooking'] + random.randint(-50, 450)
    bookingdf['Model_creation_date'] = datetime.now().strftime('%Y-%m-%d')
    bookingdf.rename(columns={'State Code':'state_code', 'forecasted_booking':'forecast_avg_bqfb' }, inplace = True)
    return bookingdf

if __name__ == '__main__':

    # Read the bigquery query table data for bookings
    qmodel_df = getbookingdf()
    print(qmodel_df.head())

    # Read the HTML Template
    htmltemplate = r'templates\maildraft_template.html'
    with open(htmltemplate) as f: 
        rawhtmlcontent = f.read()
    
    # Call the functions Modify the HTML content with analysis results
    htmlcontent = performanalysisandupdate(rawhtmlcontent, qmodel_df)

    # Below code generates the PDF from HTML
    # Options for PDF generation (optional)
    # options = {
    #     'page-size': 'A4',
    #     'margin-top': '0mm',
    #     'margin-right': '0mm',
    #     'margin-bottom': '0mm',
    #     'margin-left': '0mm'
    # }
    # # Convert HTML to PDF
    # path_wkhtml2pdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    # config = pdfkit.configuration(wkhtmltopdf=path_wkhtml2pdf)
    # pdfkit.from_string(htmlcontent, "Weekly_Analysis.pdf", options=options, configuration=config)
    # Send the email with updated Html content
    sendmail_html(htmlcontent)
