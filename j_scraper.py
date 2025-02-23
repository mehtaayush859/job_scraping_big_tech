import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tabulate import tabulate


class BaseJobScraper:
    """
    Base class for job scrapers.
    """

    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = self.init_selenium()

    def init_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        return webdriver.Chrome(service=Service(self.driver_path), options=chrome_options)

    def quit_driver(self):
        self.driver.quit()


class GoogleJobScraper(BaseJobScraper):
    """
    Scraper for Google Careers.
    """

    def scrape_jobs(self):
        url = "https://careers.google.com/jobs/results/?sort_date"
        self.driver.get(url)
        self.driver.implicitly_wait(10)
        jobs = []

        try:
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.sMn82b")
            for card in job_cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "h3").text.strip()
                    location = card.find_element(By.CSS_SELECTOR, "span.r0wTof").text.strip()
                    link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

                    jobs.append({"Title": title, "Location": location, "Link": link})
                except Exception as e:
                    print(f"Error scraping Google job card: {e}")
        except Exception as e:
            print(f"Error scraping Google Careers: {e}")
        finally:
            self.quit_driver()

        return jobs


class AmazonJobScraper(BaseJobScraper):
    """
    Scraper for Amazon Careers.
    """

    def scrape_jobs(self):
        url = "https://www.amazon.jobs/en/search?base_query=software"
        self.driver.get(url)
        self.driver.implicitly_wait(10)
        jobs = []
        now = datetime.now()

        try:
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job-tile")
            for card in job_cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "h3").text.strip()
                    location = card.find_element(By.CSS_SELECTOR, "li").text.strip()
                    link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    date_posted = card.find_element(By.CSS_SELECTOR, "div.info.col-12.col-md-4 h2.posting-date").text

                    posted_date_str = date_posted.replace("Posted", "").strip()
                    posted_date = datetime.strptime(posted_date_str, "%B %d, %Y")  # Example: "January 18, 2025"
                    # if now - posted_date <= timedelta(days=1):
                    jobs.append({"Title": title, "Location": location, "Link": link, "Date Posted": posted_date})
                except Exception as e:
                    print(f"Error scraping Amazon job card: {e}")
        except Exception as e:
            print(f"Error scraping Amazon Jobs: {e}")
        finally:
            self.quit_driver()

        return jobs


class JobScraperManager:
    """
    Manages the scraping, filtering, and reporting of job postings.
    """

    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.jobs = []

    @staticmethod
    def filter_jobs(jobs, keywords, location_keywords):
        """
        Filter jobs by title keywords and location keywords.
        """
        filtered_jobs = []
        for job in jobs:
            if any(keyword.lower() in job["Title"].lower() for keyword in keywords) and \
                    any(location.lower() in job["Location"].lower() for location in location_keywords):
                filtered_jobs.append(job)
        return filtered_jobs

    @staticmethod
    def save_to_csv(jobs, filename_prefix="jobs"):
        """
        Save job postings to a CSV file.
        """
        # Get current date and format it
        current_date = datetime.now().strftime("%d_%m_%Y")  # e.g., "20_01_2025"

        # Generate filename with date
        filename = f"{filename_prefix}_{current_date}.csv"

        df = pd.DataFrame(jobs)
        df.to_csv(filename, index=False)
        return filename

    @staticmethod
    def send_email(filename):
        """
        Send email notifications with job details.
        """
        sender_email = "mehtaayush144@gmail.com"
        receiver_email = "mehtaayush251@gmail.com"
        password = "Bill@gates4644"

        subject = "Daily Job Scraper Results"
        body = f"Please find the attached file with the latest job postings."

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))
        with open(filename, "rb") as attachment:
            message.attach(MIMEText(attachment.read(), "base64", "utf-8"))
            message.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(filename)}",
            )
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                print(f"Email sent to {receiver_email}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"Authentication error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            server.quit()

    def run_scraper(self):
        """
        Run the scrapers for Google and Amazon, filter jobs, and save results.
        """
        print("Starting job scraping...")

        # Scrape Google and Amazon jobs
        google_scraper = GoogleJobScraper(self.driver_path)
        amazon_scraper = AmazonJobScraper(self.driver_path)

        google_jobs = google_scraper.scrape_jobs()
        amazon_jobs = amazon_scraper.scrape_jobs()

        # Combine and filter jobs
        keywords = ["Software", "Engineer", "Developer", "Intern"]
        location_keywords = ["united states", "usa", "us"]
        all_jobs = google_jobs + amazon_jobs
        filtered_jobs = self.filter_jobs(all_jobs, keywords, location_keywords)

        if filtered_jobs:
            filename = self.save_to_csv(filtered_jobs)
            print(tabulate(filtered_jobs, headers="keys", tablefmt="fancy_grid"))
            # self.send_email(filename)
        else:
            print("No matching jobs found.")

    @staticmethod
    def schedule_scraper(self):
        schedule.every().day.at("09:00").do(self.run_scraper)
        print("Job scraper scheduled to run daily at 09:00.")

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    DRIVER_PATH = "D:\Grad_Docs and Courses\J_Scraper\chromedriver-win32\chromedriver-win32\chromedriver.exe"
    scraper_manager = JobScraperManager(DRIVER_PATH)
    scraper_manager.run_scraper()
    # scraper_manager.schedule_scraper()


