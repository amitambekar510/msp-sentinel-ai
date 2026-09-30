from msp_sentinel.models import Signal
def test_signal_defaults():
 s=Signal(source="test",kind="ioc",title="Example");assert s.severity=="info";assert s.observed_at is not None
