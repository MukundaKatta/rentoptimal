"""Tests for Rentoptimal."""
from src.core import Rentoptimal
def test_init(): assert Rentoptimal().get_stats()["ops"] == 0
def test_op(): c = Rentoptimal(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Rentoptimal(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Rentoptimal(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Rentoptimal(); r = c.process(); assert r["service"] == "rentoptimal"
