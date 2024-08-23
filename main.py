import json

import os
import time
from selenium import webdriver
from datetime import datetime, timedelta
import calendar
import boto3

from selenium.webdriver.common.by import By

BOOKING_DAYS = ['MONDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
DATE_STRFMT = '%m/%d/%Y'
AWS_REGION = 'us-west-2'


class UcsdTennisBooker:
    def __init__(self):

        self._boto3_session = boto3.session.Session()
        self._secrets_manager = self._boto3_session.client('secretsmanager', region_name=AWS_REGION)
        get_secret_value_response = self._secrets_manager.get_secret_value(
            SecretId='uscd-recreation-signin'
        )
        secret_dict = json.loads(get_secret_value_response['SecretString'])
        self._email = secret_dict['email']
        self._password = secret_dict['password']

        option = webdriver.ChromeOptions()
        option.add_argument('--headless')
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-gpu')
        self._driver = webdriver.Chrome(options=option)
        self._driver.get('https://rec.ucsd.edu/booking/674570b3-464b-4fd2-9d27-72ea02068d1d')

        self._booked_dates = set()
        self._load_booked_dates()

    def _load_booked_dates(self):
        try:
            file = open("booked_dates.txt", "r")
            for line in file:
                self._booked_dates.add(datetime.strptime(line.strip(), DATE_STRFMT).date())
        except:
            # File might not exist.
            pass

    @staticmethod
    def _store_booked_date(day):
        file = open("booked_dates.txt", "w")
        file.write(day.strftime(DATE_STRFMT))

    def sign_in(self):

        email_filled = False
        for _ in range(10):
            try:
                email_field = self._driver.find_element(by=By.ID, value="txtEmailUsernameLogin")
                email_field.send_keys(self._email)

                email_filled = True
                break
            except:
                time.sleep(0.2)

        if not email_filled:
            raise Exception("failed to fill email field")

        password_filled = False
        for _ in range(10):
            try:
                next_button = self._driver.find_element(by=By.ID, value="btnNextSignInFirst")
                next_button.click()

                password_field = self._driver.find_element(by=By.ID, value="txtSignInPassword")
                password_field.send_keys(self._password)

                sign_in_button = self._driver.find_element(by=By.ID, value="btnSignIn")
                sign_in_button.click()

                password_filled = True
                break
            except:
                time.sleep(0.2)

        if not password_filled:
            raise Exception("failed to fill password field")

    @staticmethod
    def _build_day_selection_name(date):
        accessible_name = f'{calendar.day_name[date.weekday()].upper()}, {date.strftime("%B").upper()} {date.day}, {date.year}'
        return accessible_name

    def navigate_to_day(self, date):
        accessible_name = self._build_day_selection_name(date)
        for _ in range(10):
            day_selection_buttons = self._driver.find_elements(by=By.CLASS_NAME, value="single-date-select-button")
            for button in day_selection_buttons:
                if button.accessible_name == accessible_name:
                    button.click()
                    return
            time.sleep(0.2)
        raise Exception("Failed to find day selection button")

    def book_slot(self, date):
        if date.date() in self._booked_dates:
            print(f"{date} already booked")
            return

        for _ in range(10):
            booking_buttons = self._driver.find_elements(by=By.XPATH, value="/html/body/div[1]/div/div[5]/div[1]/div[2]/div[12]/div[2]/div[9]/div/button")
            for button in booking_buttons:
                button.click()
                self._store_booked_date(date)
                print(f"Successfully booked {date.strftime('%m/%d/%Y')}!")
                return
            time.sleep(0.2)
        raise Exception("Failed to find time slot button")


driver = UcsdTennisBooker()
driver.sign_in()

print("sign in successful")

# for i in range(1):
#     date = datetime.today() + timedelta(days=i)
#     if calendar.day_name[date.weekday()].upper() not in BOOKING_DAYS:
#         continue
#
#     try:
#         driver.navigate_to_day(date)
#         driver.book_slot(date)
#         booking_made = True
#     except Exception as e:
#         print(f"Unable to book {date.strftime('%m/%d/%Y')}: {e}")