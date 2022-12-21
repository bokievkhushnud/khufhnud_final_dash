import pandas as pd
import sqlite3
import os
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from plotly.graph_objs import *
import requests
from bs4 import BeautifulSoup

connect = sqlite3.connect("hr")

data_ex2_employeee = pd.read_sql(
    "SELECT employees.first_name, jobs.job_title "
    + "FROM employees "
    + "INNER JOIN jobs ON employees.job_id "
    + "= jobs.job_id",
    connect,
)
salary = pd.read_sql("SELECT job_title, min_salary, max_salary FROM jobs", connect)
salary.drop(index=0, axis=0, inplace=True)
job_titles = data_ex2_employeee.groupby("job_title").count().index

# Question 2
def q2(jobs):
    employee_job = data_ex2_employeee
    if jobs == "All":
        job_count = employee_job.groupby("job_title").count().reset_index()
        job_count.columns = ["Job Title", "Count"]
    else:
        employee_job = employee_job[employee_job.job_title.isin(jobs)]
        job_count = employee_job.groupby("job_title").count().reset_index()
        job_count.columns = ["Job Title", "Count"]

    fig = px.bar(job_count, x="Job Title", y="Count")
    return fig


def q3(min_val, max_val):

    js = salary
    js["difference"] = js["max_salary"] - js["min_salary"]
    dx = int(max_val) - int(min_val)
    js = js[js["difference"] <= dx]
    fig = px.bar(js, x=js.difference, y=js.job_title, orientation="h")
    fig["layout"]["yaxis"]["title"] = "Job Title"

    return fig

def clear_df(element):
    if element == "-":
        return 0
    else:
        element = element[1:]
        element = element.replace(",","")
        return float(element)

def parsing_website():
    global hd
    URL = "https://www.itjobswatch.co.uk/jobs/uk/sqlite.do"
    requests.get(URL)
    s = BeautifulSoup(requests.get(URL).content, "html5lib")
    tab = s.find("table", attrs={"class": "summary"})
    tab.find("form").decompose()
    table_data = tab.tbody.find_all("tr")
    tab = []
    for i in table_data:
        row = []
        tdata = i.find_all("td")
        if len(tdata) == 0:
            tdata = i.find_all("th")
        for j in tdata:
            row.append(j.text)
        tab.append(row)

    hd = tab[1]
    hd[0] = "index"
    employee_sal = pd.read_sql("SELECT employees.salary " + "FROM employees", connect)
    avg_salary = employee_sal["salary"].mean()
    df = pd.DataFrame(tab)
    df.drop(index=[0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 14, 15], axis=0, inplace=True)
    df.columns = hd
    df.set_index("index", inplace=True)
    df.reset_index(inplace=True)
    hd = hd[1:]
    for i in hd:
        df[i] = df[i].apply(clear_df)

    df.loc[4] = ["Average", avg_salary, avg_salary, avg_salary]
    return df


df = parsing_website()


def q4(year):
    dframe = df[year]
    colors = ["green", "green", "green", "green", "black"]
    fig = px.scatter(
        x=df["index"], y=dframe, color=colors, color_discrete_map="identity"
    )
    fig.update_traces(marker_size=15)
    fig["layout"]["yaxis"]["title"] = "Count"
    fig["layout"]["xaxis"]["title"] = "Percentile"

    return fig


# App
app = Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server


app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.Div(
                    className="header",
                    children=[
                        html.H2("DASH - HUMAN RESOURCE"),
                        html.P(
                            """Filter Data using different Filters such as Jobs, Salary Difference and Years"""
                        ),
                    ]
                ),
                # Filter
                html.Div(
                    className="container",
                    children=[
                        html.Div(
                            className="div-for-dropdown controller",
                            children=[
                                html.P("Jobs:"),
                                dcc.Dropdown(
                                    id="job-title-filter",
                                    multi=True,
                                    options=job_titles,
                                    value="All",
                                ),
                            ],
                        ),
                        dcc.Graph(id="g1"),
                        html.Div(
                            className="div-for-dropdown controller",
                            children=[
                                html.P("Salary Difference:"),
                                dcc.RangeSlider(
                                    0,
                                    20000,
                                    1000,
                                    value=[0, 20000],
                                    id="slider1",
                                ),
                            ],
                        ),
                        dcc.Graph(id="g2"),
                        html.Div(
                            className="div-for-dropdown controller",
                            children=[
                                html.P("Years: "),
                                dcc.Dropdown(
                                    id="years-filter",
                                    options=parsing_website().columns[1:],
                                    value=parsing_website().columns[-1],
                                ),
                            ],
                        ),
                        dcc.Graph(id="g3"),
                    ]
                ),
            ],
        ),
    ]
)

@app.callback(
    [
        Output("g1", "figure"),
        Output("g2", "figure"),
        Output("g3", "figure"),
    ],
    [
        Input("job-title-filter", "value"),
        Input("slider1", "value"),
        Input("years-filter", "value"),
    ],
)
def update_output(jobs, slider, year):
    if jobs == None or len(jobs) == 0:
        jobs = "All"
    return q2(jobs), q3(slider[0], slider[1]), q4(year)


if __name__ == "__main__":
    app.run_server("0.0.0.0", debug=False, port=int(os.environ.get("PORT", 8000)))
