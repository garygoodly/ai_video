from finance_video_factory.models import Article
from finance_video_factory.services.ranking import EventRanker
def test_ranker_returns_event():
    items=[Article(title="Federal Reserve cuts interest rates",url="https://example.com/1",source="Example") ]
    result=EventRanker().rank(items,1)
    assert result and result[0].score>0
