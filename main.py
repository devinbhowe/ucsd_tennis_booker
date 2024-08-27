import json

import os
import time
from selenium import webdriver
from datetime import datetime, timedelta
import calendar
import boto3

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

DATE_STRFMT = '%m/%d/%Y'
CONFIG_NAME = 'ucsd-tennis-booking'
DYNAMO_AWS_REGION = 'us-west-2'


class UcsdTennisBooker:
    def __init__(self):

        boto3_session = boto3.session.Session()

        # Get the config from AWS.
        dynamodb = boto3_session.resource('dynamodb', region_name=DYNAMO_AWS_REGION)
        dynamodb_table = dynamodb.Table('configs')
        config_response = dynamodb_table.get_item(Key={'config': CONFIG_NAME})

        self._aws_region = config_response['Item']['region']
        self._booking_days = {}
        dic = dict(config_response['Item']['booking_times'])
        for day in dic:
            self._booking_days[day] = list(dic[day])

        # Get the username/password from AWS.
        secrets_manager = boto3_session.client('secretsmanager', region_name=self._aws_region)
        get_secret_value_response = secrets_manager.get_secret_value(
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
                print("sign in successful")
                break
            except:
                time.sleep(0.2)

        if not password_filled:
            raise Exception("failed to fill password field")

    @staticmethod
    def _build_day_selection_names(date):
        # The name will be long or short depending on screen size.
        long_name = f'{calendar.day_name[date.weekday()].upper()}, {date.strftime("%B").upper()} {date.day}, {date.year}'
        short_name = f'{date.day} {calendar.day_name[date.weekday()].upper()[:3]}'
        return [long_name, short_name]

    def navigate_to_day(self, date):
        accessible_names = self._build_day_selection_names(date)
        in_day_selection_tab = False
        for _ in range(10):
            try:
                day_selector = self._driver.find_element(by=By.XPATH, value='/html/body/div[1]/div/div[5]/div[1]/div[2]/div[9]/div[3]/div[1]/button')
                day_selector.click()
                in_day_selection_tab = True
            except:
                # Depending on screen size this may not exist and the selection buttons will be expanded.
                pass

            day_selection_buttons = self._driver.find_elements(by=By.CLASS_NAME, value="single-date-select-button")
            for button in day_selection_buttons:
                if button.accessible_name in accessible_names:
                    button.click()
                    if in_day_selection_tab:
                        apply_day_button = self._driver.find_element(by=By.ID, value='btnApplySelectedDate_00000000-0000-0000-0000-000000000000')
                        apply_day_button.click()
                    return

            time.sleep(0.05)
        raise Exception("Failed to find day selection button")

    @staticmethod
    def _printable_hour(hour):
        if hour > 12:
            return f'{hour % 12}PM'
        else:
            return f'{hour}AM'

    def book_slot(self, date, hours):
        for hour in hours:
            for i in range(10):
                if date.date() == date.today().date():
                    slot = hour - datetime.now().hour + 1
                else:
                    slot = hour - 6  # Bookings start at 7AM, but past ones disappear.
                try:
                    booking_buttons = self._driver.find_elements(by=By.XPATH, value=f'/html/body/div[1]/div/div[5]/div[1]/div[2]/div[12]/div[2]/div[{slot}]/div/button')
                    if len(booking_buttons) != 1:
                        # If this element exists we already have the booked.
                        already_booked_elements = self._driver.find_elements(by=By.XPATH, value=f'/html/body/div[1]/div/div[5]/div[1]/div[2]/div[12]/div[2]/div[{slot}]/div/div/button')
                        if len(already_booked_elements) > 0:
                            print(f'{date.strftime("%m/%d/%Y")} {self._printable_hour(hour)} - Already booked by us.')
                            break
                        else:
                            raise Exception("Couldn't find booking button nor booked button")

                    booking_button = booking_buttons[0]
                    if booking_button.accessible_name == 'UNAVAILABLE':
                        print(f'{date.strftime("%m/%d/%Y")} {self._printable_hour(hour)} - Already booked by someone else.')
                        break
                    booking_button.click()
                    print(f'{date.strftime("%m/%d/%Y")} {self._printable_hour(hour)} - Successfully booked.')
                    break
                except:
                    if i == 9:
                        raise
                    time.sleep(0.05)

    def book_all_available(self):
        for i in range(4):  # Bookings are available up to 3 days in advance.
            date = datetime.today() + timedelta(days=i)
            day_of_week = calendar.day_name[date.weekday()].upper()
            if day_of_week not in self._booking_days:
                continue

            hours = self._booking_days[day_of_week]
            try:
                driver.navigate_to_day(date)
                driver.book_slot(date, hours)
                booking_made = True
            except Exception as e:
                print(f"Unable to book {date.strftime('%m/%d/%Y')}: {e}")

driver = UcsdTennisBooker()
driver.sign_in()
driver.book_all_available()
