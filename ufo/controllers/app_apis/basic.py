# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from abc import abstractmethod
from typing import Dict, List
from ..basic import ReceiverBasic, CommandBasic, ReceiverFactory
from .word.wordclient import WordWinCOMReceiver

import win32com.client


class WinCOMReceiverBasic(ReceiverBasic):
    """
    The base class for Windows COM client.
    """


    def __init__(self, app_root_name: str, process_name: str) -> None:
        """
        Initialize the Windows COM client.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        """
        super().__init__()

        self.app_root_name = app_root_name
        self.process_name = process_name

        
        
        self.client = win32com.client.Dispatch(self.clsid)
        self.com_object = self.get_object_from_process_name()


    @abstractmethod
    def get_default_command_registry(self):
        """
        The default command registry.
        """
        pass


    @abstractmethod
    def get_object_from_process_name(self) -> None:
        """
        Get the object from the process name.
        :param process_name: The process name.
        """
        pass


    @abstractmethod
    def get_default_command_registry(self) -> Dict:
        """
        Get the method registry of the COM object.
        """
        pass
    
    

    def get_suffix_mapping(self) -> Dict[str, str]:
        """
        Get the suffix mapping.
        :return: The suffix mapping.
        """
        suffix_mapping =  {
            "WINWORD.EXE": "docx",
            "EXCEL.EXE": "xlsx",
            "POWERPNT.EXE": "pptx",
            "olk.exe": "msg"
        }
        
        return suffix_mapping.get(self.app_root_name, None)
    


    def app_match(self, object_name_list: List[str]) -> str:
        """
        Check if the process name matches the app root.
        :param object_name_list: The list of object name.
        :return: The matched object name.
        """

        suffix = self.get_suffix_mapping()

        if self.process_name.endswith(suffix):
            clean_process_name = self.process_name[:-len(suffix)]
        else:
            clean_process_name = self.process_name

        return max(object_name_list, key=lambda x: self.longest_common_substring_length(clean_process_name, x))
    


    @staticmethod
    def longest_common_substring_length(str1, str2) -> int:
        """
        Get the longest common substring of two strings.
        :param str1: The first string.
        :param str2: The second string.
        :return: The length of the longest common substring.
        """

        m = len(str1)
        n = len(str2)
        
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        max_length = 0
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i - 1] == str2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    if dp[i][j] > max_length:
                        max_length = dp[i][j]
                else:
                    dp[i][j] = 0
        
        return max_length
    


class WinCOMCommand(CommandBasic):
    """
    The abstract command interface.
    """

    def __init__(self, receiver: WinCOMReceiverBasic, params=None) -> None:
        """
        Initialize the command.
        :param receiver: The receiver of the command.
        """
        self.receiver = receiver
        self.params = params if params is not None else {}

    @abstractmethod  
    def execute(self):  
        pass



class COMReceiverFactory(ReceiverFactory):  
    def create_receiver(self, app_root_name: str, process_name: str) -> WinCOMReceiverBasic:
        """
        Create the wincom receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :return: The receiver.
        """
        win_com_client_mapping = {  
            "WINWORD.EXE": WordWinCOMReceiver  
        }

        com_receiver = win_com_client_mapping.get(app_root_name, None)
        if com_receiver is None:
            raise ValueError(f"Receiver for app root {app_root_name} is not found.")
        

        clsid = self.app_root_mappping(app_root_name)

        if clsid is None:
            raise ValueError(f"App root name {app_root_name} is not supported.")
        
        return com_receiver(app_root_name, process_name)
    

    def app_root_mappping(self, app_root_name:str) -> str:
        """
        Map the app root to the corresponding app.
        :return: The CLSID of the COM object.
        """
        
        win_com_map = {
            "WINWORD.EXE": "Word.Application",
            "EXCEL.EXE": "Excel.Application",
            "POWERPNT.EXE": "PowerPoint.Application",
            "olk.exe": "Outlook.Application"
        }

        return win_com_map.get(app_root_name, None)
    


    


        