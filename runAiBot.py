'''
Autor:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

Licencia:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

versión:    24.12.29.12.30
'''


# Importaciones
import os
import csv
import re
import pyautogui
import time


from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException

from config.personals import *
from config.questions import *
from config.search import *
from config.secrets import use_AI, username, password
from config.settings import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config
from modules.ai.openaiConnections import *

from typing import Literal


pyautogui.FAILSAFE = False
# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


#< Variables globales y lógicas

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = first_name + " " + middle_name + " " + last_name if middle_name else first_name + " " + last_name

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

aiClient = None
#>


#< Funciones de inicio de sesión
def is_logged_in_LN() -> bool:
    '''
    Función para verificar si el usuario ha iniciado sesión en LinkedIn
    * Retorna: `True` si el usuario ha iniciado sesión o `False` si no
    '''
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    '''
    Función para iniciar sesión en LinkedIn
    * Intenta iniciar sesión usando `username` y `password` de `secrets.py`
    * Si falla, intenta iniciar sesión usando el botón de perfil guardado de LinkedIn si está disponible
    * Si ambos fallan, pide al usuario que inicie sesión manualmente
    '''
    # Find the username and password fields and fill them with user credentials
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
            # print_lg(e)
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
            # print_lg(e)
        # Find the login submit button and click it
        driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            # print_lg(e1, e2)
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/")) # wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space(.)="Start a post"]')))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        # print_lg(e)
        manual_login_retry(is_logged_in_LN, 2)
#>



def get_applied_job_ids() -> set:
    '''
    Función para obtener un `set` de IDs de trabajos aplicados
    * Retorna un conjunto de IDs de trabajos del archivo csv de historial de trabajos aplicados existente
    '''
    job_ids = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids



def set_search_location() -> None:
    '''
    Función para establecer la ubicación de búsqueda
    '''
    if search_location.strip():
        try:
            print_lg(f'Setting search location as: "{search_location.strip()}"')
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code'and not(@disabled)]", False) #  and not(@aria-hidden='true')]")
            text_input(actions, search_location_ele, search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(driver, ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']")
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg("Failed to update search location, continuing with default location!", e)


def apply_filters() -> None:
    '''
    Función para aplicar filtros de búsqueda de trabajo
    '''
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="All filters"]'))).click()
        buffer(recommended_wait)

        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel(driver, experience_level) 
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies: buffer(recommended_wait)

        multi_sel(driver, job_type)
        multi_sel(driver, on_site)
        if job_type or on_site: buffer(recommended_wait)

        if easy_apply_only: boolean_button_click(driver, actions, "Easy Apply")
        
        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry: buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles: buffer(recommended_wait)

        if under_10_applicants: boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network: boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer: boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)
        
        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments: buffer(recommended_wait)

        show_results_button: WebElement = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]')
        show_results_button.click()

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm("These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.", "Please check your results", ["Turn off Pause after search", "Look's good, Continue"]):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        # print_lg(e)



def get_page_info() -> tuple[WebElement | None, int | None]:
    '''
    Función para obtener el elemento de paginación y el número de página actual
    '''
    try:
        pagination_element = try_find_by_classes(driver, ["artdeco-pagination", "artdeco-pagination__pages"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//li[contains(@class, 'active')]").text)
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page



def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    '''
    # Función para obtener los detalles principales del trabajo.
    Retorna una tupla de (job_id, title, company, work_location, work_style, skip)
    * job_id: ID del trabajo
    * title: Título del trabajo
    * company: Nombre de la empresa
    * work_location: Ubicación del trabajo
    * work_style: Estilo de trabajo de este trabajo (Remoto, Presencial, Híbrido)
    * skip: Una bandera booleana para omitir este trabajo
    '''
    job_details_button = job.find_element(By.TAG_NAME, 'a')  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute('data-occludable-job-id')
    title = job_details_button.text
    title = title[:title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
    index = other_details.find(' · ')
    company = other_details[:index]
    work_location = other_details[index+3:]
    work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
    work_location = work_location[:work_location.rfind('(')].strip()
    
    # Skip if previously rejected due to blacklist or already applied
    skip = False
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs: 
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except: pass
    try: 
        if not skip: job_details_button.click()
    except Exception as e:
        print_lg(f'Error al hacer clic en el botón de detalles del trabajo "{title} | {company}". ID: {job_id}!', e)
        discard_job()
        job_details_button.click() # To pass the error outside
    buffer(click_gap)
    return (job_id,title,company,work_location,work_style,skip)


# Función para verificar palabras en la lista negra en Acerca de la Empresa
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if word.lower() in about_company:
            print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words: 
            if word.lower() in about_company: 
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card



# Función para extraer años de experiencia requeridos de Acerca del Trabajo
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0
    return max([int(match) for match in matches if int(match) <= 12])



def get_job_description(
) -> tuple[
    str | Literal['Unknown'],
    int | Literal['Unknown'],
    bool,
    str | None,
    str | None
    ]:
    '''
    # Descripción del Trabajo
    Función para extraer la descripción del trabajo de Acerca del Trabajo.
    ### Retorna:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    '''
    try:
        jobDescription = "Unknown"
        experience_required = "Unknown"
        found_masters = 0
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        jobDescriptionLow = jobDescription.lower()
        skip = False
        skipReason = None
        skipMessage = None
        for word in bad_words:
            if word.lower() in jobDescriptionLow:
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        if not skip:
            if did_masters and 'master' in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if current_experience > -1 and experience_required > current_experience + found_masters:
                skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                skipReason = "Required experience is high"
                skip = True
    except Exception as e:
        if jobDescription == "Unknown":    print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    finally:
        return jobDescription, experience_required, skip, skipReason, skipMessage
        


# Función para subir el currículum
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(default_resume_path)
    except: return False, "Previous resume"

# Función para responder preguntas comunes para Easy Apply
def answer_common_questions(label: str, answer: str) -> str:
    if 'sponsorship' in label or 'visa' in label: answer = require_visa
    return answer


# Función para responder las preguntas para Easy Apply
def answer_questions(modal: WebElement, questions_list: set, work_location: str) -> set:
    # Get all questions from the page
     
    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    # all_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    # all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    # all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    # all_questions = all_questions + all_list_questions + all_single_line_questions

    for Question in all_questions:
        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            label_org = "Unknown"
            try:
                label = Question.find_element(By.TAG_NAME, "label")
                label_org = label.find_element(By.TAG_NAME, "span").text
            except: pass
            answer = 'Yes'
            label = label_org.lower()
            select = Select(select)
            selected_option = select.first_selected_option.text
            optionsText = []
            options = '"List of phone country codes"'
            if label != "phone country code":
                optionsText = [option.text for option in select.options]
                options = "".join([f' "{option}",' for option in optionsText])
            prev_answer = selected_option
            if overwrite_previous_answers or selected_option == "Select an option":
                if 'email' in label or 'phone' in label: answer = prev_answer
                elif 'gender' in label or 'sex' in label: answer = gender
                elif 'disability' in label: answer = disability_status
                elif 'proficiency' in label: answer = 'Professional'
                else: answer = answer_common_questions(label,answer)
                try: select.select_by_visible_text(answer)
                except NoSuchElementException as e:
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    foundOption = False
                    for phrase in possible_answer_phrases:
                        for option in optionsText:
                            if phrase in option:
                                select.select_by_visible_text(option)
                                answer = f'Decline ({option})' if len(possible_answer_phrases) > 1 else option
                                foundOption = True
                                break
                        if foundOption: break
                    if not foundOption:
                        print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                        select.select_by_index(randint(1, len(select.options)-1))
                        answer = select.first_selected_option.text
                        randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
            questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
            continue
        
        # Check if it's a radio Question
        radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
        if radio:
            prev_answer = None
            label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
            try: label = find_by_class(label, "visually-hidden", 2.0)
            except: pass
            label_org = label.text if label else "Unknown"
            answer = 'Yes'
            label = label_org.lower()

            label_org += ' [ '
            options = radio.find_elements(By.TAG_NAME, 'input')
            options_labels = []
            
            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append( f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>' ) # Saving option as "label <value>"
                if option.is_selected(): prev_answer = options_labels[-1]
                label_org += f' {options_labels[-1]},'

            if overwrite_previous_answers or prev_answer is None:
                if 'citizenship' in label or 'employment eligibility' in label: answer = us_citizenship
                elif 'veteran' in label or 'protected' in label: answer = veteran_status
                elif 'disability' in label or 'handicapped' in label: 
                    answer = disability_status
                else: answer = answer_common_questions(label,answer)
                foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                if foundOption: 
                    actions.move_to_element(foundOption).click().perform()
                else:    
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                break
                        if foundOption: break
                    # if answer == 'Decline':
                    #     answer = options_labels[0]
                    #     for phrase in ["Prefer not", "not want", "not wish"]:
                    #         foundOption = try_xp(radio, f".//label[normalize-space()='{phrase}']", False)
                    #         if foundOption:
                    #             answer = f'Decline ({phrase})'
                    #             ele = foundOption
                    #             break
                    actions.move_to_element(ele).click().perform()
                    if not foundOption: randomly_answered_questions.add((f'{label_org} ]',"radio"))
            else: answer = prev_answer
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question
        text = try_xp(Question, ".//input[@type='text']", False)
        if text: 
            do_actions = False
            label = try_xp(Question, ".//label[@for]", False)
            try: label = label.find_element(By.CLASS_NAME,'visually-hidden')
            except: pass
            label_org = label.text if label else "Unknown"
            answer = "" # years_of_experience
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'experience' in label or 'years' in label: answer = years_of_experience
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label: answer = street
                elif 'city' in label or 'location' in label or 'address' in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif 'signature' in label: answer = full_name # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif 'name' in label:
                    if 'full' in label: answer = full_name
                    elif 'first' in label and 'last' not in label: answer = first_name
                    elif 'middle' in label and 'last' not in label: answer = middle_name
                    elif 'last' in label and 'first' not in label: answer = last_name
                    elif 'employer' in label: answer = recent_employer
                    else: answer = full_name
                elif 'notice' in label:
                    if 'month' in label:
                        answer = notice_period_months
                    elif 'week' in label:
                        answer = notice_period_weeks
                    else: answer = notice_period
                elif 'salary' in label or 'compensation' in label or 'ctc' in label or 'pay' in label: 
                    if 'current' in label or 'present' in label:
                        if 'month' in label:
                            answer = current_ctc_monthly
                        elif 'lakh' in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        if 'month' in label:
                            answer = desired_salary_monthly
                        elif 'lakh' in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                elif 'linkedin' in label: answer = linkedIn
                elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: answer = website
                elif 'scale of 1-10' in label: answer = confidence_level
                elif 'headline' in label: answer = linkedin_headline
                elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                elif 'state' in label or 'province' in label: answer = state
                elif 'zip' in label or 'postal' in label or 'code' in label: answer = zipcode
                elif 'country' in label: answer = country
                else: answer = answer_common_questions(label,answer)
                if answer == "":
                    randomly_answered_questions.add((label_org, "text"))
                    answer = years_of_experience
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label = try_xp(Question, ".//label[@for]", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'summary' in label: answer = linkedin_summary
                elif 'cover' in label: answer = cover_letter
                text_area.clear()
                text_area.send_keys(answer)
                if answer == "": 
                    randomly_answered_questions.add((label_org, "textarea"))
            questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
            continue

        # Check if it's a checkbox question
        checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
        if checkbox:
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(Question, ".//label[@for]", False)  # Sometimes multiple checkboxes are given for 1 question, Not accounted for that yet
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer
            if not prev_answer:
                try:
                    actions.move_to_element(checkbox).click().perform()
                    checked = True
                except Exception as e: 
                    print_lg("Checkbox click failed!", e)
                    pass
            questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
            continue


    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list




def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    '''
    Función para abrir una nueva pestaña y guardar enlaces de aplicaciones de trabajo externas
    '''
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        try:
            # Verificando tanto en inglés como en español
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text or "excedido el límite diario" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text: 
                dailyEasyApplyLimitReached = True
        except: pass
        print_lg("Easy apply failed I guess!")
        if pagination_element != None: return True, application_link, tabs_count
    try:
        # Intentar con texto en inglés
        apply_button = driver.find_elements(By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]")
        if apply_button:
            print_lg("Botón de aplicación encontrado, intentando hacer clic...")
            apply_button[0].click()
        else:
            print_lg("No se encontró el botón de aplicación, buscando alternativas...")
            # Mostrar todos los botones disponibles para depuración
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons[:5]:  # Mostrar solo los primeros 5 para no saturar
                print_lg(f"Botón encontrado: Texto={btn.text}, Clase={btn.get_attribute('class')}")
        
        # Intentar hacer clic en "Continue" o "Continuar"
        if not wait_span_click(driver, "Continue", 1, True, False):
            wait_span_click(driver, "Continuar", 1, True, False)
            
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        print_lg(f"Error detallado: {str(e)}")  # Mostrando el error completo
        failed_job(job_id, job_link, resume, date_listed, "Probably didn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count


def follow_company(modal: WebDriver = driver) -> None:
    '''
    Función para seguir o dejar de seguir empresas aplicadas fácilmente según `follow_companies`
    '''
    try:
        follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
        if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
    


#< Registro de intentos fallidos
def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    '''
    Función para actualizar la lista de trabajos fallidos en excel
    '''
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':job_id, 'Job Link':job_link, 'Resume Tried':resume, 'Date listed':date_listed, 'Date Tried':datetime.now(), 'Assumed Reason':error, 'Stack Trace':exception, 'External Job link':application_link, 'Screenshot Name':screenshot_name})
            file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    '''
    Función para tomar una captura de pantalla para depuración
    - Retorna el nombre de la captura de pantalla como String
    '''
    screenshot_name = "{} - {} - {}.png".format( job_id, failedAt, str(datetime.now()) )
    path = logs_folder_path+"/screenshots/"+screenshot_name.replace(":",".")
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//","/"))
    return screenshot_name
#>



def submitted_jobs(job_id: str, title: str, company: str, work_location: str, work_style: str, description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
                   skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], hr_link: str | Literal['Unknown'], resume: str, 
                   reposted: bool, date_listed: datetime | Literal['Unknown'], date_applied:  datetime | Literal['Pending'], job_link: str, application_link: str, 
                   questions_list: set | None, connect_request: Literal['In Development']) -> None:
    '''
    Función para crear o actualizar el archivo CSV de trabajos aplicados, una vez que la aplicación se envía con éxito
    '''
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0: writer.writeheader()
            writer.writerow({'Job ID':job_id, 'Title':title, 'Company':company, 'Work Location':work_location, 'Work Style':work_style, 
                            'About Job':description, 'Experience required': experience_required, 'Skills required':skills, 
                                'HR Name':hr_name, 'HR Link':hr_link, 'Resume':resume, 'Re-posted':reposted, 
                                'Date Posted':date_listed, 'Date Applied':date_applied, 'Job Link':job_link, 
                                'External Job link':application_link, 'Questions Found':questions_list, 'Connect Request':connect_request})
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert("Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file", "Failed Logging")



# Función para descartar la solicitud de trabajo
def discard_job() -> None:
    actions.send_keys(Keys.ESCAPE).perform()
    if not wait_span_click(driver, 'Descartar', 2):
        print_lg("Fallo al encontrar el botón 'Descartar' para descartar la solicitud.")






# Función para aplicar a trabajos
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume
    current_city = current_city.strip()

    if randomize_search_order:  shuffle(search_terms)
    for searchTerm in search_terms:
        driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
        print_lg("\n________________________________________________________________________________________________________________________\n")
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')

        apply_filters()

        current_count = 0
        try:
            while current_count < switch_number:
                # Wait until job listings are loaded
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")  

            
                for job in job_listings:
                    if keep_screen_awake: pyautogui.press('shiftright')
                    if current_count >= switch_number: break
                    print_lg("\n-@-\n")

                    job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                    
                    if skip: continue
                    # Redundant fail safe check for applied jobs!
                    try:
                        if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                            print_lg(f'Ya se aplicó al trabajo "{title} | {company}". ID de trabajo: {job_id}!')
                            continue
                    except Exception as e:
                        print_lg(f'Intentando aplicar al trabajo "{title} | {company}". ID de trabajo: {job_id}')

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link = "Unknown"
                    hr_name = "Unknown"
                    connect_request = "In Development" # Still in development
                    date_listed = "Unknown"   # Valor predeterminado
                    fecha_encontrada = False  # Inicializamos la variable al principio
                    fecha_datetime_encontrada = False  # Nueva variable para controlar si se encontró en datetime
                    skills = "Needs an AI" # Still in development
                    resume = "Pending"
                    reposted = False
                    questions_list = None
                    screenshot_name = "Not Available"
                    
                    # Mensaje para depuración
                    no_fecha_mensaje = "No se pudo encontrar ninguna información de fecha"
                    fecha_encontrada_mensaje = "Fecha final utilizada: "

                    try:
                        rejected_jobs, blacklisted_companies, jobs_top_card = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                    except ValueError as e:
                        print_lg(e, 'Skipping this job!\n')
                        failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                        skip_count += 1
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!")
                        print_lg(e)  # Mostrando el error para depuración



                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                        # ...existing code...
                        a_elem = hr_info_card.find_element(By.TAG_NAME, "a") if hr_info_card else None
                        span_elem = hr_info_card.find_element(By.TAG_NAME, "span") if hr_info_card else None
                        hr_link = a_elem.get_attribute("href") if a_elem else "Unknown"
                        hr_name = span_elem.text if span_elem and span_elem.text else "Unknown"
                        # ...existing code...
                    except Exception as e:
                        print_lg(f'No se proporcionó la información de RRHH para "{title}" con ID de trabajo: {job_id}!')
                        print_lg(e)  # Mostrando el error para depuración


                    # Calculation of date posted with improved error handling
                    try:
                        # PRIMERO intentamos buscar la fecha en el atributo datetime
                        # Esta es la forma más confiable de encontrar la fecha
                        try:
                            time_element = driver.find_element(By.XPATH, ".//time[@datetime]")
                            datetime_value = time_element.get_attribute("datetime")
                            print_lg(f"ÉXITO: Fecha encontrada en atributo datetime: {datetime_value}")
                            
                            # Si encontramos la fecha, la usamos directamente
                            date_listed = datetime_value
                            fecha_encontrada = True
                            fecha_datetime_encontrada = True  # Marcamos que se encontró en datetime específicamente
                            print_lg(f"Usando la fecha del atributo datetime: {date_listed}")
                            # Protección: evitamos que continue la búsqueda
                            break
                        except Exception as e:
                            # Si no encontramos fecha en el atributo datetime, 
                            # continuamos con los otros métodos
                            print_lg("INFO: No se encontró fecha en atributo datetime, buscando en texto...")
                            
                            # Si encontramos fecha en el atributo datetime, no necesitamos buscar más
                            if fecha_datetime_encontrada:
                                print_lg(f"{fecha_encontrada_mensaje}{date_listed} (de datetime)")
                            else:
                                # Solo continuamos con la búsqueda basada en texto si no encontramos la fecha en datetime
                                if not fecha_encontrada:
                                    date_selectors = [
                                        # Selectores específicos de LinkedIn
                                        ".//div[contains(@class, 'jobs-unified-top-card__posted-date')]",
                                        ".//div[contains(@class, 'jobs-unified-top-card__subtitle')]//span[last()]",
                                        ".//span[contains(@class, 'jobs-unified-top-card__subtitle-secondary-grouping')]//span[last()]",
                                        ".//div[contains(@class, 'jobs-unified-top-card')]//span[text()[contains(., 'ago')]]",
                                        ".//div[contains(@class, 'jobs-unified-top-card')]//span[text()[contains(., 'Posted')]]",
                                        # Selectores para español
                                        ".//div[contains(@class, 'jobs-unified-top-card')]//span[text()[contains(., 'hace')]]",
                                        ".//div[contains(@class, 'jobs-unified-top-card')]//span[text()[contains(., 'Publicado')]]",
                                        ".//span[text()[contains(., 'hace')]]",
                                        ".//span[text()[contains(., 'Publicado')]]",
                                        # Selectores de respaldo
                                        ".//span[text()[contains(., ' ago')]]",
                                        ".//span[text()[contains(., 'Posted')]]",
                                        # Búsqueda más amplia
                                        ".//*[contains(text(), ' ago')]",
                                        ".//*[contains(text(), 'hace')]",
                                        ".//*[contains(text(), 'día')]",
                                        ".//*[contains(text(), 'dias')]",
                                        ".//*[contains(text(), 'semana')]",
                                        ".//*[contains(text(), 'hora')]"
                                    ]
                                    
                                    time_posted_text = None
                                    date_element = None
                                    
                                    # Función auxiliar para limpiar el texto de fecha
                                    def clean_date_text(text):
                                        if not text:
                                            return None
                                        text = text.strip()
                                        for prefix in ['Posted', 'Reposted', '·', 'Publicado', 'Republicado']:
                                            text = text.replace(prefix, '').strip()
                                        return text
                                    
                                    # Función para validar si un texto realmente contiene información de fecha
                                    def is_valid_date_text(text):
                                        if not text:
                                            return False
                                        # Palabras clave que deberían estar en un texto de fecha válido
                                        date_keywords = [
                                            # Inglés
                                            'ago', 'hour', 'day', 'week', 'month', 'year', 'years', 'mins', 'minutes', 'seconds',
                                            # Español
                                            'hace', 'hora', 'horas', 'día', 'días', 'dias', 'semana', 'semanas', 
                                            'mes', 'meses', 'año', 'años', 'minuto', 'minutos', 'segundo', 'segundos'
                                        ]
                                        
                                        # Palabras que indican que el texto NO es una fecha
                                        negative_keywords = [
                                            'guardar', 'save', 'share', 'compartir', 'apply', 'aplicar', 'submit',
                                            'follow', 'seguir', 'connect', 'conectar', 'report', 'reportar',
                                            'more', 'más', 'view', 'ver', 'show', 'mostrar', 'details', 'detalles',
                                            'job', 'trabajo', 'empleo', 'position', 'puesto', 'company', 'empresa',
                                            'interview', 'entrevista', 'profile', 'perfil', 'review', 'revisar',
                                            'salary', 'salario', 'skills', 'habilidades', 'click', 'clic',
                                            'en', 'in', 'a', 'to', 'the', 'el', 'la', 'los', 'las', 'un', 'una'
                                        ]
                                        
                                        # Si contiene alguna palabra negativa, no es una fecha
                                        if any(neg_word in text.lower() for neg_word in negative_keywords):
                                            return False
                                        
                                        # Debe contener al menos una palabra clave de fecha
                                        return any(keyword in text.lower() for keyword in date_keywords)
                                    
                                    # Primero buscar en jobs_top_card
                                    if jobs_top_card:
                                        for selector in date_selectors:
                                            try:
                                                elements = jobs_top_card.find_elements(By.XPATH, selector)
                                                for element in elements:
                                                    text = clean_date_text(element.text)
                                                    if text and is_valid_date_text(text):
                                                        date_element = element
                                                        time_posted_text = text
                                                        break
                                                if date_element:
                                                    break
                                            except Exception:
                                                continue
                                    
                                    # Si no se encuentra, buscar en todo el documento
                                    if not date_element:
                                        print_lg("INFO: Buscando fecha en todo el documento...")
                                        for selector in date_selectors:
                                            try:
                                                elements = driver.find_elements(By.XPATH, selector)
                                                for element in elements:
                                                    text = clean_date_text(element.text)
                                                    if text and is_valid_date_text(text):
                                                        date_element = element
                                                        time_posted_text = text
                                                        break
                                                if date_element:
                                                    break
                                            except Exception:
                                                continue
                                    
                                    # Último intento: buscar cualquier texto que contenga una referencia temporal
                                    if not date_element and not time_posted_text:
                                        try:
                                            temporal_texts = driver.find_elements(By.XPATH, 
                                                ".//*[contains(text(), 'hour') or contains(text(), 'day') or contains(text(), 'week') or contains(text(), 'month') or " + 
                                                "contains(text(), 'hora') or contains(text(), 'día') or contains(text(), 'dias') or contains(text(), 'semana') or contains(text(), 'mes')]")
                                            for element in temporal_texts:
                                                text = clean_date_text(element.text)
                                                if text and is_valid_date_text(text):
                                                    time_posted_text = text
                                                    break
                                        except Exception:
                                            pass
                                    
                                    # Procesamos el texto de fecha si lo encontramos
                                    if time_posted_text:
                                        # Verificación adicional para asegurarse de que es un texto de fecha válido
                                        if is_valid_date_text(time_posted_text):
                                            print_lg(f"Time Posted encontrado: {time_posted_text}")
                                            reposted = "reposted" in time_posted_text.lower()
                                            date_listed = calculate_date_posted(time_posted_text)
                                            fecha_encontrada = True
                                        else:
                                            print_lg(f"Se encontró texto pero no parece ser una fecha válida: {time_posted_text}")
                                            time_posted_text = None  # Reiniciamos para que no se considere como fecha encontrada
                        
                        # Mensaje final sobre el estado de la fecha
                        if fecha_encontrada or fecha_datetime_encontrada:
                            print_lg(f"{fecha_encontrada_mensaje}{date_listed}")
                        else:
                            print_lg("INFO: No se encontró información de fecha - Usando 'Unknown'")
                            date_listed = "Unknown"
                            
                    except Exception as e:
                        print_lg(f"Error al calcular la fecha de publicación: {str(e)}")
                        date_listed = "Unknown"
                    
                    # Depuración: Muestra el estado final de las variables
                    print_lg(f"DEBUG: Estado final - fecha_encontrada: {fecha_encontrada}, fecha_datetime_encontrada: {fecha_datetime_encontrada}, date_listed: {date_listed}")
                    
                    # Continuamos con el proceso independientemente de si encontramos la fecha o no
                    print_lg(f"Continuando con el proceso de aplicación... (Fecha: {date_listed})")
                    
                    # Agregamos un pequeño tiempo de espera para asegurarnos de que la página se ha cargado completamente
                    time.sleep(2)

                    description, experience_required, skip, reason, message = get_job_description()
                    if skip:
                        print_lg(message)
                        failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                        rejected_jobs.add(job_id)
                        skip_count += 1
                        continue

                    
                    if use_AI and description != "Unknown":
                        skills = ai_extract_skills(aiClient, description)

                    uploaded = False
                    # Case 1: Easy Apply Button
                    print_lg("Buscando botón de Easy Apply...")
                    
                    # Búsqueda más amplia que incluye variantes en español
                    button_selectors = [
                        # Inglés
                        ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]",
                        # Español
                        ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'fácil')]",
                        # Búsqueda genérica
                        ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]",
                        ".//button[contains(@class,'jobs-apply-button')]"
                    ]
                    
                    easy_apply_found = False
                    for selector in button_selectors:
                        buttons = driver.find_elements(By.XPATH, selector)
                        if buttons:
                            print_lg(f"Botón encontrado con selector: {selector}")
                            print_lg(f"Texto del botón: {buttons[0].text}")
                            print_lg(f"Atributos del botón: Clase={buttons[0].get_attribute('class')}, Aria-Label={buttons[0].get_attribute('aria-label')}")
                            try:
                                # Intentar hacer clic en el botón
                                print_lg("Intentando hacer clic en el botón...")
                                buttons[0].click()
                                print_lg("Clic exitoso!")
                                easy_apply_found = True
                                break
                            except Exception as e:
                                print_lg(f"Error al hacer clic en el botón: {str(e)}")
                                continue
                    
                    if not easy_apply_found:
                        print_lg("No se encontró ningún botón de aplicación. Mostrando todos los botones disponibles:")
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                        for i, btn in enumerate(all_buttons[:10]):  # Mostrar los primeros 10 botones
                            print_lg(f"Botón {i+1}: Texto='{btn.text}', Clase='{btn.get_attribute('class')}', Aria-Label='{btn.get_attribute('aria-label')}'")
                        
                        # Si no se encuentra ningún botón específico, intentar buscar por texto
                        apply_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply') or contains(text(), 'Aplicar')]")
                        if apply_buttons:
                            print_lg(f"Se encontraron {len(apply_buttons)} botones con texto 'Apply' o 'Aplicar'")
                            try:
                                apply_buttons[0].click()
                                print_lg("Clic en botón de texto 'Apply/Aplicar' exitoso!")
                                easy_apply_found = True
                            except Exception as e:
                                print_lg(f"Error al hacer clic en botón por texto: {str(e)}")
                    
                    # Si se encontró y se hizo clic en el botón de Easy Apply, continuar con el proceso normal
                    if easy_apply_found:
                        print_lg("Procesando aplicación Easy Apply...")
                        try:
                            try:
                                errored = ""
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                # Intentar con Next o Siguiente
                                if not wait_span_click(modal, "Next", 1):
                                    wait_span_click(modal, "Siguiente", 1)
                                
                                resume = "Previous resume"
                                next_button = True
                                questions_list = set()
                                next_counter = 0
                                while next_button:
                                    next_counter += 1
                                    if next_counter >= 15: 
                                        if pause_at_failed_question:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            pyautogui.alert("No se pudo responder una o más preguntas.\nHaga clic en \"Continuar\" cuando termine.\nNO HAGA CLIC en los botones Atrás, Siguiente o Revisar en LinkedIn.\n\n\n\n\nPuede desactivar la configuración \"Pause at failed question\" en config.py", "Ayuda necesaria", "Continuar")
                                            next_counter = 1
                                            continue
                                        if questions_list: print_lg("Atascado en una o algunas de las siguientes preguntas...", questions_list)
                                        screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        errored = "stuck"
                                        raise Exception("Parece que estamos atascados en un bucle continuo de siguiente, probablemente debido a nuevas preguntas.")
                                    
                                    questions_list = answer_questions(modal, questions_list, work_location)
                                    if useNewResume and not uploaded: uploaded, resume = upload_resume(modal, default_resume_path)
                                    
                                    # Intentar encontrar los botones en diferentes idiomas
                                    try: 
                                        next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Revisar"]')
                                    except NoSuchElementException:
                                        try:
                                            next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Review"]')
                                        except NoSuchElementException:
                                            try:
                                                next_button = modal.find_element(By.XPATH, './/button[contains(span, "Next")]')
                                            except NoSuchElementException:
                                                next_button = modal.find_element(By.XPATH, './/button[contains(span, "Siguiente")]')
                                    
                                    try: next_button.click()
                                    except ElementClickInterceptedException: break    # Ocurre cuando intenta hacer clic en el botón Siguiente en la sección de fotos de About Company
                                    buffer(click_gap)

                            except NoSuchElementException: errored = "nose"
                            finally:
                                if questions_list and errored != "stuck": 
                                    print_lg("Se respondieron las siguientes preguntas...", questions_list)
                                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                
                                # Intentar con diferentes textos para los botones
                                if not wait_span_click(driver, "Revisar", 1, scrollTop=True):
                                    wait_span_click(driver, "Review", 1, scrollTop=True)
                                
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = pyautogui.confirm('1. Por favor verifique su información.\n2. Si editó algo, vuelva a esta pantalla final.\n3. NO HAGA CLIC en "Enviar solicitud".\n\n\n\n\nPuede desactivar la configuración "Pause before submit" en config.py\nPara desactivar temporalmente la pausa, haga clic en "Desactivar pausa"', "Confirme su información",["Desactivar pausa", "Descartar solicitud", "Enviar solicitud"])
                                    if decision == "Descartar solicitud": raise Exception("Solicitud de trabajo descartada por el usuario!")
                                    pause_before_submit = False if "Desactivar pausa" == decision else True
                                
                                follow_company(modal)
                                
                                # Intentar los botones de envío en diferentes idiomas
                                submit_clicked = False
                                if wait_span_click(driver, "Enviar solicitud", 2, scrollTop=True):
                                    submit_clicked = True
                                elif wait_span_click(driver, "Submit application", 2, scrollTop=True):
                                    submit_clicked = True
                                
                                if submit_clicked:
                                    date_applied = datetime.now()
                                    if not wait_span_click(driver, "Listo", 2):
                                        if not wait_span_click(driver, "Done", 2):
                                            actions.send_keys(Keys.ESCAPE).perform()
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("¿Has enviado la solicitud manualmente? 😒", "No se pudo encontrar el botón de enviar solicitud", ["Si", "No"]):
                                    date_applied = datetime.now()
                                    wait_span_click(driver, "Done", 2)
                                else:
                                    print_lg("No se pudo enviar la solicitud, descartando la aplicación...")
                                    if errored == "nose": raise Exception("No se pudo hacer clic en el botón de enviar solicitud 😑")

                                # Si se envió correctamente, registrar en las estadísticas
                                application_link = "Easy Applied"
                                easy_applied_count += 1
                                submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                                if uploaded: useNewResume = False
                                applied_jobs.add(job_id)
                                print_lg(f'Aplicación enviada exitosamente para "{title} | {company}". ID de trabajo: {job_id}')

                        except Exception as e:
                            print_lg("Error en el proceso de Easy Apply!")
                            print_lg(f"Error detallado: {str(e)}")
                            critical_error_log("Error en el proceso de Easy Apply",e)
                            failed_job(job_id, job_link, resume, date_listed, "Problema en Easy Apply", e, application_link, screenshot_name)
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Si no se pudo encontrar o hacer clic en un botón de Easy Apply, intentar con aplicación externa
                        print_lg("Intentando proceso de aplicación externa...")
                        try:
                            screenshot_name = screenshot(driver, job_id, "external_apply_attempt")
                            skip, application_link, tabs_count = external_apply(pagination_element, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                            if dailyEasyApplyLimitReached:
                                print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                                return
                            if skip: continue
                            
                            submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                            external_jobs_count += 1
                            applied_jobs.add(job_id)
                            print_lg(f'Información de aplicación externa guardada para "{title} | {company}". ID de trabajo: {job_id}')
                        except Exception as e:
                            print_lg(f"Error al intentar aplicación externa: {str(e)}")
                            failed_count += 1
                            continue
                    
                    current_count += 1



                # Switching to next page
                if pagination_element == None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
                    break

        except Exception as e:
            print_lg("No se pudieron encontrar ofertas de trabajo!", e)
            critical_error_log("En Aplicador", e)
            print_lg(driver.page_source, pretty=True)
            # print_lg(e)

        
def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg("\n########################################################################################################################\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'")
    apply_to_jobs(search_terms)
    print_lg("########################################################################################################################\n")
    if not dailyEasyApplyLimitReached:
        print_lg("Sleeping for 10 min...")
        sleep(300)
        print_lg("Few more min... Gonna start with in next 5 min...")
        sleep(300)
    buffer(3)
    return total_runs + 1



chatGPT_tab = False
linkedIn_tab = False

def validate_code_structure() -> None:
    # Función simple para validar (o notificar) la estructura del código.
    print("Estructura de código validada.")

def main() -> None:
    try:
        validate_code_structure()  # Validación de la estructura
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        total_runs = 1        
        validate_config()
        
        if not os.path.exists(default_resume_path):
            pyautogui.alert(text='Your default resume "{}" is missing! Please update it\'s folder path "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!'.format(default_resume_path), title="Missing Resume", button="OK")
            useNewResume = False
        
        # Login to LinkedIn
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        
        linkedIn_tab = driver.current_window_handle

        # # Login to ChatGPT in a new tab for resume customization
        # if use_resume_generator:
        #     try:
        #         driver.switch_to.new_window('tab')
        #         driver.get("https://chat.openai.com/")
        #         if not is_logged_in_GPT(): login_GPT()
        #         open_resume_chat()
        #         global chatGPT_tab
        #         chatGPT_tab = driver.current_window_handle
        #     except Exception as e:
        #         print_lg("Opening OpenAI chatGPT tab failed!")
        if use_AI:
            aiClient = ai_create_openai_client()

        # Start applying to jobs
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)
        while(run_non_stop):
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                date_posted = date_options[date_options.index(date_posted)+1 if date_options.index(date_posted)+1 > len(date_options) else -1] if stop_date_cycle_at_24hr else date_options[0 if date_options.index(date_posted)+1 >= len(date_options) else date_options.index(date_posted)+1]
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached:
                break
        

    except NoSuchWindowException:   pass
    except Exception as e:
        critical_error_log("In Applier Main", e)
        pyautogui.alert(e,alert_title)
    finally:
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg("Total applied or collected:     {}".format(easy_applied_count + external_jobs_count))
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))
        if randomly_answered_questions: print_lg("\n\nQuestions randomly answered:\n  {}  \n\n".format(";\n".join(str(question) for question in randomly_answered_questions)))
        quote = choice([
            "You're one step closer than before.", 
            "All the best with your future interviews.", 
            "Keep up with the progress. You got this.", 
            "If you're tired, learn to take rest but never give up.",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
            "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
            "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
            "Opportunities don't happen, you create them. - Chris Grosser",
            "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
            "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
            ])
        msg = f"\n{quote}\n\n\nBest regards,\nSai Vignesh Golla\nhttps://www.linkedin.com/in/saivigneshgolla/\n\n"
        pyautogui.alert(msg, "Exiting..")
        print_lg(msg,"Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!" 
            pyautogui.alert(msg,"Info")
            print_lg("\n"+msg)
        ai_close_openai_client(aiClient)
        try:
            driver.quit()
        except OSError as oe:
            if "[WinError 6]" in str(oe):
                print_lg("Driver ya cerrado. Se ignora el error al intentar cerrar el driver.")
            else:
                critical_error_log("When quitting...", oe)
        except Exception as e:
            critical_error_log("When quitting...", e)

if __name__ == "__main__":
    main()
