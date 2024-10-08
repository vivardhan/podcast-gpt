# System Imports
import abc
from typing import List, Tuple


class LLMQAGenerator(metaclass=abc.ABCMeta):
    """
    This is an abstract class which specifies an interface for
    using LLMs to convert podcast transcripts into question answer pairs.
    """

    def __init__(self, model_name: str):
        self.pipeline = self.load_llm(model_name)
        # Perform any additional setup in your derived class,
        # eg. inference settings can be initialized here

    @abc.abstractmethod
    def load_llm(self, model_name: str) -> any:
        """
        Loads the LLM and returns it

        TODO(vivardhan.kanoria) the return type should be updated
        to the transformers library model class

        params:
                model_name: The string identifier for the model

        returns:
                The initialized model
        """
        pass

    @abc.abstractmethod
    def create_qa_prompt(
        self, episode_title: str, chapter_title: str, chapter_transcript: str
    ) -> str:
        """
        Given an episode title, chapter title and chapter transcript, creates a prompt to run inference with.

        params:
                episode_title: The title of the episode
                chapter_title: The title of the current chapter from the episode
                transcript: The transcript of current chapter

        returns:
                The prompt text
        """
        pass

    @abc.abstractmethod
    def run_model_inference(self, prompt: str) -> str:
        """
        Runs inference on self.model using the provided prompt.

        params:
                prompt: The prompt text

        returns:
                The model output text
        """
        pass

    @abc.abstractmethod
    def parse_model_output(self, model_output: str) -> List[Tuple[str, str]]:
        """
        Parse the model output into a list of question answer pairs

        params:
                model_output: inference result

        returns
                a List of question answer tuples, i.e.:
                [
                        (question_1, answer_1),
                        ...
                        (question_n), answer_n),
                ]
        """
        pass

    def generate_question_answer_pairs(
        self,
        podcast_host: str,
        episode_title: str,
        chapter_title: str,
        chapter_transcript: str,
    ) -> List[Tuple[str, str]]:
        """
        Generates QA pairs using self.model for a chapter within a podcast episode

        You do not need to re-implement this function for a child class

        podcast_host:
                        The name of the podcast host
                episode_title:
                        The title of the episode
                chapter_title:
                        The title of the current chapter from the episode
                transcript: The transcript of current chapter

        returns:
                a List of question answer tuples, i.e.:
                [
                        (question_1, answer_1),
                        ...
                        (question_n), answer_n),
                ]
        """
        prompt = self.create_qa_prompt(
            podcast_host, episode_title, chapter_title, chapter_transcript
        )
        output = self.run_model_inference(prompt)
        return self.parse_model_output(output)
