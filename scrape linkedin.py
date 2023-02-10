from selenium import webdriver
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

searchword = "analista de dados Brazil"

url = "https://www.linkedin.com/jobs/search/?currentJobId=3470736305&geoId=106057199&keywords=analista%20de%20dados&location=Brazil&refresh=true"

wd = webdriver.Chrome(executable_path = "C:/Users/VNFSK/Downloads/chromedriver_win32 (1)/chromedriver.exe")
wd.get(url)
wd.maximize_window()


no_of_jobs = wd.find_element(By.CSS_SELECTOR, "h1>span").text
no_of_jobs = int("".join(i for i in no_of_jobs.split("+")[0] if i.isdigit()))


i = 2
##pages = no_of_jobs/25
pages = 50

while i <= int(pages)+1:
    time.sleep(2)
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    i = i + 1
    try:
        if (EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/main/section/button"))):
            wd.find_element("xpath", "/html/body/div/div/main/section/button").click()
    except:
        print("no")
        pass


job_lists = wd.find_element(By.CLASS_NAME, "jobs-search__results-list")
jobs = job_lists.find_elements(By.TAG_NAME, "li") # return a list

len(jobs)




job_id = []
job_title = []
company_name = []
location = []
date = []
job_link = []
jd = []
seniority = []
emp_type = []
job_func = []
industries = []

for job in jobs:
    job_id0 = job.find_element(By.CSS_SELECTOR, "div").get_attribute("data-tracking-id")
    job_id.append(job_id0)

    job_title0 = job.find_element(By.CSS_SELECTOR, "h3").text
    job_title.append(job_title0)

    company_name0 = job.find_element(By.CSS_SELECTOR, "h4").text
    company_name.append(company_name0)

    location0 = job.find_element(By.CLASS_NAME, "job-search-card__location").text
    location.append(location0)

    date0 = job.find_element(By.CSS_SELECTOR, "div>div>time").get_attribute("datetime")
    date.append(date0)

    job_link0 = job.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
    job_link.append(job_link0)

    

for jobnum in range(len(jobs)):
##    time.sleep(3)

    try:
        WebDriverWait(wd, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#main-content > section.two-pane-serp-page__results-list > ul > li:nth-child(" + str(jobnum + 1) + ") > div > a")) or
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#main-content > section.two-pane-serp-page__results-list > ul > li:nth-child(" + str(jobnum + 1) + ") > a"))
        )
    except:
       print("TIMEOUT")
    

    try:
        job_click_css = "#main-content > section.two-pane-serp-page__results-list > ul > li:nth-child(" + str(jobnum + 1) + ") > div > a"
        wd.find_element(By.CSS_SELECTOR, job_click_css).click()
    except:
        job_click_css = "#main-content > section.two-pane-serp-page__results-list > ul > li:nth-child(" + str(jobnum + 1) + ") > a"
        wd.find_element(By.CSS_SELECTOR, job_click_css).click()
    


    time.sleep(3)
    
    try:
        show_more_path = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/div/section/button[1]"
        wd.find_element(By.XPATH, show_more_path).click()
    except:
        print("no2")
        pass
        

    try:
        jd0 = wd.find_element(By.CLASS_NAME, "show-more-less-html__markup").text
        jd.append(jd0)
    except:
        jd0 = ""
        jd.append(jd0)
        
    try:
        seniority_path = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/ul/li[1]/span"
        seniority0 = wd.find_element(By.XPATH, seniority_path).text
        seniority.append(seniority0)
    except:
        seniority0 = ""
        seniority.append(seniority0)

    try:
        emp_type_path = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/ul/li[2]/span"
        emp_type0 = wd.find_element(By.XPATH, emp_type_path).text
        emp_type.append(emp_type0)
    except:
        emp_type0 = ""
        emp_type.append(emp_type0)

    try:
        job_func_path = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/ul/li[3]/span"
        job_func0 = wd.find_element(By.XPATH, job_func_path).text
        job_func.append(job_func0)
    except:
        job_func0 = ""
        job_func.append(job_func0)

    try:       
        industries_path = "/html/body/div[1]/div/section/div[2]/div/section[1]/div/ul/li[4]/span"
        industries0 = wd.find_element(By.XPATH, industries_path).text
        industries.append(industries0)
    except:
        industries0 = ""
        industries.append(industries0)



job_data = pd.DataFrame({"ID": job_id,
"date": date,
"company": company_name,
"title": job_title,
"location": location,
"description": jd,
"level": seniority,
"type": emp_type,
"function": job_func,
"industry": industries,
"link": job_link
})

job_data.to_csv("LinkedIn Job Data - "  + str(no_of_jobs) + " results searching " + searchword + ".csv", index = False)

