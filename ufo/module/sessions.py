# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import os
import time
import traceback

from art import text2art
from pywinauto.uia_defines import NoPatternInterfaceError
from ..automator.ui_control.screenshot import PhotographerFacade

from .. import utils
from ..agent.agent import AgentFactory
from ..agent.basic import MemoryItem
from ..automator.ui_control import utils as control
from ..config.config import Config
from ..experience.summarizer import ExperienceSummarizer
from . import processor



configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]



class Session(object):
    """
    A session for UFO.
    """
    def __init__(self, task):
        """
        Initialize a session.
        :param task: The name of current task.
        :param gpt_key: GPT key.
        """
        self.task = task
        self._step = 0
        self._round = 0

        self.log_path = f"logs/{self.task}/"
        utils.create_folder(self.log_path)
        self.logger = self.initialize_logger(self.log_path, "response.log")
        self.request_logger = self.initialize_logger(self.log_path, "request.log")

        self.HostAgent = AgentFactory.create_agent("host", "HostAgent", configs["HOST_AGENT"]["VISUAL_MODE"], configs["HOSTAGENT_PROMPT"], configs["HOSTAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"])
    
        self.AppAgent = None

        self.photographer = PhotographerFacade()

        self._status = "APP_SELECTION"
        self.application = ""
        self.app_root = ""
        self.app_window = None
        self.plan = ""

        self._cost = 0.0
        self.control_reannotate = None

        welcome_text = """
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
{art}
Please enter your request to be completed🛸: """.format(art=text2art("UFO"))

        utils.print_with_color(welcome_text, "cyan")
        
        self.request = input()


    def process_application_selection(self) -> None:

        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """

        host_agent_processor = processor.HostAgentProcessor(log_path=self.log_path, photographer=self.photographer, plan=self.plan, request=self.request, 
                                                            request_logger=self.request_logger, logger=self.logger, host_agent=self.HostAgent)
        
        process_status, process_step, process_cost = host_agent_processor.process()
        self._status = process_status
        self._step += process_step
        self._cost += process_cost

        self.AppAgent = self.HostAgent.get_active_appagent()
        self.app_window = host_agent_processor.get_active_window()


    def process_action_selection(self) -> None:
        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """

        utils.print_with_color("Step {step}: Taking an action on application {application}.".format(step=self._step, application=self.application), "magenta")
        control_screenshot_save_path = self.log_path + f"action_step{self._step}_selected_controls.png"


        if self.app_window == None:
            self._status = "ERROR"
            utils.print_with_color("Required Application window is not available.", "red")
            return

        image_url, annotation_dict, control_info = self.screenshots_and_control_info_helper()
        

        if configs["RAG_EXPERIENCE"]:
            experience_examples, experience_tips = self.AppAgent.rag_experience_retrieve(self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"])
        else:
            experience_examples = []
            experience_tips = []
            
        if configs["RAG_DEMONSTRATION"]:
            demonstration_examples, demonstration_tips = self.AppAgent.rag_demonstration_retrieve(self.request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"])
        else:
            demonstration_examples = []
            demonstration_tips = []
        
        examples = experience_examples + demonstration_examples
        tips = experience_tips + demonstration_tips

        external_knowledge_prompt = self.AppAgent.external_knowledge_prompt_helper(self.request, configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"], configs["RAG_ONLINE_RETRIEVED_TOPK"])


        action_history = self.HostAgent.get_global_action_memory().to_json()
        request_history = self.HostAgent.get_request_history_memory().to_json()

        appagent_prompt_message = self.AppAgent.message_constructor(examples, tips, external_knowledge_prompt, image_url, request_history, action_history, 
                                                                            control_info, self.plan, self.request, configs["INCLUDE_LAST_SCREENSHOT"])
        
        self.request_logger.debug(json.dumps({"step": self._step, "prompt": appagent_prompt_message, "status": ""}))

        try:
            response_string, cost = self.AppAgent.get_response(appagent_prompt_message, "APPAGENT", use_backup_engine=True)
        except Exception as e:
            error_trace = traceback.format_exc()
            log = json.dumps({"step": self._step, "status": str(error_trace), "prompt": appagent_prompt_message})
            utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(error_trace)), "red")
            self.request_logger.info(log)
            self._status = "ERROR"
            time.sleep(configs["SLEEP_TIME"])
            return 
            
        self.update_cost(cost=cost)

        try:
            response_json = self.AppAgent.response_to_dict(response_string)

            control_label = response_json["ControlLabel"]
            control_text = response_json["ControlText"]
            operation = response_json["Function"]
            args = utils.revise_line_breaks(response_json["Args"])

            control_selected = annotation_dict.get(control_label, "")

            self.AppAgent.print_response(response_json)

            # Build the executor for over the control item.
            # ui_controller = self.AppAgent.Puppeteer.create_ui_controller(control_selected)

            self.AppAgent.Puppeteer.create_ui_control_receiver(control_selected, self.app_window)
        

            # Take screenshot of the selected control


            self.photographer.capture_app_window_screenshot_with_rectangle(self.app_window, sub_control_list=[control_selected], save_path=control_screenshot_save_path)


            # Set the result and log the result.
            self.plan = response_json["Plan"]
            self._status = response_json["Status"]


            # Compose the function call and the arguments string.
            action = self.AppAgent.Puppeteer.get_command_string(operation, args)

            if self.safe_guard(action, control_text):
                # Execute the action
                # results = ui_controller.execution(operation, args)
                results = self.AppAgent.Puppeteer.execute_command(operation, args)
                if not utils.is_json_serializable(results):
                    results = ""
            else:
                results = "The user decide to stop the task."

            # Create a memory item for the app agent
            app_agent_step_memory = MemoryItem()
            
            additional_memory = {"Step": self._step, "AgentStep": self.AppAgent.get_step(), "Round": self._round, "Action": action, 
                                 "Request": self.request, "Agent": "ActAgent", "AgentName": self.AppAgent.name, "Application": self.app_root, "Cost": cost, "Results": results}
            app_agent_step_memory.set_values_from_dict(response_json)
            app_agent_step_memory.set_values_from_dict(additional_memory)

            self.AppAgent.add_memory(app_agent_step_memory)

            response_json = self.set_result_and_log(app_agent_step_memory.to_dict())


        except Exception as e:
            # Return the error message and log the error.
            utils.print_with_color("Error occurs at step {step}".format(step=self._step), "red")
            utils.print_with_color(str(e), "red")
            self._status = "ERROR"

            self.error_logger(response_string, str(e))
            return
        
        self._step += 1
        self.AppAgent.update_step()
        self.AppAgent.update_status(self._status)

        # Handle the case when the control item is overlapped and the agent is unable to select the control item. Retake the annotated screenshot.
        if "SCREENSHOT" in self._status.upper():
            utils.print_with_color("Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.", "magenta")
            # self.control_reannotate = ui_controller.annotation(args, annotation_dict)
            self.control_reannotate = self.AppAgent.Puppeteer.execute_command("annotation", args, annotation_dict)
            return

        self.control_reannotate = None
            
        time.sleep(configs["SLEEP_TIME"])

        return
    


    def _app_agent_load_retrievers(self):
        """
        Load the retrievers for APP_AGENT.
        """

        if configs["RAG_OFFLINE_DOCS"]:
            utils.print_with_color("Loading offline document indexer for {app}...".format(app=self.application), "magenta")
            self.AppAgent.build_offline_docs_retriever()
        if configs["RAG_ONLINE_SEARCH"]:
            utils.print_with_color("Creating a Bing search indexer...", "magenta")
            self.AppAgent.build_online_search_retriever(self.request, configs["RAG_ONLINE_SEARCH_TOPK"])
        if configs["RAG_EXPERIENCE"]:
            utils.print_with_color("Creating an experience indexer...", "magenta")
            experience_path = configs["EXPERIENCE_SAVED_PATH"]
            db_path = os.path.join(experience_path, "experience_db")
            self.AppAgent.build_experience_retriever(db_path)
        if configs["RAG_DEMONSTRATION"]:
            utils.print_with_color("Creating an demonstration indexer...", "magenta")
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            db_path = os.path.join(demonstration_path, "demonstration_db")
            self.AppAgent.build_human_demonstration_retriever(db_path)

    
    def screenshots_and_control_info_helper(self) -> tuple:
        """
        Helper function for taking screenshots.
        return: The image url, the annotation dict, and the control info.
        """

        screenshot_save_path = self.log_path + f"action_step{self._step}.png"
        annotated_screenshot_save_path = self.log_path + f"action_step{self._step}_annotated.png"
        concat_screenshot_save_path = self.log_path + f"action_step{self._step}_concat.png"

        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            control_list = control.find_control_elements_in_descendants(BACKEND, self.app_window, control_type_list = configs["CONTROL_LIST"], class_name_list = configs["CONTROL_LIST"])

        annotation_dict = self.photographer.get_annotation_dict(self.app_window, control_list, annotation_type="number")

        self.photographer.capture_app_window_screenshot(self.app_window, save_path=screenshot_save_path)
        self.photographer.capture_app_window_screenshot_with_annotation(self.app_window, control_list, annotation_type="number", save_path=annotated_screenshot_save_path)

        control_info = control.get_control_info_dict(annotation_dict, ["control_text", "control_type" if BACKEND == "uia" else "control_class"])
        
        image_url = []

        if configs["INCLUDE_LAST_SCREENSHOT"]:
            
            last_screenshot_save_path = self.log_path + f"action_step{self._step - 1}.png"
            last_control_screenshot_save_path = self.log_path + f"action_step{self._step - 1}_selected_controls.png"
            image_url += [utils.encode_image_from_path(last_control_screenshot_save_path if os.path.exists(last_control_screenshot_save_path) else last_screenshot_save_path)]

        if configs["CONCAT_SCREENSHOT"]:
            self.photographer.concat_screenshots(screenshot_save_path, annotated_screenshot_save_path, concat_screenshot_save_path)
            image_url += [utils.encode_image_from_path(concat_screenshot_save_path)]
        else:
            screenshot_url = utils.encode_image_from_path(screenshot_save_path)
            screenshot_annotated_url = utils.encode_image_from_path(annotated_screenshot_save_path)
            image_url += [screenshot_url, screenshot_annotated_url]

        return image_url, annotation_dict, control_info

    

    def experience_asker(self) -> bool:
        utils.print_with_color("""Would you like to save the current conversation flow for future reference by the agent?
[Y] for yes, any other key for no.""", "magenta")
        
        ans = input()

        if ans.upper() == "Y":
            return True
        else:
            return False
        

    def experience_saver(self) -> None:
        """
        Save the current agent experience.
        """
        utils.print_with_color("Summarizing and saving the execution flow as experience...", "yellow")

        summarizer = ExperienceSummarizer(configs["APP_AGENT"]["VISUAL_MODE"], configs["EXPERIENCE_PROMPT"], configs["APPAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"])
        experience = summarizer.read_logs(self.log_path)
        summaries, total_cost = summarizer.get_summary_list(experience)

        experience_path = configs["EXPERIENCE_SAVED_PATH"]
        utils.create_folder(experience_path)
        summarizer.create_or_update_yaml(summaries, os.path.join(experience_path, "experience.yaml"))
        summarizer.create_or_update_vector_db(summaries, os.path.join(experience_path, "experience_db"))
        
        self.update_cost(cost=total_cost)
        utils.print_with_color("The experience has been saved.", "magenta")


    def set_new_round(self) -> None:
        """
        Start a new round.
        """

        self.HostAgent.add_request_memory(self.request)
        self._round += 1
        utils.print_with_color("""Please enter your new request. Enter 'N' for exit.""", "cyan")
        
        self.request = input()

        if self.request.upper() == "N":
            self._status = "ALLFINISH"
            return
        else:
            self._status = "APP_SELECTION"
            return
        

    def get_round(self) -> int:
        """
        Get the round of the session.
        return: The round of the session.
        """
        return self._round
    
    
    def set_round(self, new_round: int) -> None:
        """
        Set the round of the session.
        """
        self.round = new_round



    def get_status(self) -> str:
        """
        Get the status of the session.
        return: The status of the session.
        """
        return self._status
    
    
    def get_step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self._step
    

    def get_cost(self) -> float:
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self._cost
    

    def get_results(self) -> str:
        """
        Get the results of the session.
        return: The results of the session.
        """

        action_history = self.HostAgent.get_global_action_memory().content

        if len(action_history) > 0:
            result = action_history[-1].to_dict().get("Results")
        else:
            result = ""
        return result
    
    
    def get_cost(self):
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self._cost
    
    def get_application_window(self) -> object:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.app_window
    

    def set_result_and_log(self, response_json: dict) -> dict:
        """
        Set the result of the session, and log the result.
        result: The result of the session.
        response_json: The response json.
        return: The response json.
        """

        self.logger.info(json.dumps(response_json))

        return response_json
    
    
    def safe_guard(self, action: str, control_text: str) -> bool:
        """
        Safe guard for the session.
        action: The action to be taken.
        control_text: The text of the control item.
        return: The boolean value indicating whether to proceed or not.
        """
        if "PENDING" in self._status.upper() and configs["SAFE_GUARD"]:
            utils.print_with_color("[Input Required:] UFO🛸 will apply {action} on the [{control_text}] item. Please confirm whether to proceed or not. Please input Y or N.".format(action=action, control_text=control_text), "magenta")
            decision = utils.yes_or_no()
            if not decision:
                utils.print_with_color("The user decide to stop the task.", "magenta")
                self._status = "FINISH"
                return False
            
            # Handle the PENDING_AND_FINISH case
            elif "FINISH" in self.plan:
                self._status = "FINISH"
        return True
    

    def error_logger(self, response_str: str, error: str) -> None:
        """
        Error handler for the session.
        """
        log = json.dumps({"step": self._step, "status": "ERROR", "response": response_str, "error": error})
        self.logger.info(log)


    def update_cost(self, cost):
        """
        Update the cost of the session.
        """
        if isinstance(cost, float) and isinstance(self._cost, float):
            self._cost += cost
        else:
            self._cost = None


    @staticmethod
    def initialize_logger(log_path: str, log_filename: str) -> logging.Logger:
        """
        Initialize logging.
        log_path: The path of the log file.
        log_filename: The name of the log file.
        return: The logger.
        """
        # Code for initializing logging
        logger = logging.Logger(log_filename)

        if not configs["PRINT_LOG"]:
            # Remove existing handlers if PRINT_LOG is False
            logger.handlers = []


        log_file_path = os.path.join(log_path, log_filename)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(configs["LOG_LEVEL"])

        return logger