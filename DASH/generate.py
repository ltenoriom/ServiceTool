#!/usr/bin/python3
# This script is the CLI frontend

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import csv
import pandas as pd

if __name__ == '__main__':
    Names = "Name"
    #headers = ["open","closed","survey_sent","survey_received","surveys","CSAT","CES","NPS","Resolution","PerC_witout_Violations"]
    df = pd.read_csv('satisfaction.csv')
    headers= df.columns.tolist()
    del headers[0]




    f = open("generate_it.py", "w")
    
    f.write('''#!/usr/bin/python3
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px

df = pd.read_csv('satisfaction.csv')

    ''')

    for head in headers: 
        print(head)
        f.write('\npd_%s = pd.DataFrame({"User": (df["%s"]),"Amount": (df["%s"]),})\n'  % (head,Names,head))
        f.write("fig_%s = px.bar(pd_%s, x=\"User\", y=\"Amount\", text=\"Amount\", barmode=\"group\")\n" % (head,head))

    f.write('\n')
    f.write('''

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[

html.H1(children='NA Linux Team Review'),
    ''')
    for head in headers: 
        f.write("html.Div(children=\'%s\'),dcc.Graph(id='id_%s',  figure=fig_%s),\n" % (head,head,head))

    f.write("])\n\n")
    f.write('''
if __name__ == '__main__':
    app.run_server(debug=True)
    ''')
