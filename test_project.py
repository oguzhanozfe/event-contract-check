import unittest
from project import analyze


PLAN = {"buy": {"cost": {"type": "number"}, "coupon": {"type": "string", "required": False}}}


def sample(props):
    return analyze({"plan": PLAN, "events": [{"name": "buy", "properties": props}]})


class TrackingTests(unittest.TestCase):
    def test_optional_absence_and_integer_as_number(self):
        self.assertEqual(sample({"cost": 1})["rows"], [])

    def test_boolean_as_number_and_null_present_are_mistypes(self):
        rows = sample({"cost": False, "coupon": None})["rows"]
        self.assertEqual([r["Observed"] for r in rows], ["boolean", "null"])
        self.assertEqual(sample({"cost": False, "coupon": None})["metrics"]["Failing samples"], 1)

    def test_required_absence_and_coverage(self):
        self.assertEqual(sample({})["rows"][0]["Finding"], "Missing property")
        result = analyze({"plan": PLAN, "events": [{"name": "other", "properties": {}}]})
        self.assertEqual(result["metrics"]["Unobserved event names"], 1)
        self.assertEqual(result["rows"][0]["Finding"], "Unplanned event")

    def test_rejects_invalid_plan_even_when_sample_empty(self):
        with self.assertRaises(ValueError):
            analyze({"plan": {"a": {"p": {"type": "numbre"}}}, "events": []})
