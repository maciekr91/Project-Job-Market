import pandas as pd
import pickle
import plotly.express as px
import plotly.graph_objs as go
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
from datetime import datetime, timedelta, date

offers_db = pickle.load(open('offers_db', 'rb'))
offers_db['added_at'] = pd.to_datetime(offers_db['added_at'])

app = dash.Dash()

interactive_elements_style = {'width': '300px', 'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'top'}

app.layout = html.Div(
    children=[
        html.H1("Job Market Dashboard", style={'font-size': '50px'}),
        html.Div([
            "Database created at: ",
            html.B(datetime.strftime(offers_db.added_at.min(), '%Y-%m-%d')),
            html.Br(),
            "Last update: ",
            html.B(datetime.strftime(offers_db.added_at.max(), '%Y-%m-%d'))
        ], style={'margin-bottom':'20px'}),
        html.Div([
            html.Label('Choose site:'),
            dcc.Dropdown(id='site_dd',
                         options=[
                             {'label': 'All', 'value': 'All'},
                             {'label': 'justjoin.it', 'value': 'justjoin.it'},
                             {'label': 'pracuj.pl', 'value': 'pracuj.pl'}
                         ],
                         style={'height': '50px'},
                         value='All',
                         clearable=False)], style=interactive_elements_style),
        html.Div([
            html.Label('Choose experience level:'),
            dcc.Dropdown(id='exp_dd',
                         options=[
                             {'label': 'All', 'value': 'All'},
                             {'label': 'Junior', 'value': 'junior'},
                             {'label': 'Mid', 'value': 'mid'},
                             {'label': 'Senior', 'value': 'senior'},
                             {'label': 'C-level', 'value': 'c-level'},
                         ],
                         style={'height':'50px'},
                         value='All',
                         clearable=False)], style=interactive_elements_style),
        html.Div([
            html.Label('Choose date range:'),
            dcc.DatePickerRange(id='date_range',
                                initial_visible_month=datetime.now(),
                                start_date=date.today() - timedelta(days=7),
                                end_date=date.today(),
                                style={'height': '50px'}
                                )], style=interactive_elements_style),
        dcc.Graph(id='salary_hist', style={'width':'70%', 'display':'inline-block'}),
        dcc.Graph(id='exp_pie', style={'width':'30%', 'display':'inline-block'})
    ])

@app.callback(
    Output('exp_pie', 'figure'),
    Input('site_dd', 'value'),
    Input('exp_dd', 'value'),
    Input('date_range', 'start_date'),
    Input('date_range', 'end_date')
)
def update_pie(selected_site, selected_exp, start_date, end_date):
    if selected_site == 'All':
        filtered_df = offers_db
    else:
        filtered_df = offers_db[offers_db['site'] == selected_site]

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)

    filtered_df = filtered_df[
        (filtered_df['added_at'] >= start_date) & (filtered_df['added_at'] < end_date)
    ]

    exp_dist = filtered_df['experience'].value_counts(normalize=True)

    if selected_exp == 'All':
        colors = px.colors.sequential.Hot
        pull = [0,0,0,0]
    else:
        colors = ['lightgrey' if exp != selected_exp else '#FF5733' for exp in exp_dist.index]
        pull = [0 if exp != selected_exp else 0.1 for exp in exp_dist.index]

    fig = go.Figure(data=[go.Pie(
        labels=exp_dist.index, values=exp_dist.values,
        marker=dict(colors=colors), pull=pull,
        textinfo='percent'
    )])

    fig.update_layout({
        'title':{
            'text': 'Number of offers due to experience',
            'font':{'size':24, 'color':'black'}
            }, 'title_x':0.5, 'title_y':0.95
    })

    return fig


@app.callback(
    Output('salary_hist', 'figure'),
    Input('site_dd', 'value'),
    Input('exp_dd', 'value'),
    Input('date_range', 'start_date'),
    Input('date_range', 'end_date')
)
def update_hist(selected_site, selected_exp, start_date, end_date):
    if selected_site == 'All':
        filtered_df = offers_db
    else:
        filtered_df = offers_db[offers_db['site'] == selected_site]

    if selected_exp != 'All':
        filtered_df = filtered_df[filtered_df['experience'] == selected_exp]

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)

    filtered_df = filtered_df[
        (filtered_df['added_at'] >= start_date) & (filtered_df['added_at'] < end_date)
    ]

    fig = px.histogram(data_frame=filtered_df, x='salary_avg', color_discrete_sequence=['#FF5733'])

    annotation = (f"Number of offers: <b>{filtered_df.shape[0]}</b><br>"
                  f"Offers with salary ranges: <b>{filtered_df.salary_avg.notna().sum()}</b><br>"
                  f"Median salary: <b>{filtered_df.salary_avg.median()}</b>")
    fig.update_layout({
        'title':{
            'text': 'Histogram of salaries',
            'font':{'size':24, 'color':'black'}
            }, 'title_x':0.5, 'title_y':0.95,
        'annotations':[{
            'showarrow': False,
            'text': annotation,
            'xref':'paper', 'yref':'paper', 'x':0.9, 'y':0.9,
            'font':{'size':18},
            'align':'left'
        }],
        'xaxis':{'title': {'text':'Declared average salary in offered position'}},
        'yaxis': {'title': {'text': 'Number of offers'}}
    })
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
