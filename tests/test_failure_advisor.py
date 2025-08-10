import os
import json
import unittest
from unittest.mock import MagicMock

from src.failure_advisor import FailureAdvisor


class DummyModel:
    def __init__(self, text: str):
        self._text = text

    def generate_content(self, prompt: str):
        # Return an object with .text and .parts similar to Gemini SDK responses
        return type("Resp", (), {"text": self._text, "parts": [self._text]})()


class DummyNLPClient:
    def __init__(self, text: str):
        self._model = DummyModel(text)

    @property
    def flash_model(self):
        return self._model

    @property
    def pro_model(self):
        return self._model


class TestFailureAdvisor(unittest.TestCase):
    def setUp(self):
        # Enable advisor for tests
        os.environ["ERROR_ADVISOR_ENABLED"] = "true"

    def tearDown(self):
        if "ERROR_ADVISOR_ENABLED" in os.environ:
            del os.environ["ERROR_ADVISOR_ENABLED"]

    def test_prompt_contains_context_and_rules(self):
        advisor = FailureAdvisor(nlp_client=DummyNLPClient('{"message":"x","actions":["Retry","Help"]}'))
        ctx = {"error_code": "E_OKX_HTTP", "intent": "get_price", "entities": {"symbol": "ETH"}}
        prompt = advisor._build_prompt(ctx)
        self.assertIn("FailureAdvisor", prompt)
        self.assertIn("Context:", prompt)
        self.assertIn("error_code", prompt)
        self.assertIn("Suggest 2-3", prompt)

    def test_parses_valid_response(self):
        text = json.dumps({"message": "Service is busy; please try again soon.", "actions": ["retry", "help", "wait"]})
        advisor = FailureAdvisor(nlp_client=DummyNLPClient(text))
        res = advisor.summarize({"error_code": "E_OKX_HTTP"})
        self.assertIsInstance(res, dict)
        self.assertEqual(res["message"], "Service is busy; please try again soon.")
        self.assertIn("Retry", res["actions"])  # Title-cased

    def test_returns_none_on_malformed_response(self):
        advisor = FailureAdvisor(nlp_client=DummyNLPClient("not json"))
        res = advisor.summarize({"error_code": "E_UNKNOWN"})
        self.assertIsNone(res)

    def test_returns_none_when_disabled(self):
        os.environ["ERROR_ADVISOR_ENABLED"] = "false"
        advisor = FailureAdvisor(nlp_client=DummyNLPClient('{"message":"x","actions":["Retry","Help"]}'))
        res = advisor.summarize({"error_code": "E_OKX_HTTP"})
        self.assertIsNone(res)

    def test_returns_none_when_nlp_raises(self):
        class BadNLP:
            @property
            def flash_model(self):
                raise RuntimeError("boom")
        advisor = FailureAdvisor(nlp_client=BadNLP())
        res = advisor.summarize({"error_code": "E_OKX_HTTP"})
        self.assertIsNone(res) 