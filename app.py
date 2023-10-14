from flask import Flask, render_template
import pandas as pd
from datetime import datetime
from draft_mailscript import *

app = Flask(__name__, static_url_path='/static')

@app.route("/", methods=['GET'])
def index():
    bookingdf = getbookingdf()
    bookingstats, results_actualbookingstats = actualbookingstats(bookingdf)
    thisweekvslastweekobs, thisweekvslastweekobsptags = bookingcomparison_previousweek(bookingdf)
    thisweekvsyear2019obs, thisweekvsyear2019obsptags = bookingcomparison_year2019(bookingdf)
    statewiseanalysis_ytdstr, statewiseanalysis_ytdstrptag = statewiseanalysis_ytd(bookingdf)
    divisionwiseanalysis_ytdstr, divisionwiseanalysis_ytdstrptag = divisionwiseanalysis(bookingdf)

    return render_template("maildraftv1.html",
                           results_actualbookingstats = bookingstats,
                           thisweekvslastweekobs = thisweekvslastweekobs, 
                           thisweekvsyear2019obs = thisweekvsyear2019obs, 
                           statewiseanalysis_ytdstr=statewiseanalysis_ytdstr,
                           divisionwiseanalysis_ytdstr=divisionwiseanalysis_ytdstr)

#if __name__ == '__main__':
#    app.run(host="0.0.0.0", port=8090)
#    #app.run(debug=True)
