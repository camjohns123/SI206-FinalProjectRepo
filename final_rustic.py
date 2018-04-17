import requests
import json
from bs4 import BeautifulSoup
import sqlite3
import plotly.plotly as py
import plotly.graph_objs as go
import countries_file

DBNAME = 'Rustic1.db'
#cache code
CACHE_FNAME = 'Rustic_Pathways_Scrape.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

except:
    CACHE_DICTION = {}

def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)

def make_request_using_cache(baseurl, params={}, auth=None):
    unique_ident = params_unique_combination(baseurl,params)
    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    else:
        # print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params, auth=auth)
        content_type = resp.headers.get('content-type')
        if content_type == 'application/json':
            CACHE_DICTION[unique_ident] = json.loads(resp.text)
        else:
            CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]

#creating the database
def init_db():
    print('Creating Database...')
    try:
        conn = sqlite3.connect('Rustic1.db')
        cur = conn.cursor()
    except Error as e:
        print(e)

    statement_drop_countries = '''
        DROP TABLE IF EXISTS 'Countries';
        '''

    cur.execute(statement_drop_countries)
    conn.commit()

    statement_countries_table = """
        CREATE TABLE Countries (
        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'Country' TEXT NOT NULL,
        'NumberPrograms' INTEGER
        );
    """
    cur.execute(statement_countries_table)
    conn.commit()

    # Drop table if already exists
    statement_drop_programs= '''
        DROP TABLE IF EXISTS 'Programs';
    '''
    cur.execute(statement_drop_programs)
    conn.commit()

    statement_programs_table = """
        CREATE TABLE Programs (
            'ProgramId' INTEGER PRIMARY KEY AUTOINCREMENT,
            'CountryId' INTEGER,
            'CountryName' TEXT,
            'ProgramName' TEXT,
            'MinAge' INTEGER,
            'MaxAge' INTEGER,
            'Length' INTEGER,
            'Cost' INTEGER,
            'AirfareIncluded' TEXT,
            'URL' TEXT
        );
    """
    cur.execute(statement_programs_table)
    conn.commit()
    conn.close()

#getting the program URL's
def get_programs():
    country_url = 'https://rusticpathways.com/programs/countries/australia/'
    country_request = make_request_using_cache(country_url)
    country_soup = BeautifulSoup(country_request, 'html.parser')
    country_results_list = country_soup.find('div', class_ = 'results')
    programs = country_results_list.find_all('li')
    program_url_list = []
    program_dictionary = {}
    for i in programs:
        program_url = i.find('a')['href']
        program_url_list.append(program_url)
    for link in program_url_list:
        link_request = make_request_using_cache(link)
        link_soup = BeautifulSoup(link_request, 'html.parser')
        program_attributes = link_soup.find(class_ = "attributes")
        if program_attributes is None:
            country_name = 'Gap'
        else:
            country_name_options = program_attributes.find('dd')
            country_name = country_name_options.find('a').text
        program_dictionary[country_name] = []

    for link in program_url_list:
        link_request = make_request_using_cache(link)
        link_soup = BeautifulSoup(link_request, 'html.parser')
        program_attributes = link_soup.find(class_ = "attributes")
        if program_attributes is None:
            country_name = 'Gap'
        else:
            country_name_options = program_attributes.find('dd')
            country_name = country_name_options.find('a').text
        program_dictionary[country_name].append(link)

    return program_dictionary

#scraping information on each program
def scrape_program_pages(url):
    trip_list = []
    trip_request = make_request_using_cache(url)
    trip_soup = BeautifulSoup(trip_request, 'html.parser')

    trip_results = trip_soup.find('ul', class_ = 'meta-list')
    trip_more_info = trip_results.find_all('li')

    #title
    trip_results= trip_soup.find('div', class_ = 'title-wrapper')
    trip_name_w_tab = trip_results.find('h1')
    trip_list.append(trip_name_w_tab.text.strip()) # index 0

    #ages
    ages = trip_more_info[0].text[6:].split('-')
    min_age = ages[0]
    trip_list.append(int(min_age)) # index 1
    max_age = ages[1]
    if max_age[0] == 'o':
        max_age = max_age[1:]
    trip_list.append(int(max_age)) # index 2

    #length
    length = trip_more_info[2].text.split()[1]
    trip_list.append(int(length)) # index 3

    #cost
    comma_cost = trip_more_info[3].text.split()[1][1:]
    cost = comma_cost.replace(',', '')
    trip_list.append(int(cost)) #index 4

    #airfare
    testing = trip_more_info[3].text.split()
    if testing.__contains__('plus'):
        airfare = 'No'
    else:
        airfare = 'Yes'
    trip_list.append(airfare) #index 5

    return trip_list

#getting data for the countries table
def get_countries_table_data():
    countries_list = ['Australia','Cambodia','China','Costa Rica','Cuba','Dominican Republic',
    'Fiji Islands','Laos','Mongolia','Morocco','Myanmar','Mystery Destination','Peru',
    'Tanzania','Thailand','United States','Vietnam', 'Gap']

    program_dictionary = get_programs()
    program_country = []
    program_num_dict = {}

    dictionary_keys = program_dictionary.keys()
    for i in dictionary_keys:
        if i not in program_num_dict:
            program_num_dict[i]  = 0
            for url in program_dictionary[i]:
                program_num_dict[i] += 1
        else:
            for url in program_dictionary[i]:
                program_num_dict[i] += 1
    final_countries =[]
    for x in countries_list:
        if x in program_num_dict.keys():
            final_countries.append((x,program_num_dict[x]))
        else:
            final_countries.append((x,0))
    return final_countries

#inserting data into the countries table
def insert_countries_data():
    try:
        conn = sqlite3.connect('Rustic1.db')
        cur = conn.cursor()
    except Error as e:
        print(e)

    final_countries = get_countries_table_data()

    cur.executemany("INSERT INTO Countries VALUES (NULL,?,?)", final_countries)
    conn.commit()
    print('Inserting Countries Data...')
    conn.close()

#inserting data into the programs table
def insert_programs_data():
    try:
        conn = sqlite3.connect('Rustic1.db')
        cur = conn.cursor()
    except Error as e:
        print(e)

    query = "SELECT * FROM COUNTRIES"
    cur.execute(query)
    conn.commit()

    country_mapping = {}
    for country in cur:
        id = country[0] # Country id
        name = country[1] # Country name
        country_mapping[name] = id

    program_dictionary = get_programs()
    final = [] # intialize "final" list
    for country, links in program_dictionary.items():
        for link in links:
            if link.__contains__('gap'):
                continue
            web_scrape = scrape_program_pages(link)
            program_name = web_scrape[0]
            min_age = web_scrape[1]
            max_age = web_scrape[2]
            length = web_scrape[3]
            cost = web_scrape[4]
            airfare = web_scrape[5]
            url = link
            clean_country = country.split(',')[0]
            countryid = country_mapping[clean_country]
            final.append((countryid, clean_country, program_name, min_age, max_age, length, cost, airfare, url))
    cur.executemany("INSERT INTO Programs VALUES (NULL,?,?,?,?,?,?,?,?,?)", final)
    conn.commit()
    print('Inserting Programs Data...')
    conn.close()

#creating a pie chart of the % of rustic programs in each country
def countries_pie_chart():
    conn = sqlite3.connect('Rustic1.db')
    cur = conn.cursor()

    statement = '''
    SELECT *
    FROM Countries
    '''

    cur.execute(statement)
    conn.commit()

    labels = []
    values = []
    for row in cur:
        labels.append(row[1])
        values.append(row[2])

    data = go.Pie(labels=labels, values=values)

    layout = go.Layout(title="Percent of all Rustic Programs by Country")

    fig = go.Figure(data=[data], layout=layout)

    plot = py.plot(fig, filename = 'basic-line')
    cur.close()
    return plot

#creating a bar chart of the number of programs for each minimum age in a given country
def min_age_bar_chart(country):

    conn = sqlite3.connect('Rustic1.db')
    cur = conn.cursor()

    statement = '''
    SELECT ProgramName, MinAge
    FROM Programs
    WHERE CountryName = '''

    statement += '"' + country + '"'

    country_min_age = cur.execute(statement).fetchall()
    conn.commit()

    min_age_counter= {}
    for row in country_min_age:
        if row[1] in min_age_counter.keys():
            min_age_counter[row[1]] += 1
        else:
            min_age_counter[row[1]] = 1

    x_list = []
    for i in min_age_counter.keys():
        x_list.append(i)

    y_list = []
    for i in  min_age_counter:
        y_list.append(min_age_counter[i])

    data = [go.Bar(x= x_list , y = y_list,
        text=y_list,
        textposition = 'auto',
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
        ),
        opacity=0.6)]

    layout = dict(title = 'Number of Programs for Each Minimum Age in a Given Country')

    fig = dict(data=data, layout=layout)

    plot = py.plot(fig, filename='Min_age_basic_bar')
    cur.close()
    return plot

#creating a bar chart of the number of programs for each maximum age in a given country
def max_age_bar_chart(country):

    conn = sqlite3.connect('Rustic1.db')
    cur = conn.cursor()

    statement = '''
    SELECT ProgramName, MaxAge
    FROM Programs
    WHERE CountryName = '''

    statement += '"' + country + '"'

    country_max_age = cur.execute(statement)
    conn.commit()

    max_age_counter= {}
    for row in country_max_age:
        if row[1] in max_age_counter.keys():
            max_age_counter[row[1]] += 1
        else:
            max_age_counter[row[1]] = 1

    x_list = []
    for i in max_age_counter.keys():
        x_list.append(i)

    y_list = []
    for i in  max_age_counter:
        y_list.append(max_age_counter[i])

    data = [go.Bar(x= x_list , y = y_list,
            text=y_list,
            textposition = 'auto',
            marker=dict(
                color='rgb(158,202,225)',
                line=dict(
                    color='rgb(8,48,107)',
                    width=1.5),
            ),
            opacity=0.6
        )]

    layout = dict(title = 'Number of Programs for Each Maximum Age in a Given Country')

    fig = dict(data=data, layout=layout)

    plot = py.plot(fig, filename='Max_age_basic_bar')
    cur.close()
    return(plot)

#creating a scatterplot for the cost of every program in a given country
def cost_scatter(country):

    conn = sqlite3.connect('Rustic1.db')
    cur = conn.cursor()

    statement = '''
    SELECT ProgramName, Cost
    FROM Programs
    WHERE CountryName = '''

    statement += '"' + country + '"'

    country_cost = cur.execute(statement).fetchall()
    conn.commit()


    x_list = []
    y_list = []
    for row in country_cost:
        x_list.append(row[0])
        y_list.append(row[1])
    trace = go.Scatter(
        x = x_list,
        y = y_list,
        mode = 'markers'
        )

    data = [trace]

    layout = go.Layout({
      "autosize": False,
      "font": {"family": "Balto"},
      "height": 500,
      "hovermode": "closest",
      "plot_bgcolor": "rgba(240,240,240,0.9)",
      "title": "Cost of Programs in Country Scatterplot",
      "width": 700,
      "xaxis": {
        "gridcolor": "rgb(255,255,255)",
        "mirror": True,
        "showline": True,
        "ticklen": 4,
        "title": "Program Name",
        "zeroline": False,
      },
      "yaxis": {
        "gridcolor": "rgb(255,255,255)",
        "mirror": True,
        "showline": True,
        "ticklen": 4,
        "title": "Cost ($)",
        "zeroline": False}})

    fig = dict(data=data, layout=layout)

    plot = py.plot(fig, filename='cost_basic_scatter')
    conn.close()
    return plot

#a boxplot of the length of the programs in all countries
def length_boxplot():

    conn = sqlite3.connect('Rustic1.db')
    cur = conn.cursor()

    statement = '''
    SELECT CountryName, Length
    FROM Programs
    '''

    country_length = cur.execute(statement)
    conn.commit()

    length_mapping = {}
    for row in country_length:
        if row[0] not in length_mapping.keys():
            length_mapping[row[0]] = []
        country = row[0]
        length = row[1]
        length_mapping[country].append(length)

    lengths = []
    for country in length_mapping:
        country = go.Box(
        y=length_mapping[country],
        name = country
        )
        lengths.append(country)

    data = lengths
    layout = dict(title = 'Length of Programs for all Countries Boxplots',
            )
    fig = dict(data=data, layout=layout)

    plot = py.plot(fig, filename='length_basic_boxplot')
    conn.close()
    return plot

#a bubble graph which depics the cost of the program by length for a specified country
def cost_length_bubble(country):

    conn = sqlite3.connect('Rustic1.db')
    cur = conn.cursor()

    statement = '''
    SELECT Cost, Length
    FROM Programs
    WHERE CountryName = '''

    statement += '"' + country + '"'

    bubble_Data = cur.execute(statement).fetchall()
    conn.commit()

    x_list = []
    y_list = []
    for row in bubble_Data:
        x_list.append(row[0])
        y_list.append(row[1])

    trace0 = go.Scatter(
    x=x_list,
    y=y_list,
    mode='markers',
    marker=dict(
        size=[40, 60, 80, 100],
    ))

    data = [trace0]

    layout = dict(title = 'Cost of Programs by Length for Country',
    xaxis=dict(title='Cost of Program ($)'),
    yaxis=dict(title='Length of Program (Days)'),)

    fig = dict(data=data, layout=layout)

    plot = py.plot(fig, filename='bubblechart-size')
    conn.close()
    return plot



if __name__=="__main__":
    #to initially create and populate the database
    # init_db()
    # insert_countries_data()
    # insert_programs_data()

    option = ""
    base_prompt = """
        Enter command (or "help" for options):
        Command: """
    feedback = ""
    while True:
        action = input(feedback + "\n" + base_prompt)
        feedback = ""
        action = action.lower()
        user_request = action.split(' ')
        if len(user_request) == 0:
            print("Please write a request.")
            continue

        elif action == "exit":
            print("""Exiting the program...""")
            break

        elif action == 'country list':
            countries_list = ['australia','cambodia','china','costa rica','cuba','dominican republic',
            'fiji islands','laos','mongolia','morocco','myanmar','mystery destination','peru',
            'tanzania','thailand','united states','vietnam']
            for x in countries_list:
                print(x)

        elif action == 'create database':
            init_db()
            insert_countries_data()
            insert_programs_data()

        elif action == "programs pie chart":
            print("""Creating Pie Chart...""")
            countries_pie_chart()

        elif action[:7] == "min age":
            if len(user_request) < 3:
                print("Invalid Input. Request a country.")
                continue
            elif len(user_request) == 3:
                if user_request[-1] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Bar Chart...""")
                bar_chart = min_age_bar_chart(user_request[-1].capitalize())
            elif len(user_request) == 4:
                country = user_request[-2].capitalize()
                country += " "
                country += user_request[-1].capitalize()
                if action[8:] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Bar Chart...""")
                bar_chart = min_age_bar_chart(country)

        elif action[:7] == "max age":
            if len(user_request) < 3:
                print("Invalid Input. Request a country.")
                continue
            elif len(user_request) == 3:
                if user_request[-1] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Bar Chart...""")
                bar_chart = max_age_bar_chart(user_request[-1].capitalize())
            elif len(user_request) == 4:
                country = user_request[-2].capitalize()
                country += " "
                country += user_request[-1].capitalize()
                print(country)
                if action[8:] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Bar Chart...""")
                bar_chart = max_age_bar_chart(country)

        elif action[:12] == "cost scatter":
            if len(user_request) < 3:
                print("Invalid Input. Request a country.")
                continue
            elif len(user_request) == 3:
                if user_request[-1] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Scatter Plot...""")
                scatter_plot = cost_scatter(user_request[-1].capitalize())
            elif len(user_request) == 4:
                country = user_request[-2].capitalize()
                country += " "
                country += user_request[-1].capitalize()
                if action[13:] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Scatter Plot...""")
                scatter_plot = cost_scatter(country)

        elif action[:11] == 'cost length':
            if len(user_request) < 3:
                print("Invalid Input. Request a country.")
                continue
            elif len(user_request) == 3:
                if user_request[-1] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Bubble Graph...""")
                bubble_graph = cost_length_bubble(user_request[-1].capitalize())
            elif len(user_request) == 4:
                country = user_request[-2].capitalize()
                country += " "
                country += user_request[-1].capitalize()
                if action[12:] not in countries_file.countries_list:
                    print("Invalid input. Try a different country.")
                    continue
                print("""Creating Bubble Graph...""")
                bubble_graph = cost_length_bubble(country)

        elif action == "program length boxplot":
            print("""Creating BoxPlot...""")
            length_boxplot()

        elif action == "help":
            large_menu = """
    programs pie chart
        creating a pie chart of the percent of rustic programs in each country
        valid inputs: programs pie chart

    min age <country>
        creating a bar chart of the number of programs for each minimum age in the specified country
        valid inputs: min age country (from the available list)

    max age <country>
        creating a bar chart of the number of programs for each maximum age in the specified country
        valid inputs: max age country (from the available list)

    cost scatter <country>
        creating a scatterplot for the cost of every program in the specified country
        valid inputs: cost scatter country (from the available list)

    length boxplot
        creating a boxplot of the length of the programs in all countries
        valid inputs: length boxplot

    cost length <country>
        creating bubble graph which depics the cost of the program by length for
        a specified country
        valid inputs: cost length country (from the available list)

    country list
        prints a list of the countries available to use as an input
        valid inputs: country list

    exit
        Exits the Program

    help
        Lists Available Commands (these instructions)"""
            print(large_menu)

        else:
            print("I didn't understand that. Please make a new request.")
