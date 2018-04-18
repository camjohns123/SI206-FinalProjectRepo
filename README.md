Data Sources:
I scraped the Rustic Pathways website (https://rusticpathways.com/programs/countries/australia/).
This website does not require any API keys or client secrets.

My code is set up with an interactive portion. The user can choose what graphs to present.
Here is the interactive code so you can familiarize yourself with the different command options.
Interactive code:
    create database
        creates the database and populates the tables
        valid inputs: create database

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
        Lists Available Commands (these instructions)


The graphs are displayed through plotly. To get started with plotly.
Follow these steps to use plotly:
1. Make a plotly account.
2. Install plotly on your computer
3. Get a plotly API key
4. Set up a plotly credentials file (this will have your username and api key)


Based on the command a user enters, a particular graph or text is displayed.

My code is structured as a series of functions that get called through the different interactive prompt commands.
The most important functions I have are insert_countries_data() and insert_programs_data(). These functions populate the tables I created with information scraped form the webpage. I have also reference a file called countries_file.py. This file contains a list of all the countries in which Rustic Pathways offers programs. I use this as a reference for user inputs.
