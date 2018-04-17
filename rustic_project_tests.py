import unittest
from final_rustic import *


class TestPrograms(unittest.TestCase):

    def test_programs_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT CountryName FROM Programs'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Fiji Islands',), result_list) #1
        self.assertEqual(len(result_list), 104) #2
        self.assertIn(('Laos',), result_list) #3

        sql = '''
            SELECT ProgramName, [Length], Cost
            FROM Programs
            WHERE CountryName = 'Costa Rica'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 16) #4
        self.assertEqual(result_list[0][-1], 4495) #5

        sql = '''
            SELECT ProgramName, AirfareIncluded
            FROM Programs
            WHERE AirfareIncluded = "Yes"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 1) #6

        sql = '''
            SELECT ProgramName, CountryName, [Length]
            FROM Programs
            WHERE CountryName = 'Thailand'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertTrue(result_list[-2], 25) #7

        sql = '''
        SELECT Count(*)
        FROM Programs
        WHERE CountryName = 'Myanmar'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][0], 2) #8
        self.assertEqual(len(result_list), 1) #9

        sql = '''
        SELECT AVG(Cost)
        FROM Programs
        WHERE CountryId = '7'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][0], 3675.0) #10

        conn.close()

class TestCountries(unittest.TestCase):

    def test_countries_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Country, NumberPrograms
            FROM Countries
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn('Australia', result_list[0]) #11
        self.assertEqual(len(result_list), 18) #12
        self.assertTrue(result_list[-1][-1], 3) #13

        conn.close()

class TestJoins(unittest.TestCase):
    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT ProgramName
            FROM Programs
                JOIN Countries
                ON Programs.CountryId=Countries.Id
            WHERE Programs.Length > "16"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertNotEqual(result_list[1][0], 'Race in America') #14
        self.assertEqual(len(result_list), 23) #15

        conn.close()

class TestScraping(unittest.TestCase):
    def test_page_scrape(self):
        results = scrape_program_pages('https://rusticpathways.com/programs/young-explorers-land-down-under/')
        self.assertEqual(results[1], 12) #16
        self.assertEqual(len(results), 6) #17

    def test_page_scrape2(self):
        results = scrape_program_pages('https://rusticpathways.com/programs/come-with-nothing-the-mekong-expedition/')
        self.assertEqual(results[-1], 'No') #18
        self.assertIn((4795), results) #19

    def test_page_scrape3(self):
        results = scrape_program_pages('https://rusticpathways.com/programs/njoro-village-service-immersion/')
        self.assertEqual(results[-3], 9) #20
        self.assertEqual(results[-2], 2495) #21

class TestProcessing(unittest.TestCase):
    def test_mapping_dictionary(self):
        results = get_countries_table_data()
        self.assertEqual(results[1][-1], 4) #22
        self.assertEqual(results[-2][0], 'Vietnam') #23

unittest.main()
